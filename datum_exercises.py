"""Shared helpers for the Datum-Exercises scripts: paths, loading, serialization, normalization."""
import hashlib
import json
import os
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXERCISES_DIR = ROOT / "exercises"
IMAGES_DIR = ROOT / "images"
PROVENANCE = IMAGES_DIR / "provenance.json"
MANIFEST = ROOT / "manifest.json"
AGGREGATE = ROOT / "exercises.json"
STYLE_FILE = ROOT / "image-style.md"

# Fixed key order for every serialized exercise. Keys not listed here sort after these, alphabetically.
KEY_ORDER = [
    "name", "force", "level", "mechanic", "equipment", "primaryMuscles", "secondaryMuscles",
    "instructions", "category", "images", "id", "isTimeBased", "isPerSide", "aliases", "retired",
    "image_prompt_scene",
]
REPO_ONLY_KEYS = {"image_prompt_scene"}
MANIFEST_ORDER = [
    "schema_version", "content_version", "updated", "exercises_file", "exercises_sha256",
    "exercise_count", "images",
]


def ordered(entry):
    keys = [k for k in KEY_ORDER if k in entry] + sorted(k for k in entry if k not in KEY_ORDER)
    return {k: entry[k] for k in keys}


def dumps(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def load_sources():
    """Return all exercises/<id>.json files as {id: entry}, keyed by filename stem."""
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(EXERCISES_DIR.glob("*.json"))}


def build_aggregate_text(sources):
    entries = []
    for entry in sources.values():
        public = {k: v for k, v in entry.items() if k not in REPO_ONLY_KEYS}
        entries.append(ordered(public))
    entries.sort(key=lambda e: e["id"])
    return dumps(entries), entries


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def short_hash(path):
    return sha256_file(path)[:16]


def normalize(text):
    """Match the app's name normalization: lowercase, strip diacritics, runs of non-alphanumerics become one space."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join("".join(c if c.isalnum() else " " for c in stripped).split())


def bundled_dir():
    app = Path(os.environ.get("DATUM_APP_DIR", str(ROOT.parent / "datum"))).expanduser()
    return app / "Datum" / "Resources" / "ExerciseImages"


def has_bundled(ex_id, directory):
    return directory.is_dir() and (directory / f"{ex_id}.jpg").exists()


def missing_exercises(sources):
    """Non-retired exercises with neither a bundled app image nor a remote image, sorted by id."""
    directory = bundled_dir()
    if not directory.is_dir():
        import sys
        print(f"warning: bundled image folder not found at {directory}; treating none as bundled", file=sys.stderr)
    return [
        sources[i] for i in sorted(sources)
        if not sources[i].get("retired", False)
        and not has_bundled(i, directory)
        and not (IMAGES_DIR / f"{i}.jpg").exists()
    ]


def jpeg_info(path):
    """Return (is_jpeg, width, height) by parsing the JPEG header; no Pillow needed."""
    data = Path(path).read_bytes()
    if data[:2] != b"\xff\xd8":
        return False, 0, 0
    i = 2
    while i + 4 <= len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7 or marker == 0xFF:
            i += 1 if marker == 0xFF else 2
            continue
        length = int.from_bytes(data[i + 2:i + 4], "big")
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            height = int.from_bytes(data[i + 5:i + 7], "big")
            width = int.from_bytes(data[i + 7:i + 9], "big")
            return True, width, height
        i += 2 + length
    return True, 0, 0
