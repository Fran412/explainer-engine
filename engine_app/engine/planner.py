"""Scene planning: narration beats -> scene specs.

Two planners:
  * LLMPlanner       - asks Claude (Anthropic API) to design every scene from the prop catalog.
  * HeuristicPlanner - offline keyword fallback (no API key needed).
Every spec passes through validate(), so a bad LLM answer can never crash the renderer.
"""
import json, os, re
from .props import PROPS, PROP_DOC
from .scene import LAYOUTS, MOTIONS, LINKS, POSES, HERO_MOTIONS, CHARTS

SYSTEM = """You are the scene director for a dark-mode animated explainer channel.
Visual system: black background, white glowing line art, ONE orange accent, and a recurring faceless
orange hooded hero character. Each narration beat becomes one scene of 3-9 seconds.

Return ONLY a JSON array with one scene spec per beat, in order. Spec schema:
{
 "headline": "2-4 WORDS IN CAPS with ONE *KEY WORD* in asterisks",
 "layout": one of %(layouts)s,
 "objects": [{"prop": <prop name>, "label": "1-2 word caption or ''", "motion": one of %(motions)s}],
 "hero": null OR {"pose": one of %(poses)s, "motion": "bob" or "jump"},
 "link": one of %(links)s,
 "chart": null OR {"kind": one of %(charts)s, "value": number (pie only), "ratio": number (compare only)},
 "callout": null OR "a number or short stat from the beat, e.g. $115.8B"
}
Layout object counts: center=1, split=2, row3=3, row4=4, flow=3 (a loop), hero_scene=2 (hero on the left),
versus=2 (two sides), chart=1 (optional extra object; uses "chart"), hero_center=3 (hero in the middle).
Props (use ONLY these names):
%(props)s

Rules:
- The scene must visually explain what the narrator says in that beat. Pick props by meaning, not at random.
- Never use the same layout + prop set as the previous scene. Vary layouts across the whole video.
- Use chart layouts only when the beat talks about numbers, growth, decline, or percentages.
- Use the hero when the beat is about "you", a person's feeling, or a decision (about 1 in 3 scenes).
- Use link "coins" when money flows between objects, "arrow" for cause/effect, "loop" with flow layout for cycles.
- Put real numbers from the beat into "callout" or the chart value. Never invent numbers.
- Headline wording must come from the beat. No emojis. No punctuation except ? and $ and %%."""


def _prompt_system():
    return SYSTEM % {
        "layouts": list(LAYOUTS), "motions": MOTIONS, "poses": POSES, "links": LINKS, "charts": CHARTS,
        "props": "\n".join(f"- {k}: {v}" for k, v in PROP_DOC.items()),
    }


def _headline_fix(h, text):
    h = re.sub(r"[^A-Za-z0-9\s\*\?\$%'\.,/-]", "", str(h or "")).upper().strip()
    if not h:
        h = " ".join(re.findall(r"[A-Za-z0-9$%']+", text)[:4]).upper()
    if "*" not in h:
        w = h.split()
        if w:
            i = max(range(len(w)), key=lambda k: len(w[k]))
            w[i] = f"*{w[i]}*"
            h = " ".join(w)
    if h.count("*") % 2:
        h = h.replace("*", "")
        w = h.split()
        w[-1] = f"*{w[-1]}*"
        h = " ".join(w)
    w = h.split()
    while len(" ".join(w)) > 30 and len(w) > 1:
        idx = [i for i, x in enumerate(w) if "*" not in x]
        if not idx:
            break
        w.pop(idx[-1])
    return " ".join(w)


def validate(spec, text=""):
    s = dict(spec) if isinstance(spec, dict) else {}
    lay = s.get("layout") if s.get("layout") in LAYOUTS else "center"
    objs = []
    for o in (s.get("objects") or [])[:LAYOUTS[lay]]:
        if not isinstance(o, dict):
            continue
        p = o.get("prop") if o.get("prop") in PROPS else "question"
        m = o.get("motion") if o.get("motion") in MOTIONS else "float"
        objs.append({"prop": p, "label": str(o.get("label", ""))[:16], "motion": m})
    if not objs and lay != "chart":
        objs = [{"prop": "lightbulb", "label": "", "motion": "float"}]
        lay = "center"
    h = s.get("hero")
    if isinstance(h, str):
        h = {"pose": h}
    if isinstance(h, dict):
        h = {"pose": h.get("pose") if h.get("pose") in POSES else "down", "motion": h.get("motion") if h.get("motion") in HERO_MOTIONS else "bob"}
    else:
        h = None
    ch = s.get("chart") if isinstance(s.get("chart"), dict) else None
    if lay == "chart":
        ch = ch or {"kind": "bars_up"}
        if ch.get("kind") not in CHARTS:
            ch["kind"] = "bars_up"
    out = {"headline": _headline_fix(s.get("headline"), text), "layout": lay, "objects": objs, "hero": h,
           "link": s.get("link") if s.get("link") in LINKS else "none", "chart": ch,
           "callout": (str(s["callout"])[:14] if s.get("callout") else None)}
    return out


# ------------------------------------------------------------------ LLM planner
class LLMPlanner:
    def __init__(self, model=None, api_key=None, chunk=12):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.model = model or os.environ.get("PLANNER_MODEL", "claude-sonnet-5-5")
        self.chunk = chunk
        self.fallback = HeuristicPlanner()

    def plan(self, beats):
        specs, recent = [], []
        for i in range(0, len(beats), self.chunk):
            part = beats[i:i + self.chunk]
            payload = {"previous_scenes": recent[-3:], "beats": [{"n": b["id"], "text": b["text"]} for b in part]}
            got = None
            for attempt in range(2):
                try:
                    r = self.client.messages.create(model=self.model, max_tokens=6000, system=_prompt_system(),
                                                    messages=[{"role": "user", "content": json.dumps(payload)}])
                    raw = "".join(c.text for c in r.content if getattr(c, "type", "") == "text")
                    raw = raw[raw.index("["): raw.rindex("]") + 1]
                    arr = json.loads(raw)
                    if isinstance(arr, list) and len(arr) == len(part):
                        got = arr
                        break
                except Exception as e:  # noqa
                    print(f"  planner attempt {attempt + 1} failed: {e}")
            if got is None:
                print("  falling back to heuristic planner for this chunk")
                got = self.fallback.plan(part, offset_specs=recent)
            for b, sp in zip(part, got):
                v = validate(sp, b["text"])
                specs.append(v)
                recent.append({"layout": v["layout"], "props": [o["prop"] for o in v["objects"]]})
        return specs


# ------------------------------------------------------------------ heuristic planner
KW = [
    (("chip", "gpu", "processor", "semiconductor"), "chip"), (("data centre", "data center", "server", "infrastructure"), "datacentre"),
    (("billion", "million", "revenue", "profit", "cash", "money", "dollar", "$", "sales"), "moneybag"),
    (("sec ", "investigat", "audit", "scrutiny", "inquiry", "regulator"), "magnifier"), (("report", "filing", "accounting", "accounts", "statement"), "document"),
    (("news", "reuters", "headline", "press"), "newspaper"), (("country", "countries", "global", "world", "geograph"), "globe"),
    (("company", "companies", "business", "headquarters", "firm"), "building"), (("bank", "loan", "lender", "borrow", "debt"), "bank"),
    (("investor", "customer", "people", "person", "founder", "billionaire"), "person"), (("grow", "boom", "launch", "surge", "rocket"), "rocket"),
    (("win", "record", "success", "champion", "best"), "trophy"), (("time", "year", "week", "day", "hour", "deadline"), "clock"),
    (("idea", "lesson", "insight", "realize", "understand"), "lightbulb"), (("risk", "danger", "crisis", "collapse", "crash"), "fire"),
    (("safe", "protect", "hedge", "secure"), "shield"), (("power", "electric", "energy"), "bolt"), (("cloud",), "cloud"),
    (("process", "system", "mechanism", "works"), "gear"), (("house", "home", "real estate", "property"), "house"),
    (("watch", "attention", "eyes", "scrutin"), "eye"), (("balance", "fair", "verdict", "guilty"), "scale"),
    (("price", "cost", "cheap", "expensive"), "tag"), (("phone", "message", "notification"), "phone"), (("no ", "not ", "never", "without"), "cross"),
]
STOP = set("the a an and or but of to in on at for with from by is are was were be been it its this that these those you your we our they their he she i as so if then than when what which who how why not no do does did have has had will would can could should may might just very also".split())


class HeuristicPlanner:
    CYCLE = ["hero_scene", "split", "row3", "center", "flow", "versus", "hero_center"]

    def plan(self, beats, offset_specs=None):
        specs, last, k = [], None, 0
        for b in beats:
            text = b["text"]
            low = " " + text.lower() + " "
            props = []
            for keys, p in KW:
                if any(w in low for w in keys) and p not in props:
                    props.append(p)
            if "?" in text and "question" not in props:
                props.insert(0, "question")
            nums = re.findall(r"\$?\d[\d,\.]*\s?(?:billion|million|%|B|M)?", text)
            callout = nums[0].strip() if nums else None
            if callout:
                callout = re.sub(r"\s*billion", "B", callout)
                callout = re.sub(r"\s*million", "M", callout)
            if callout and len(callout) < 2:
                callout = None
            lay = None
            chart = None
            if callout and re.search(r"grew|double|rise|rose|growth|increase|up|record|surge", low):
                lay, chart = "chart", {"kind": "bars_up"}
            elif callout and re.search(r"fell|drop|decline|down|collapse|lose|loss", low):
                lay, chart = "chart", {"kind": "bars_down"}
            elif callout and "%" in text:
                lay, chart = "chart", {"kind": "pie", "value": float(re.search(r"(\d+(?:\.\d+)?)\s?%", text).group(1))}
            elif len(props) >= 3:
                lay = "row3"
            elif len(props) == 2:
                lay = "flow" if re.search(r"loop|cycle|ecosystem|each other|circular", low) else "split"
            if lay is None or lay == last:
                lay = self.CYCLE[k % len(self.CYCLE)]
                k += 1
                if lay == last:
                    lay = self.CYCLE[k % len(self.CYCLE)]
                    k += 1
            need = LAYOUTS[lay]
            fill = ["lightbulb", "gear", "globe", "eye"]
            while len(props) < need:
                props.append(fill[len(props) % len(fill)])
            objs = [{"prop": p, "label": "", "motion": MOTIONS[(i + k) % 4 + 1]} for i, p in enumerate(props[:need])]
            hero = None
            if lay in ("hero_scene", "hero_center") or re.search(r"\byou\b|\byour\b|\bi\b", low):
                pose = "up" if re.search(r"win|grow|record|strong|success|rocket", low) else ("shrug" if "?" in text else "fwd")
                hero = {"pose": pose, "motion": "jump" if pose == "up" else "bob"}
                if lay not in ("hero_scene", "hero_center", "chart", "center"):
                    hero = None
            link = "coins" if re.search(r"money|fund|financ|invest|pay|loan|borrow|\$", low) and need > 1 else ("arrow" if need > 1 else "none")
            if lay == "flow" and link == "arrow":
                link = "loop"
            words = [w for w in re.findall(r"\$?\d[\d,\.]*[%BM]?|[A-Za-z']+", text) if w.lower() not in STOP]
            head = " ".join(words[:4]) if words else text[:24]
            specs.append(validate({"headline": head, "layout": lay, "objects": objs, "hero": hero, "link": link,
                                   "chart": chart, "callout": callout}, text))
            last = lay
        return specs
