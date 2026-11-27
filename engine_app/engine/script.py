"""Parse a narration script into beats. Supports plain prose or '(m:ss) text' timestamped lines."""
import re

TS = re.compile(r"^\(?\s*(\d{1,2}):(\d{2})(?:\s*[-–]\s*(\d{1,2}):(\d{2}))?\s*\)?\s*(.*)$")


def _clean(line):
    line = line.strip()
    line = re.sub(r"^#+\s*", "", line)
    line = line.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    return line.replace("\u2014", ", ").replace("\u2013", "-")


def parse(text, max_words=34, min_words=9):
    lines = [_clean(l) for l in text.splitlines() if l.strip()]
    stamped = sum(1 for l in lines if TS.match(l)) >= max(2, len(lines) // 3)
    beats = []
    if stamped:
        for l in lines:
            m = TS.match(l)
            if not m or not m.group(5).strip():
                continue  # headings, titles, '---'
            start = int(m.group(1)) * 60 + int(m.group(2))
            beats.append({"text": m.group(5).strip(), "start": start})
    else:
        sents = []
        for l in lines:
            if re.fullmatch(r"[-=*_ ]{3,}", l):
                continue
            if len(l.split()) < 5 and not re.search(r"[.!?]$", l):
                continue  # looks like a heading
            sents += [s.strip() for s in re.split(r"(?<=[.!?])\s+", l) if s.strip()]
        cur = ""
        for s in sents:
            if cur and len((cur + " " + s).split()) > max_words:
                beats.append({"text": cur})
                cur = s
            else:
                cur = (cur + " " + s).strip()
            if len(cur.split()) >= min_words and re.search(r"[.!?]$", cur):
                beats.append({"text": cur})
                cur = ""
        if cur:
            beats.append({"text": cur})
    for i, b in enumerate(beats):
        b["id"] = i + 1
    return beats
