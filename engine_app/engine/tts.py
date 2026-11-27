"""Voice providers. Each returns an audio file for one beat of narration.

  elevenlabs : POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}   (header xi-api-key)
  fish       : POST https://api.fish.audio/v1/tts                            (Bearer key + 'model' header)
  mock       : silent audio sized to the word count (for testing without keys)
Results are cached by hash(provider, voice, model, text), so re-runs cost nothing.
"""
import hashlib, os, subprocess, time


def probe_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


class Base:
    name = "base"
    ext = "mp3"

    def __init__(self, cache_dir):
        self.cache = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def key(self, text):
        return hashlib.sha1(f"{self.name}|{self.ident()}|{text}".encode()).hexdigest()[:16]

    def ident(self):
        return ""

    def synth(self, text, prev_text="", next_text=""):
        path = os.path.join(self.cache, f"{self.name}_{self.key(text)}.{self.ext}")
        if os.path.exists(path) and os.path.getsize(path) > 500:
            return path
        data = self._request(text, prev_text, next_text)
        with open(path, "wb") as f:
            f.write(data)
        return path

    def _post(self, fn, tries=4):
        import requests
        for i in range(tries):
            r = fn(requests)
            if r.status_code == 200:
                return r.content
            if r.status_code in (429, 500, 502, 503, 504) and i < tries - 1:
                time.sleep(2 ** (i + 1))
                continue
            raise RuntimeError(f"{self.name} TTS failed: HTTP {r.status_code}: {r.text[:300]}")


class ElevenLabs(Base):
    name = "elevenlabs"

    def __init__(self, cache_dir, api_key=None, voice_id=None, model=None, stability=0.5, similarity=0.75, speed=1.0):
        super().__init__(cache_dir)
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        self.voice_id = voice_id or os.environ.get("ELEVENLABS_VOICE_ID")
        self.model = model or os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")
        self.stability, self.similarity, self.speed = stability, similarity, speed
        if not self.api_key or not self.voice_id:
            raise SystemExit("Set ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID (or pass --voice).")

    def ident(self):
        return f"{self.voice_id}|{self.model}|{self.stability}|{self.similarity}|{self.speed}"

    def _request(self, text, prev_text, next_text):
        body = {"text": text, "model_id": self.model,
                "voice_settings": {"stability": self.stability, "similarity_boost": self.similarity, "speed": self.speed}}
        if prev_text:
            body["previous_text"] = prev_text[-400:]   # keeps tone continuous between beats
        if next_text:
            body["next_text"] = next_text[:400]
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        return self._post(lambda rq: rq.post(url, params={"output_format": "mp3_44100_128"}, json=body, timeout=120,
                                             headers={"xi-api-key": self.api_key, "Content-Type": "application/json"}))


class Fish(Base):
    name = "fish"

    def __init__(self, cache_dir, api_key=None, voice_id=None, model=None, speed=1.0):
        super().__init__(cache_dir)
        self.api_key = api_key or os.environ.get("FISH_API_KEY")
        self.voice_id = voice_id or os.environ.get("FISH_REFERENCE_ID", "")
        self.model = model or os.environ.get("FISH_MODEL", "s2.1-pro")
        self.speed = speed
        if not self.api_key:
            raise SystemExit("Set FISH_API_KEY (and FISH_REFERENCE_ID for a specific voice).")

    def ident(self):
        return f"{self.voice_id}|{self.model}|{self.speed}"

    def _request(self, text, prev_text, next_text):
        body = {"text": text, "format": "mp3", "mp3_bitrate": 128}
        if self.voice_id:
            body["reference_id"] = self.voice_id
        if self.speed != 1.0:
            body["prosody"] = {"speed": self.speed}
        return self._post(lambda rq: rq.post("https://api.fish.audio/v1/tts", json=body, timeout=180,
                                             headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json",
                                                      "model": self.model}))


class Mock(Base):
    name = "mock"
    ext = "wav"

    def _request(self, text, prev_text, next_text):
        secs = max(1.5, len(text.split()) / 2.7)
        out = os.path.join(self.cache, f"_tmp_{self.key(text)}.wav")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", f"{secs:.2f}", out], check=True)
        data = open(out, "rb").read()
        os.remove(out)
        return data


def make(provider, cache_dir, voice=None, model=None, speed=1.0):
    p = (provider or "mock").lower()
    if p in ("elevenlabs", "11labs", "eleven"):
        return ElevenLabs(cache_dir, voice_id=voice, model=model, speed=speed)
    if p in ("fish", "fish.audio", "fishaudio"):
        return Fish(cache_dir, voice_id=voice, model=model, speed=speed)
    if p == "mock":
        return Mock(cache_dir)
    raise SystemExit(f"Unknown TTS provider: {provider}")
