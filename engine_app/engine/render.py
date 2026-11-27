"""Frame rendering + assembly: specs + durations -> MP4 (with voiceover and captions.srt)."""
import hashlib, json, os, subprocess, sys
from multiprocessing import Pool
from PIL import ImageFont
from . import gfx
from .scene import compose

W, H = 1280, 720
VB = "0 0 680 383"
BUNDLED_FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "DejaVuSans-Bold.ttf")
FONT_PATHS = [BUNDLED_FONT, "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
              "/Library/Fonts/Arial Bold.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"]
BG = ('<defs><radialGradient id="g" cx="50%" cy="45%" r="75%"><stop offset="0" stop-color="#1b1b21"/><stop offset="1" stop-color="#050507"/></radialGradient>'
      '<pattern id="p" width="16" height="16" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="0.8" fill="#ffffff" fill-opacity=".12"/></pattern></defs>'
      '<rect width="680" height="383" fill="url(#g)"/><rect width="680" height="383" fill="url(#p)"/>')


def _font(size=27):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return None


def headline_svg(h, size=27):
    f = _font(size)
    parts = h.split("*")
    x0 = 340 - (f.getlength(h.replace("*", "")) if f else 0.66 * size * len(h.replace("*", ""))) / 2
    out = ""
    for i, p in enumerate(parts):
        if not p.strip():
            continue
        before = "".join(parts[:i]) + (p[: len(p) - len(p.lstrip())])
        x = x0 + (f.getlength(before) if f else 0.66 * size * len(before))
        out += gfx.txt(x, 44, p.strip(), size, "#ff6a00" if i % 2 else "#ffffff", "start")
    return out


def _svg(inner):
    return f'<svg width="{W}" height="{H}" viewBox="{VB}" xmlns="http://www.w3.org/2000/svg">{inner}</svg>'


_BACKEND = None


def _pick_backend():
    """cairosvg is fastest but needs the native Cairo library (a pain on Windows).
    Fall back to resvg (pure pip wheel, no system libraries). Force one with EXPLAINER_RENDERER=cairo|resvg."""
    global _BACKEND
    want = os.environ.get("EXPLAINER_RENDERER", "").lower()
    if want != "resvg":
        try:
            import cairosvg
            cairosvg.svg2png(bytestring=b'<svg xmlns="http://www.w3.org/2000/svg" width="2" height="2"/>')
            _BACKEND = "cairo"
            return
        except Exception:
            if want == "cairo":
                raise
    try:
        import resvg_py  # noqa: F401
    except ImportError:
        raise SystemExit("No SVG renderer found. Run:  pip install resvg-py")
    _BACKEND = "resvg"
    print("SVG renderer: resvg", flush=True)


def png_size(svg, w, h):
    if _BACKEND is None:
        _pick_backend()
    if _BACKEND == "cairo":
        import cairosvg
        return cairosvg.svg2png(bytestring=svg.encode(), output_width=w, output_height=h)
    import resvg_py
    return bytes(resvg_py.svg_to_bytes(svg_string=svg, width=w, height=h, skip_system_fonts=True, font_files=[BUNDLED_FONT]))


def png(svg):
    return png_size(svg, W, H)


def frame(spec, t, D, seed):
    gfx.seed(seed)
    body = compose(spec, t, D)
    e = min(1, t / 0.3)
    off = 22 * (1 - gfx.ez(t / 0.35))
    return png(_svg(f'<g opacity="{e:.3f}" transform="translate(61,{72 + off:.2f}) scale(0.82)">{body}</g>'))


def spec_hash(spec, D, fps):
    return hashlib.sha1(json.dumps([spec, round(D, 2), fps], sort_keys=True).encode()).hexdigest()[:10]


def render_beat(job):
    idx, spec, D, outdir, fps = job
    out = os.path.join(outdir, "clips", f"clip_{idx:03d}_{spec_hash(spec, D, fps)}.mp4")
    if os.path.exists(out):
        return idx, out
    hl = os.path.join(outdir, "clips", f"h_{idx:03d}.png")
    with open(hl, "wb") as f:
        f.write(png(_svg(headline_svg(spec["headline"]))))
    bg = os.path.join(outdir, "clips", "bg.png")
    fc = ("[1:v]format=rgba[s];[2:v]format=rgba,fade=t=in:st=0.05:d=0.25:alpha=1[h];[0:v][s]overlay=shortest=1[a];"
          "[a][h]overlay=x=0:y='-18*max(0,1-t/0.3)':eval=frame:shortest=1,fps=30,tpad=stop_mode=clone:stop_duration=0.5[o]")
    tmp = out + ".tmp.mp4"
    cmd = ["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(fps), "-t", f"{D:.3f}", "-i", bg,
           "-f", "image2pipe", "-c:v", "png", "-framerate", str(fps), "-i", "-",
           "-loop", "1", "-framerate", str(fps), "-t", f"{D:.3f}", "-i", hl,
           "-filter_complex", fc, "-map", "[o]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
           "-crf", "20", "-r", "30", "-t", f"{D:.3f}", "-f", "mp4", tmp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fi in range(int(D * fps)):
        p.stdin.write(frame(spec, fi / fps, D, 5 + idx))
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError(f"ffmpeg failed on beat {idx}")
    os.replace(tmp, out)
    return idx, out


def srt_time(s):
    ms = int(round(s * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def build(beats, specs, durations, audio_paths, outdir, out_name="video.mp4", fps=24, workers=None):
    os.makedirs(os.path.join(outdir, "clips"), exist_ok=True)
    with open(os.path.join(outdir, "clips", "bg.png"), "wb") as f:
        f.write(png(_svg(BG)))
    jobs = [(i + 1, specs[i], durations[i], outdir, fps) for i in range(len(beats))]
    workers = workers or max(1, min(os.cpu_count() or 1, 4))
    print(f"Rendering {len(jobs)} scenes ({sum(durations):.0f}s) with {workers} worker(s)...")
    done = {}
    if workers == 1:
        for j in jobs:
            i, p = render_beat(j)
            done[i] = p
            print(f"  scene {i}/{len(jobs)}", flush=True)
    else:
        with Pool(workers) as pool:
            for i, p in pool.imap_unordered(render_beat, jobs):
                done[i] = p
                print(f"  scene {i}/{len(jobs)}", flush=True)
    lst = os.path.join(outdir, "clips", "list.txt")
    with open(lst, "w") as f:
        for i in range(1, len(jobs) + 1):
            f.write("file '" + os.path.abspath(done[i]).replace("\\", "/") + "'\n")
    vid = os.path.join(outdir, "video_silent.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid], check=True)
    # captions
    t = 0.0
    with open(os.path.join(outdir, "captions.srt"), "w") as f:
        for i, b in enumerate(beats):
            f.write(f"{i + 1}\n{srt_time(t)} --> {srt_time(t + durations[i] - 0.1)}\n{b['text']}\n\n")
            t += durations[i]
    final = os.path.join(outdir, out_name)
    if not audio_paths:
        os.replace(vid, final)
        return final
    parts = []
    for i, ap in enumerate(audio_paths):
        pw = os.path.join(outdir, "clips", f"a_{i + 1:03d}.wav")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", ap, "-af", "apad", "-t", f"{durations[i]:.3f}", "-ar", "44100", "-ac", "2", pw], check=True)
        parts.append(pw)
    al = os.path.join(outdir, "clips", "alist.txt")
    with open(al, "w") as f:
        for pw in parts:
            f.write("file '" + os.path.abspath(pw).replace("\\", "/") + "'\n")
    wav = os.path.join(outdir, "voiceover.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", al, "-c", "copy", wav], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", final], check=True)
    return final
