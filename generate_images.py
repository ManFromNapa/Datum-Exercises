#!/usr/bin/env python3
"""Generate exercise images with the Gemini API, then turn them into images/<id>.jpg.

Usage:
  export GEMINI_API_KEY=...            (never put the key in the repo)
  python3 generate_images.py --missing --batch 5          # try 5 first
  python3 generate_images.py --id Burpee --force          # redo one
  python3 generate_images.py --missing --batch 5 --dry-run   # print prompts, call nothing

Each result is saved raw to staging/ (ignored by git), then processed with process_image.py
(tool recorded as "gemini"). Exercises that already have an image are skipped, so a run can be
repeated safely. Afterwards run `python3 review_sheet.py` and open review.html to check them.
Does not bump content_version.
"""
import argparse
import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

from datum_exercises import ROOT, load_sources, missing_exercises
from prompts import build_prompt, default_person, read_style

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
DEFAULT_MODEL = "gemini-3.1-flash-image"
STAGING = ROOT / "staging"


def find_image_base64(node):
    """The API nests the image under an output field; take the first long base64 string under a 'data' key."""
    if isinstance(node, dict):
        data = node.get("data")
        if isinstance(data, str) and len(data) > 1000:
            return data
        for value in node.values():
            found = find_image_base64(value)
            if found:
                return found
    elif isinstance(node, list):
        for value in node:
            found = find_image_base64(value)
            if found:
                return found
    return None


def request_image(prompt, model, key):
    body = json.dumps({
        "model": model,
        "input": [{"type": "text", "text": prompt}],
        "response_format": {"type": "image", "mime_type": "image/jpeg", "aspect_ratio": "3:2"},
    }).encode()
    req = urllib.request.Request(
        ENDPOINT, data=body, method="POST",
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = find_image_base64(json.load(resp))
            if not data:
                raise RuntimeError("response had no image (the prompt may have been blocked)")
            return base64.b64decode(data)
        except urllib.error.HTTPError as err:
            detail = err.read().decode("utf-8", "replace")[:300]
            if err.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(5 * 2 ** attempt)
                continue
            raise RuntimeError(f"HTTP {err.code}: {detail}")
        except (urllib.error.URLError, TimeoutError) as err:
            if attempt < 3:
                time.sleep(5 * 2 ** attempt)
                continue
            raise RuntimeError(f"network error: {err}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--id", help="one exercise id")
    ap.add_argument("--missing", action="store_true", help="every exercise with no image")
    ap.add_argument("--batch", type=int, metavar="N", help="only the first N")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--force", action="store_true", help="redo an exercise that already has an image")
    ap.add_argument("--dry-run", action="store_true", help="print the prompts and call nothing")
    ap.add_argument("--delay", type=float, default=2.0, help="seconds between requests")
    args = ap.parse_args()
    if bool(args.id) == args.missing:
        ap.error("give exactly one of --id or --missing")

    sources = load_sources()
    style, params, persons = read_style()
    all_ids = sorted(sources)
    if args.id:
        if args.id not in sources:
            sys.exit(f"unknown id {args.id}")
        chosen = [sources[args.id]]
    else:
        chosen = missing_exercises(sources)
        if args.batch:
            chosen = chosen[:args.batch]

    if not chosen:
        print("Every exercise already has an image. Nothing to generate.")
        return

    key = os.environ.get("GEMINI_API_KEY")
    if not key and not args.dry_run:
        sys.exit("set GEMINI_API_KEY in your environment first (do not put it in the repo)")

    STAGING.mkdir(exist_ok=True)
    done, failed = [], []
    for n, e in enumerate(chosen, 1):
        prompt = build_prompt(e, style, params, "gemini", default_person(e["id"], all_ids, persons))
        if args.dry_run:
            print(f"## {e['id']}\n{prompt}\n")
            continue
        print(f"[{n}/{len(chosen)}] {e['id']} ...", flush=True)
        try:
            raw = request_image(prompt, args.model, key)
            raw_path = STAGING / f"{e['id']}.jpg"
            raw_path.write_bytes(raw)
            subprocess.run(
                [sys.executable, str(ROOT / "process_image.py"), str(raw_path), e["id"], "--tool", "gemini"],
                check=True, cwd=ROOT, stdout=subprocess.DEVNULL,
            )
            done.append(e["id"])
        except (RuntimeError, subprocess.CalledProcessError) as err:
            print(f"  failed: {err}", file=sys.stderr)
            failed.append(e["id"])
        time.sleep(args.delay)
    if not args.dry_run:
        print(f"\nmade {len(done)}, failed {len(failed)}" + (f": {', '.join(failed)}" if failed else ""))
        print("next: python3 review_sheet.py, then open review.html")


if __name__ == "__main__":
    main()
