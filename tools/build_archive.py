"""Keep every article forever.

Reads every edition file in data/ (data/YYYY-MM-DD-HH.json) and writes
  data/index.json            {"dates": [all edition IDs, newest first]}
  data/archive/index.json    {"months": ["2026-11", ...], "count": N, "updated": "..."}
  data/archive/YYYY-MM.json  {"month": "...", "articles": [...]}  every unique article, newest first

An article seen in several editions is stored once (keyed by its link, or its title when there is no link);
the newest wording is kept and the first/last edition it appeared in is recorded.
Run by .github/workflows/archive.yml after every edition push; safe to run any number of times.
"""
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
ARCH = os.path.join(DATA, "archive")
ID_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})(?:-(\d{2}))?$")


def edition_ids():
    ids = []
    for name in os.listdir(DATA):
        if not name.endswith(".json") or name == "index.json":
            continue
        eid = name[:-5]
        if ID_RE.match(eid):
            ids.append(eid)
    # "2026-11-23" (old daily file) sorts as the start of that day
    return sorted(ids, key=lambda i: (i[:10], i[11:13] if len(i) > 10 else "00"), reverse=True)


def key_of(item):
    url = (item.get("url") or "").strip()
    # aggregator pages (one link for many stories) can't identify a story; use the title for those
    generic = not url or "etoland.co.kr" in url or "/rank/" in url
    basis = ("t:" + re.sub(r"\s+", "", item.get("title", ""))) if generic else ("u:" + url)
    return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]


def main():
    ids = edition_ids()
    with open(os.path.join(DATA, "index.json"), "w", encoding="utf-8") as f:
        json.dump({"dates": ids}, f, ensure_ascii=False)

    seen = {}
    for eid in reversed(ids):  # oldest first, so newer editions overwrite the wording
        try:
            with open(os.path.join(DATA, eid + ".json"), encoding="utf-8") as f:
                doc = json.load(f)
        except Exception as e:  # a broken file must not stop the archive
            print("skip", eid, e, file=sys.stderr)
            continue
        date = doc.get("date") or eid[:10]
        for sec in doc.get("sections") or []:
            for it in sec.get("items") or []:
                if not it.get("title"):
                    continue
                k = key_of(it)
                prev = seen.get(k)
                rec = {
                    "key": k,
                    "category": sec.get("category", ""),
                    "topic": it.get("topic", ""),
                    "title": it.get("title", ""),
                    "summary": it.get("summary", ""),
                    "source": it.get("source", ""),
                    "url": it.get("url", ""),
                    "verify": it.get("verify") or {},
                    "date": prev["date"] if prev else date,
                    "first": prev["first"] if prev else eid,
                    "last": eid,
                }
                seen[k] = rec
        m = doc.get("markets")
        if m and m.get("summary"):
            k = hashlib.sha1(("m:" + eid).encode()).hexdigest()[:16]
            seen[k] = {"key": k, "category": "증시", "topic": "경제", "market": True,
                       "title": m.get("headline") or "증시", "summary": m.get("summary", ""),
                       "source": m.get("source", ""), "url": m.get("url", ""), "verify": m.get("verify") or {},
                       "asOf": m.get("asOf", ""), "date": date, "first": eid, "last": eid}

    os.makedirs(ARCH, exist_ok=True)
    by_month = {}
    for rec in seen.values():
        by_month.setdefault(rec["date"][:7], []).append(rec)
    months = sorted(by_month, reverse=True)
    for mon in months:
        arts = sorted(by_month[mon], key=lambda r: (r["last"], r["first"]), reverse=True)
        with open(os.path.join(ARCH, mon + ".json"), "w", encoding="utf-8") as f:
            json.dump({"month": mon, "articles": arts}, f, ensure_ascii=False)
    with open(os.path.join(ARCH, "index.json"), "w", encoding="utf-8") as f:
        json.dump({"months": months, "count": len(seen), "editions": len(ids),
                   "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}, f, ensure_ascii=False)
    print(f"{len(ids)} editions, {len(seen)} unique articles, months: {months}")


if __name__ == "__main__":
    main()
