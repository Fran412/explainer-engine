"""Render worker: runs the Explainer Engine for jobs submitted by the Vercel app.

Env vars:
  WORKER_TOKEN        required. Shared secret; the Vercel API sends it in the x-token header.
  FISH_API_KEY / ELEVENLABS_API_KEY / ANTHROPIC_API_KEY   keys live HERE, never in the browser.
  FISH_MODEL          default s2.1-pro-free
  DATA_DIR            where jobs are stored (default /data, falls back to /tmp/explainer_jobs)
  ENGINE_DIR          folder containing run.py (default ./engine_app)
  MAX_SCRIPT_CHARS    default 30000
"""
import hmac, hashlib, json, os, re, shutil, subprocess, sys, threading, time, uuid
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

ROOT = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.environ.get("ENGINE_DIR", os.path.join(ROOT, "engine_app"))
DATA = os.environ.get("DATA_DIR", "/data")
try:
    os.makedirs(DATA, exist_ok=True)
except OSError:
    DATA = "/tmp/explainer_jobs"
    os.makedirs(DATA, exist_ok=True)
MAX_CHARS = int(os.environ.get("MAX_SCRIPT_CHARS", "30000"))
FILES = {"video.mp4", "captions.srt", "voiceover.wav", "specs.json"}
JOBS = {}
RUN_LOCK = threading.Semaphore(1)   # one render at a time (CPU bound)
app = FastAPI(title="Explainer worker")


def token():
    t = os.environ.get("WORKER_TOKEN", "")
    if not t:
        raise HTTPException(500, "WORKER_TOKEN is not set on the worker")
    return t


def auth(x_token):
    if not x_token or not hmac.compare_digest(x_token, token()):
        raise HTTPException(401, "bad token")


def sign(job_id, name, exp):
    return hmac.new(token().encode(), f"{job_id}|{name}|{exp}".encode(), hashlib.sha256).hexdigest()[:32]


class JobIn(BaseModel):
    script: str
    provider: str = "fish"          # fish | elevenlabs | mock | none
    voice: str = ""
    model: str = ""
    planner: str = "heuristic"      # llm | heuristic | specs
    specs: Optional[list] = None    # required when planner == "specs"
    limit: Optional[int] = None     # test run: first N scenes
    workers: Optional[int] = None


def cleanup(max_age=24 * 3600):
    now = time.time()
    for d in os.listdir(DATA):
        p = os.path.join(DATA, d)
        if os.path.isdir(p) and now - os.path.getmtime(p) > max_age:
            shutil.rmtree(p, ignore_errors=True)
            JOBS.pop(d, None)


def run_job(job_id, cmd, env):
    job = JOBS[job_id]
    out = os.path.join(DATA, job_id)
    with RUN_LOCK:
        job.update(status="running", stage="Starting...")
        scene_done = 0
        try:
            p = subprocess.Popen(cmd, cwd=ENGINE, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, encoding="utf-8", errors="replace")
            for line in p.stdout:
                line = line.rstrip()
                job["log"] = (job["log"] + [line])[-60:]
                if line.startswith("Planning"):
                    job["stage"] = "Designing scenes..."
                m = re.search(r"voice (\d+)/(\d+)", line)
                if m:
                    job["progress"] = round(30 * int(m.group(1)) / int(m.group(2)))
                    job["stage"] = f"Voice {m.group(1)}/{m.group(2)}"
                m = re.search(r"scene (\d+)/(\d+)", line)
                if m:
                    scene_done += 1
                    job["progress"] = round(30 + 68 * scene_done / int(m.group(2)))
                    job["stage"] = f"Rendering {scene_done}/{m.group(2)}"
            p.wait()
            if p.returncode == 0 and os.path.exists(os.path.join(out, "video.mp4")):
                job.update(status="done", progress=100, stage="Done")
            else:
                job.update(status="failed", stage="Failed", error="\n".join(job["log"][-8:]))
        except Exception as e:  # noqa
            job.update(status="failed", stage="Failed", error=str(e))
        os.utime(out, None)


@app.get("/health")
def health():
    return {"ok": True, "ffmpeg": bool(shutil.which("ffmpeg")), "engine": os.path.exists(os.path.join(ENGINE, "run.py"))}


@app.post("/jobs")
def create(j: JobIn, x_token: str = Header(None)):
    auth(x_token)
    script = j.script.strip()
    if len(script.split()) < 8:
        raise HTTPException(400, "Script is too short")
    if len(script) > MAX_CHARS:
        raise HTTPException(400, f"Script is too long (max {MAX_CHARS} characters)")
    if j.provider not in ("fish", "elevenlabs", "mock", "none"):
        raise HTTPException(400, "Unknown voice provider")
    if j.planner not in ("llm", "heuristic", "specs"):
        raise HTTPException(400, "Unknown planner")
    if j.provider == "fish" and not os.environ.get("FISH_API_KEY"):
        raise HTTPException(400, "FISH_API_KEY is not set on the worker")
    if j.provider == "elevenlabs" and not os.environ.get("ELEVENLABS_API_KEY"):
        raise HTTPException(400, "ELEVENLABS_API_KEY is not set on the worker")
    if j.planner == "llm" and not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(400, "ANTHROPIC_API_KEY is not set on the worker")
    if j.planner == "specs" and not j.specs:
        raise HTTPException(400, "Paste your specs JSON")
    if any(JOBS[k]["status"] in ("queued", "running") for k in JOBS) and sum(1 for k in JOBS if JOBS[k]["status"] == "queued") >= 3:
        raise HTTPException(429, "Worker is busy, try again in a few minutes")
    cleanup()
    job_id = uuid.uuid4().hex
    out = os.path.join(DATA, job_id)
    os.makedirs(out)
    sp = os.path.join(out, "script.txt")
    open(sp, "w", encoding="utf-8").write(script)
    cmd = [sys.executable, "-u", "run.py", sp, "--out", out, "--tts", j.provider, "--workers", str(max(1, min(j.workers or 2, 8)))]
    if j.provider in ("fish", "elevenlabs"):
        if j.voice.strip():
            cmd += ["--voice", j.voice.strip()[:80]]
        model = j.model.strip() or (os.environ.get("FISH_MODEL", "s2.1-pro-free") if j.provider == "fish" else "")
        if model:
            cmd += ["--tts-model", model[:60]]
    if j.planner == "specs":
        specs_path = os.path.join(out, "input_specs.json")
        json.dump(j.specs, open(specs_path, "w"))
        cmd += ["--specs", specs_path]
    else:
        cmd += ["--planner", j.planner]
    if j.limit:
        cmd += ["--limit", str(max(1, min(j.limit, 200)))]
    JOBS[job_id] = {"status": "queued", "progress": 0, "stage": "Queued", "log": [], "error": None, "created": time.time()}
    threading.Thread(target=run_job, args=(job_id, cmd, os.environ.copy()), daemon=True).start()
    return {"id": job_id}


@app.get("/jobs/{job_id}")
def status(job_id: str, x_token: str = Header(None)):
    auth(x_token)
    if not re.fullmatch(r"[0-9a-f]{32}", job_id):
        raise HTTPException(400, "bad id")
    out = os.path.join(DATA, job_id)
    job = JOBS.get(job_id)
    if not job:
        if os.path.exists(os.path.join(out, "video.mp4")):
            job = {"status": "done", "progress": 100, "stage": "Done", "log": [], "error": None}
        else:
            raise HTTPException(404, "unknown job")
    res = {k: job[k] for k in ("status", "progress", "stage", "error")}
    res["log"] = job["log"][-12:]
    res["downloads"] = []
    if job["status"] == "done":
        exp = int(time.time()) + 3600
        for name in sorted(FILES):
            if os.path.exists(os.path.join(out, name)):
                res["downloads"].append({"name": name, "url": f"/download/{job_id}/{name}?exp={exp}&sig={sign(job_id, name, exp)}"})
    return res


@app.get("/download/{job_id}/{name}")
def download(job_id: str, name: str, exp: int, sig: str):
    if not re.fullmatch(r"[0-9a-f]{32}", job_id) or name not in FILES:
        raise HTTPException(404, "not found")
    if exp < time.time() or not hmac.compare_digest(sig, sign(job_id, name, exp)):
        raise HTTPException(403, "link expired or invalid")
    path = os.path.join(DATA, job_id, name)
    if not os.path.exists(path):
        raise HTTPException(404, "not found")
    return FileResponse(path, filename=name)
