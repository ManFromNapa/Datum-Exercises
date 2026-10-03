#!/usr/bin/env python3
"""Turn any image into images/<id>.jpg: center-crop to 3:2, resize to 850x567, progressive JPEG under 150 KB.

Usage: python3 process_image.py <input> <id> --tool <name>
Records the tool and date in images/provenance.json, then runs build.py to refresh the manifest hash.
Does not bump content_version. Needs Pillow.
"""
import argparse
import io
import json
import subprocess
import sys
from datetime import date

from PIL import Image, ImageOps

from datum_exercises import IMAGES_DIR, PROVENANCE, ROOT, dumps, load_sources

SIZE = (850, 567)
TARGET_BYTES = 70 * 1024
LIMIT_BYTES = 150 * 1024


def encode(img, quality):
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("id")
    ap.add_argument("--tool", required=True, help="generator used, for example chatgpt, gemini or midjourney")
    args = ap.parse_args()

    if args.id not in load_sources():
        sys.exit(f"unknown exercise id {args.id}")
    img = ImageOps.exif_transpose(Image.open(args.input)).convert("RGB")
    img = ImageOps.fit(img, SIZE, Image.LANCZOS, centering=(0.5, 0.5))  # center-crops to 3:2, then resizes

    data = None
    fallback = None
    for quality in range(90, 19, -2):
        out = encode(img, quality)
        if len(out) <= TARGET_BYTES:
            data = out
            break
        if fallback is None and len(out) < LIMIT_BYTES:
            fallback = out
    data = data or fallback
    if data is None:
        sys.exit("could not get the image under 150 KB; try a simpler source image")

    IMAGES_DIR.mkdir(exist_ok=True)
    (IMAGES_DIR / f"{args.id}.jpg").write_bytes(data)
    prov = json.loads(PROVENANCE.read_text(encoding="utf-8")) if PROVENANCE.exists() else {}
    prov[args.id] = {"tool": args.tool, "date": date.today().isoformat()}
    PROVENANCE.write_text(dumps(dict(sorted(prov.items()))), encoding="utf-8")
    print(f"wrote images/{args.id}.jpg ({len(data) / 1024:.1f} KB)")
    subprocess.run([sys.executable, str(ROOT / "build.py")], check=True, cwd=ROOT)


if __name__ == "__main__":
    main()
