#!/usr/bin/env python3
"""Index Markdown notes into web/data.js using only Python's standard library."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NOTES_DIR = ROOT / "notes"
OUTPUT = ROOT / "web" / "data.js"

def title_of(text, path):
    for line in text.splitlines():
        m = re.match(r"^\s*#\s+(.+?)\s*$", line)
        if m:
            return m.group(1).strip()
    return path.stem.replace("_", " ").strip()

def clean_text(text):
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", text)
    text = re.sub(r"[*_`>]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def category_for(path):
    try:
        rel = path.parent.relative_to(NOTES_DIR)
        return rel.parts[-1] if rel.parts else "یادداشت‌ها"
    except ValueError:
        return "یادداشت‌ها"

def main():
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(NOTES_DIR.rglob("*.md"))
    notes = []
    for path in files:
        raw = path.read_text(encoding="utf-8", errors="replace")
        title = title_of(raw, path)
        summary = clean_text(raw)
        if len(summary) > 600:
            summary = summary[:597].rstrip() + "..."
        rel = path.relative_to(NOTES_DIR)
        category = rel.parent.name if str(rel.parent) != "." else "یادداشت‌ها"
        notes.append({
            "id": len(notes),
            "title": title,
            "category": category,
            "summary": summary,
            "path": rel.as_posix()
        })

    title_to_ids = {}
    for note in notes:
        title_to_ids.setdefault(note["title"].casefold(), []).append(note["id"])

    links = []
    seen = set()
    for i, path in enumerate(files):
        raw = path.read_text(encoding="utf-8", errors="replace")
        body = raw.casefold()
        for other in notes:
            j = other["id"]
            if i == j:
                continue
            other_title = other["title"]
            linked = other_title.casefold() in body
            if not linked:
                for wiki in re.findall(r"\[\[([^\]]+)\]\]", raw):
                    normalized = wiki.split("|", 1)[0].strip().casefold()
                    if normalized == other_title.casefold() or normalized == Path(other["path"]).stem.casefold():
                        linked = True
                        break
            pair = (min(i, j), max(i, j))
            if linked and pair not in seen:
                seen.add(pair)
                links.append({"source": pair[0], "target": pair[1]})

    payload = {"nodes": notes, "links": links}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("window.NOTES_GRAPH = " + json.dumps(payload, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"Indexed {len(notes)} notes and {len(links)} links -> {OUTPUT}")

if __name__ == "__main__":
    main()
