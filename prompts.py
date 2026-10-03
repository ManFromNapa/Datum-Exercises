#!/usr/bin/env python3
"""Print ready-to-paste image prompts.

Usage:
  python3 prompts.py --id <id> [--tool chatgpt|gemini|midjourney]
  python3 prompts.py --missing [--batch N] [--offset M | --batch-index K] [--tool ...]
  add --person N (1-based, from the People list) or --person-text "..." to override the person

--missing lists exercises with no bundled app image and no remote image, sorted by id.
Set DATUM_APP_DIR to the datum app repo (default ../datum) to find the bundled images.
"""
import argparse
import re
import sys

from datum_exercises import STYLE_FILE, load_sources, missing_exercises


def read_style():
    text = STYLE_FILE.read_text(encoding="utf-8")
    block = re.search(r"<!-- style-block:start -->\s*(.*?)\s*<!-- style-block:end -->", text, re.S)
    params = re.search(r"^midjourney_params:\s*(.+)$", text, re.M)
    if not block or not params:
        sys.exit("image-style.md needs a style block between the markers and a midjourney_params line")
    people = re.search(r"<!-- people:start -->\s*(.*?)\s*<!-- people:end -->", text, re.S)
    if not people or "{person}" not in block.group(1):
        sys.exit("image-style.md needs a people list between its markers and {person} in the style block")
    persons = [line.strip() for line in people.group(1).splitlines() if line.strip()]
    return " ".join(block.group(1).split()), params.group(1).strip(), persons


def build_prompt(e, style, params, tool, person):
    scene = e.get("image_prompt_scene")
    if not scene:
        steps = e.get("instructions") or []
        scene = steps[0] if steps else e["name"]
        print(f"note: {e['id']} has no image_prompt_scene; using the first instruction step", file=sys.stderr)
    scene = scene.strip().rstrip(".!?")
    equipment = e.get("equipment") or "none"
    text = f"Exercise: {e['name']}. Start position: {scene}. Equipment: {equipment}. {style.replace('{person}', person)}"
    return f"{text} {params}" if tool == "midjourney" else text


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--id", help="print the prompt for one exercise id")
    ap.add_argument("--missing", action="store_true", help="every exercise with no bundled or remote image")
    ap.add_argument("--batch", type=int, metavar="N", help="take N missing exercises")
    ap.add_argument("--offset", type=int, default=None, help="skip this many missing exercises first")
    ap.add_argument("--batch-index", type=int, default=None, help="skip K*N missing exercises (0-based batch number)")
    ap.add_argument("--person", type=int, metavar="N", help="use person N (1-based) from the People list for every prompt")
    ap.add_argument("--person-text", help="use this description of the person for every prompt")
    ap.add_argument("--tool", choices=["chatgpt", "gemini", "midjourney"], default="chatgpt")
    args = ap.parse_args()
    if bool(args.id) == args.missing:
        ap.error("give exactly one of --id or --missing")
    if args.offset is not None and args.batch_index is not None:
        ap.error("use --offset or --batch-index, not both")
    if args.batch_index is not None and not args.batch:
        ap.error("--batch-index needs --batch")

    sources = load_sources()
    style, params, persons = read_style()
    all_ids = sorted(sources)

    def person_for(e):
        if args.person_text:
            return args.person_text.strip().rstrip(".")
        if args.person:
            return persons[(args.person - 1) % len(persons)]
        return persons[all_ids.index(e["id"]) % len(persons)]

    if args.id:
        if args.id not in sources:
            sys.exit(f"unknown id {args.id}")
        chosen = [sources[args.id]]
    else:
        chosen = missing_exercises(sources)
        start = args.offset if args.offset is not None else (args.batch_index * args.batch if args.batch_index is not None else 0)
        chosen = chosen[start:start + args.batch] if args.batch else chosen[start:]
        if not chosen:
            print("no exercises in this range", file=sys.stderr)
    for n, e in enumerate(chosen):
        if len(chosen) > 1:
            print(f"## {e['id']}")
        print(build_prompt(e, style, params, args.tool, person_for(e)))
        if len(chosen) > 1 and n < len(chosen) - 1:
            print()


if __name__ == "__main__":
    main()
