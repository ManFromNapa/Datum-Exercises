#!/usr/bin/env python3
"""Write review.html: every image in images/ in a grid with its exercise name and id, newest first.

Usage: python3 review_sheet.py [--tool gemini] [--limit N]
Open review.html in a browser, note the ids that need a redo, then run
`python3 generate_images.py --id <id> --force` for each. review.html is ignored by git.
"""
import argparse
import html
import json

from datum_exercises import IMAGES_DIR, PROVENANCE, ROOT, load_sources


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tool", help="only images made with this tool")
    ap.add_argument("--limit", type=int, help="only the newest N")
    args = ap.parse_args()
    sources = load_sources()
    prov = json.loads(PROVENANCE.read_text(encoding="utf-8")) if PROVENANCE.exists() else {}
    files = sorted(IMAGES_DIR.glob("*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
    if args.tool:
        files = [p for p in files if prov.get(p.stem, {}).get("tool") == args.tool]
    if args.limit:
        files = files[:args.limit]
    cards = []
    for p in files:
        name = sources.get(p.stem, {}).get("name", p.stem)
        tool = prov.get(p.stem, {}).get("tool", "")
        cards.append(
            f'<figure><img src="images/{html.escape(p.name)}" loading="lazy">'
            f"<figcaption><b>{html.escape(name)}</b><br><code>{html.escape(p.stem)}</code> {html.escape(tool)}</figcaption></figure>"
        )
    page = (
        "<!doctype html><meta charset=utf-8><title>Image review</title>"
        "<style>body{font:14px system-ui;margin:16px;background:#f4f2f8}"
        ".g{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}"
        "figure{margin:0;background:#fff;padding:8px;border-radius:8px}img{width:100%;border-radius:4px}"
        "code{color:#6b46c1}</style>"
        f"<h2>{len(cards)} images</h2><div class=g>{''.join(cards)}</div>"
    )
    (ROOT / "review.html").write_text(page, encoding="utf-8")
    print(f"wrote review.html ({len(cards)} images)")


if __name__ == "__main__":
    main()
