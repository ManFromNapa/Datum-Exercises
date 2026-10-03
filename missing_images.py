#!/usr/bin/env python3
"""List exercises that still have no image, bundled in the app or remote here, and count them.

Usage: python3 missing_images.py
Set DATUM_APP_DIR to the datum app repo (default ../datum) to find the bundled images.
"""
from datum_exercises import bundled_dir, load_sources, missing_exercises


def main():
    sources = load_sources()
    missing = missing_exercises(sources)
    for e in missing:
        print(f"{e['id']}\t{e['name']}")
    active = sum(1 for e in sources.values() if not e.get("retired", False))
    print(f"{len(missing)} of {active} exercises have no bundled or remote image (bundled folder: {bundled_dir()})")


if __name__ == "__main__":
    main()
