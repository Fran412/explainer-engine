# Explainer Engine

Script in, animated dark-mode explainer video out (with voiceover and captions).

    script.txt --> beats --> scene specs (LLM) --> voiceover (ElevenLabs / Fish) --> animated frames --> video.mp4 + captions.srt

Visual system: black background, glowing white line art, one orange accent, a recurring orange
hooded hero, big headline with one highlighted word, props that animate (coins flow, rocket lifts,
bars grow, clocks tick). Scene length follows the voiceover audio, so picture and narration stay in sync.

## Setup

    # Windows (PowerShell):  winget install Gyan.FFmpeg     (then close and reopen PowerShell)
    # macOS:                 brew install ffmpeg
    # Linux:                 sudo apt install ffmpeg
    pip install -r requirements.txt
    copy .env.example .env                    # Windows  (macOS/Linux: cp)  - then fill in keys

No Cairo / GTK install is needed: the engine uses cairosvg if it works and otherwise falls back to
resvg (a plain pip package) automatically. A font is bundled, so nothing else to install.
Force one with the environment variable EXPLAINER_RENDERER=cairo or resvg.

## No terminal? Use the desktop app

Double-click `Install.bat` once, then `Start.bat`. See `START_HERE.txt`.

## Run (command line)

    # no keys needed (silent placeholder audio, offline planner) - good for a first test
    python run.py examples/sample_script.txt --tts mock --planner heuristic --limit 6

    # real run: Claude designs the scenes, ElevenLabs narrates
    python run.py my_script.txt --tts elevenlabs --voice YOUR_VOICE_ID

    # same, with Fish Audio
    python run.py my_script.txt --tts fish --voice YOUR_REFERENCE_ID

    # video only (uses (m:ss) timestamps in the script if present)
    python run.py my_script.txt --tts none

Outputs land in `out/`: `video.mp4`, `captions.srt`, `voiceover.wav`, `specs.json`, `beats.json`.

## Script format

Plain prose, or timestamped lines like `(0:12) Text...`. Headings and `---` lines are skipped.
With a voice provider, scene durations come from the generated audio (timestamps are ignored).
With `--tts none`, timestamps set the durations.

## Planner (the scene designer)

`engine/planner.py` sends your beats to Claude with the prop catalog and a strict JSON schema
(headline, layout, objects, hero pose, link, chart, callout). Every spec is validated, so a bad
answer can never crash the renderer; failed chunks fall back to the offline heuristic planner.
Without `ANTHROPIC_API_KEY` the heuristic planner is used (works, but scenes are plainer).

Control it by hand: edit `out/specs.json`, then

    python run.py my_script.txt --specs out/specs.json --tts elevenlabs --voice ID

Only scenes whose spec or duration changed are re-rendered, and cached voice clips are reused,
so tweaking costs no extra TTS credits.

## Voice providers (engine/tts.py)

- ElevenLabs: `POST /v1/text-to-speech/{voice_id}`, `xi-api-key` header. Sends previous/next text for continuity.
- Fish Audio: `POST https://api.fish.audio/v1/tts`, Bearer key, `model` header (default `s2.1-pro`; the old `s1` is being retired).
- Audio is cached under `out/audio_cache/` by hash of provider, voice, model and text.
- Add another provider by subclassing `Base` and implementing `_request()`.

## Extending the look

- `python run.py --catalog` renders `out/prop_catalog.png`, a sheet of all 38 props.
- Add a prop: write `f(cx, cy, s, label, t)` in `engine/props.py`, register it in `PROPS` and `PROP_DOC`.
  The planner learns about it automatically from `PROP_DOC`.
- Layouts and charts live in `engine/scene.py`.
- Keep drawing calls unconditional (use opacity to hide things) so the hand-drawn wobble stays stable between frames.

## Known limits

- Scenes are composed from the prop library, so variety is bounded by it. Grow the library over time.
- Rendering is CPU-bound (about real time per core); use `--workers N`.
- The resvg renderer is slower than cairosvg (about 0.2 s per frame); use `--workers 4` or more.
