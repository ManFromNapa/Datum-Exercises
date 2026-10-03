#!/usr/bin/env python3
"""Rebuild exercises.json and the manifest's hash, count and images map from exercises/*.json and images/*.jpg.

Does not bump content_version or change `updated`; do that by hand when content changes.
Usage: python3 build.py
"""
import json

from datum_exercises import (
    AGGREGATE, IMAGES_DIR, MANIFEST, MANIFEST_ORDER, build_aggregate_text, dumps, load_sources, sha256_file, short_hash,
)


def main():
    sources = load_sources()
    text, entries = build_aggregate_text(sources)
    AGGREGATE.write_text(text, encoding="utf-8")

    old = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    images = {p.stem: short_hash(p) for p in sorted(IMAGES_DIR.glob("*.jpg")) if p.stem in sources}
    manifest = {
        "schema_version": 1,
        "content_version": old.get("content_version", 1),
        "updated": old.get("updated", "2026-10-03"),
        "exercises_file": "exercises.json",
        "exercises_sha256": sha256_file(AGGREGATE),
        "exercise_count": len(entries),
        "images": images,
    }
    MANIFEST.write_text(dumps({k: manifest[k] for k in MANIFEST_ORDER}), encoding="utf-8")
    print(f"built exercises.json ({len(entries)} exercises) and manifest.json ({len(images)} images, content_version {manifest['content_version']})")


if __name__ == "__main__":
    main()
