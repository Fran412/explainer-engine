#!/usr/bin/env python3
"""Explainer Engine CLI.

  python run.py script.txt --tts elevenlabs --voice VOICE_ID
  python run.py script.txt --tts fish --voice REFERENCE_ID
  python run.py script.txt --tts mock --planner heuristic --limit 8     # no API keys needed
  python run.py --catalog                                               # render a sheet of every prop
Edit out/specs.json by hand, then re-run with --specs out/specs.json to re-render only changed scenes.
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def load_env(path=".env"):
    if os.path.exists(path):
        for l in open(path):
            l = l.strip()
            if l and not l.startswith("#") and "=" in l:
                k, v = l.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def catalog(out):
    from engine import gfx
    from engine.props import PROPS
    from engine.render import png, _svg, BG
    os.makedirs(out, exist_ok=True)
    names = list(PROPS)
    cols = 7
    body = ""
    gfx.seed(3)
    for i, n in enumerate(names):
        cx = 50 + (i % cols) * 96
        cy = 60 + (i // cols) * 120
        body += PROPS[n](cx, cy, 0.62, n, 0.4)
    # taller canvas
    rows = (len(names) + cols - 1) // cols
    svg = (f'<svg width="1400" height="{rows * 240}" viewBox="0 0 680 {rows * 120}" xmlns="http://www.w3.org/2000/svg">'
           f'<rect width="680" height="{rows * 120}" fill="#0b0b0d"/>{body}</svg>')
    p = os.path.join(out, "prop_catalog.png")
    from engine.render import png_size
    open(p, "wb").write(png_size(svg, 1400, rows * 240))
    print("wrote", p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script", nargs="?")
    ap.add_argument("--out", default="out")
    ap.add_argument("--planner", choices=["llm", "heuristic"], default=None, help="default: llm if ANTHROPIC_API_KEY is set")
    ap.add_argument("--specs", help="use an existing specs.json (skips planning)")
    ap.add_argument("--tts", default="mock", help="elevenlabs | fish | mock | none")
    ap.add_argument("--voice", help="ElevenLabs voice_id or Fish reference_id")
    ap.add_argument("--tts-model")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--limit", type=int, help="only the first N beats (for testing)")
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--workers", type=int)
    ap.add_argument("--cache-dir", help="folder for cached voice clips (default: <out>/audio_cache)")
    ap.add_argument("--catalog", action="store_true")
    a = ap.parse_args()
    load_env()
    if a.catalog:
        return catalog(a.out)
    if not a.script:
        ap.error("script path required")
    from engine import script as S, planner as P, tts as T, render as Rn
    os.makedirs(a.out, exist_ok=True)
    beats = S.parse(open(a.script, encoding="utf-8").read())
    if a.limit:
        beats = beats[:a.limit]
    print(f"{len(beats)} beats")
    json.dump(beats, open(os.path.join(a.out, "beats.json"), "w"), indent=1)
    # 1) plan
    if a.specs:
        specs = [P.validate(s, b["text"]) for s, b in zip(json.load(open(a.specs)), beats)]
        if len(specs) < len(beats):
            raise SystemExit(f"{a.specs} has {len(specs)} specs for {len(beats)} beats")
    else:
        mode = a.planner or ("llm" if os.environ.get("ANTHROPIC_API_KEY") else "heuristic")
        print(f"Planning scenes ({mode})...")
        specs = (P.LLMPlanner() if mode == "llm" else P.HeuristicPlanner()).plan(beats)
        if mode == "heuristic":
            specs = [P.validate(s, b["text"]) for s, b in zip(specs, beats)]
    json.dump(specs, open(os.path.join(a.out, "specs.json"), "w"), indent=1)
    # 2) voice
    audio, durs = None, []
    if a.tts.lower() != "none":
        eng = T.make(a.tts, a.cache_dir or os.path.join(a.out, "audio_cache"), a.voice, a.tts_model, a.speed)
        audio = []
        for i, b in enumerate(beats):
            prev = beats[i - 1]["text"] if i else ""
            nxt = beats[i + 1]["text"] if i + 1 < len(beats) else ""
            print(f"  voice {i + 1}/{len(beats)}", flush=True)
            audio.append(eng.synth(b["text"], prev, nxt))
        durs = [max(2.5, T.probe_duration(p) + 0.45) for p in audio]
    else:
        for i, b in enumerate(beats):
            if "start" in b and i + 1 < len(beats) and "start" in beats[i + 1]:
                durs.append(max(2.0, beats[i + 1]["start"] - b["start"]))
            else:
                durs.append(max(2.5, len(b["text"].split()) / 2.7 + 0.5))
    # 3) render + assemble
    final = Rn.build(beats, specs, durs, audio, a.out, fps=a.fps, workers=a.workers)
    print("\nDONE:", final, f"({sum(durs):.0f}s)")
    print("captions:", os.path.join(a.out, "captions.srt"))


if __name__ == "__main__":
    main()
