#!/usr/bin/env python3
"""Validate the exercise content. Run before every commit. Needs `pip install jsonschema`.

Usage: python3 validate.py
Exit code 1 if anything fails.
"""
import json
import sys

from jsonschema import Draft202012Validator

from datum_exercises import (
    AGGREGATE, EXERCISES_DIR, IMAGES_DIR, MANIFEST, PROVENANCE, ROOT, build_aggregate_text, jpeg_info, load_sources,
    normalize, sha256_file, short_hash,
)

MUSCLES = {
    "abdominals", "abductors", "adductors", "biceps", "calves", "chest", "forearms", "glutes", "hamstrings",
    "lats", "lower back", "middle back", "neck", "quadriceps", "shoulders", "traps", "triceps",
}
EQUIPMENT = {
    "barbell", "dumbbell", "cable", "machine", "kettlebells", "bands", "medicine ball", "exercise ball",
    "foam roll", "e-z curl bar", "body only", "other", None,
}
CATEGORIES = {"strength", "stretching", "cardio", "plyometrics", "powerlifting", "strongman", "olympic weightlifting"}
FORCES = {"push", "pull", "static", None}
LEVELS = {"beginner", "intermediate", "expert"}
MECHANIC_REQUIRED = {"strength", "plyometrics", "powerlifting", "strongman", "olympic weightlifting"}

# Legacy entries from the original seed that have a null mechanic although their category requires one.
# The data is not edited, so these ids are allowed to stay null. This list is closed: never add to it.
# New exercises must have a mechanic.
KNOWN_LEGACY_MECHANIC_NULLS = {
    "Carioca_Quick_Step",
    "Double_Kettlebell_Windmill",
    "Kettlebell_Figure_8",
    "Kneeling_Arm_Drill",
    "Reverse_Hyperextension",
    "Side_Bridge",
    "Single-Cone_Sprint_Drill",
}

# Legacy entries from the original seed that contain one blank instruction step. The data is not edited,
# so these ids may keep it. This list is closed: never add to it. New exercises get no blank steps.
KNOWN_LEGACY_BLANK_STEPS = {"Barbell_Squat_To_A_Bench", "Clean"}

MAX_IMAGE_BYTES = 150 * 1024
IMAGE_SIZE = (850, 567)

errors = []


def err(msg):
    errors.append(msg)


def check_exercises(sources):
    schema = json.loads((ROOT / "schema/exercise.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    names = {}
    # An alias may repeat the name of a retired exercise: that is how a merged exercise keeps its
    # old name searchable (Side Bridge on Side Plank). Retired names still count for duplicate names.
    live_names = {}
    for ex_id, e in sources.items():
        label = f"exercises/{ex_id}.json"
        for problem in validator.iter_errors(e):
            where = "/".join(str(p) for p in problem.absolute_path)
            err(f"{label}: {where}: {problem.message}" if where else f"{label}: {problem.message}")
        if e.get("id") != ex_id:
            err(f"{label}: id {e.get('id')!r} does not match filename")
        name = e.get("name", "")
        key = normalize(name)
        if key in names:
            err(f"{label}: normalized name {key!r} also used by {names[key]}")
        names[key] = ex_id
        if not e.get("retired", False):
            live_names[key] = ex_id
        for field in ("primaryMuscles", "secondaryMuscles"):
            for m in e.get(field, []):
                if m not in MUSCLES:
                    err(f"{label}: {field} has unknown muscle {m!r}")
        if e.get("equipment") not in EQUIPMENT:
            err(f"{label}: unknown equipment {e.get('equipment')!r}")
        if e.get("category") not in CATEGORIES:
            err(f"{label}: unknown category {e.get('category')!r}")
        if e.get("force") not in FORCES:
            err(f"{label}: unknown force {e.get('force')!r}")
        if e.get("level") not in LEVELS:
            err(f"{label}: unknown level {e.get('level')!r}")
        if (e.get("category") in MECHANIC_REQUIRED and e.get("mechanic") is None
                and ex_id not in KNOWN_LEGACY_MECHANIC_NULLS):
            err(f"{label}: mechanic is required for category {e.get('category')!r}")
        if not e.get("retired", False) and not any(s.strip() for s in e.get("instructions", [])):
            err(f"{label}: instructions are empty")
        if any(not s.strip() for s in e.get("instructions", [])) and ex_id not in KNOWN_LEGACY_BLANK_STEPS:
            err(f"{label}: instructions contain a blank step")
    # Aliases: unique across all names and all other aliases, same normalization as the app.
    alias_owner = {}
    for ex_id, e in sources.items():
        seen_here = set()
        for alias in e.get("aliases", []):
            key = normalize(alias)
            label = f"exercises/{ex_id}.json"
            if not key:
                err(f"{label}: alias {alias!r} normalizes to nothing")
                continue
            if key in seen_here:
                err(f"{label}: duplicate alias {alias!r}")
            seen_here.add(key)
            if key in live_names:
                err(f"{label}: alias {alias!r} equals the name of {live_names[key]}")
            if key in alias_owner and alias_owner[key] != ex_id:
                err(f"{label}: alias {alias!r} also used by {alias_owner[key]}")
            alias_owner.setdefault(key, ex_id)


def check_build(sources):
    text, entries = build_aggregate_text(sources)
    if not AGGREGATE.exists() or AGGREGATE.read_text(encoding="utf-8") != text:
        err("exercises.json is stale: run python3 build.py")
        return entries
    return entries


def check_manifest(sources, entries):
    if not MANIFEST.exists():
        err("manifest.json is missing")
        return
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if m.get("schema_version") != 1:
        err("manifest schema_version must be 1")
    if not isinstance(m.get("content_version"), int) or m["content_version"] < 1:
        err("manifest content_version must be an integer >= 1")
    if m.get("exercises_file") != "exercises.json":
        err("manifest exercises_file must be exercises.json")
    if AGGREGATE.exists() and m.get("exercises_sha256") != sha256_file(AGGREGATE):
        err("manifest exercises_sha256 does not match exercises.json: run python3 build.py")
    if m.get("exercise_count") != len(entries):
        err(f"manifest exercise_count {m.get('exercise_count')} != {len(entries)}")
    images = m.get("images", {})
    for ex_id, digest in images.items():
        path = IMAGES_DIR / f"{ex_id}.jpg"
        if ex_id not in sources:
            err(f"manifest image {ex_id}: no such exercise")
        if not path.exists():
            err(f"manifest image {ex_id}: images/{ex_id}.jpg is missing")
            continue
        if short_hash(path) != digest:
            err(f"manifest image {ex_id}: hash does not match the file: run python3 build.py")
    for path in sorted(IMAGES_DIR.glob("*.jpg")):
        if path.stem not in images:
            err(f"images/{path.name} is not in the manifest: run python3 build.py")
        is_jpeg, w, h = jpeg_info(path)
        if not is_jpeg:
            err(f"images/{path.name}: not a JPEG")
        elif (w, h) != IMAGE_SIZE:
            err(f"images/{path.name}: size {w}x{h}, expected {IMAGE_SIZE[0]}x{IMAGE_SIZE[1]}")
        if path.stat().st_size >= MAX_IMAGE_BYTES:
            err(f"images/{path.name}: {path.stat().st_size} bytes, must be under {MAX_IMAGE_BYTES}")
    if PROVENANCE.exists():
        prov = json.loads(PROVENANCE.read_text(encoding="utf-8"))
        for ex_id in prov:
            if ex_id not in sources:
                err(f"images/provenance.json: unknown exercise {ex_id}")


def main():
    sources = load_sources()
    if not sources:
        err("no files in exercises/")
    check_exercises(sources)
    entries = check_build(sources)
    check_manifest(sources, entries)
    legacy_present = sorted(i for i in KNOWN_LEGACY_MECHANIC_NULLS if i in sources)
    for ex_id in KNOWN_LEGACY_MECHANIC_NULLS - set(sources):
        err(f"KNOWN_LEGACY_MECHANIC_NULLS lists {ex_id}, which does not exist")
    for ex_id in legacy_present:
        if sources[ex_id].get("mechanic") is not None:
            err(f"KNOWN_LEGACY_MECHANIC_NULLS lists {ex_id}, which now has a mechanic: remove it from the list")
    if errors:
        print("\n".join(errors))
        print(f"FAILED: {len(errors)} problem(s) in {len(sources)} exercises")
        sys.exit(1)
    n_alias = sum(len(e.get("aliases", [])) for e in sources.values())
    n_with = sum(1 for e in sources.values() if e.get("aliases"))
    print(f"KNOWN_LEGACY_MECHANIC_NULLS allowlist: {len(legacy_present)} ids")
    print(f"KNOWN_LEGACY_BLANK_STEPS allowlist: {len(KNOWN_LEGACY_BLANK_STEPS)} ids")
    print(f"OK: {len(sources)} exercises, {n_alias} aliases on {n_with} exercises, "
          f"{len(list(IMAGES_DIR.glob('*.jpg')))} remote images")


if __name__ == "__main__":
    main()
