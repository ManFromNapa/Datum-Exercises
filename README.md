# Datum Exercises

The exercise library for the Datum iOS app, served at `exercises.datumfitness.app` through GitHub Pages (to be set up; this repo is local only for now).

- `exercises/<id>.json`: one file per exercise. This is the source of truth, validated by `schema/exercise.schema.json`.
- `exercises.json`: built aggregate of all exercises, sorted by id, without repo-only fields. The app downloads this file. Never edit it by hand.
- `manifest.json`: `content_version`, the aggregate's hash and count, and a short hash per remote image. The app downloads files only when `content_version` is newer.
- `images/<id>.jpg`: remote images, one per exercise (start position, 850x567 JPEG, under 150 KB). `images/provenance.json` records which tool made each one.
- `image-style.md`: the shared image style block and Midjourney parameters.
- `schema/exercise.schema.json`: JSON Schema (draft 2020-12).

## Fields

The 879 original exercises keep the shape of the app's bundled seed: `id`, `name`, `force`, `level`, `mechanic`, `equipment`, `primaryMuscles`, `secondaryMuscles`, `instructions`, `category`, `images`. Optional additions:

- `isTimeBased`, `isPerSide`: booleans, absent means false.
- `aliases`: other names people search for. An alias must not equal the name of any live (not retired) exercise or any other alias after normalization; it may repeat the name of a retired exercise, which is how a merged exercise keeps its old name searchable (lowercase, no diacritics, every run of non-alphanumerics becomes one space).
- `retired`: true hides an exercise from new use. The file stays and the id is never reused.
- `image_prompt_scene`: repo-only (stripped from `exercises.json`). One sentence describing the start position, used by `prompts.py`.

## Update workflow

1. Edit or add files in `exercises/`. The filename is `<id>.json`.
2. `python3 build.py` rebuilds `exercises.json` and the manifest hashes.
3. `python3 validate.py` must print `OK`.
4. Bump `content_version` and set `updated` in `manifest.json` by hand.
5. Review the diff and commit. Do not push until the hosting is set up.

Setup: `pip install -r requirements.txt` (or use a `.venv`, which is gitignored). `validate.py` needs `jsonschema`; `process_image.py` needs `Pillow`.

## Scripts

| Command | What it does |
|---|---|
| `python3 validate.py` | Schema, vocabularies, ids, names, aliases, instructions, stale build, manifest hashes, image format and size |
| `python3 build.py` | Rebuilds `exercises.json` and the manifest hash, count and images map. Keeps `content_version` |
| `python3 prompts.py --id <id> [--tool chatgpt\|gemini\|midjourney]` | Prints one image prompt |
| `python3 prompts.py --missing [--batch N] [--offset M \| --batch-index K] [--tool ...]` | Prints prompts for exercises with no bundled and no remote image, sorted by id. `--batch-index K` skips K*N |
| `python3 process_image.py <input> <id> --tool <name>` | Crops to 3:2, resizes to 850x567, writes a progressive JPEG under 150 KB (60 to 70 KB when possible), records provenance, runs `build.py` |
| `python3 missing_images.py` | Lists exercises still without an image and counts them |

`prompts.py` and `missing_images.py` read the app's bundled images from `$DATUM_APP_DIR/Datum/Resources/ExerciseImages` (default `../datum`). If the folder is absent, nothing counts as bundled and a warning prints.

## Rules

- Ids are permanent. Never rename an id or delete an exercise; set `retired: true` instead.
- Never add a new enum value (equipment, category, muscle, force, level, mechanic) until the shipped app supports it. An older app that meets a value it does not know can reject the whole file, so it keeps its old copy. The same lesson cost a content release in Aminolog-Content. `validate.py` fixes the vocabularies; change them only after the app release that reads the new value is the minimum in use.
- Muscles come from the 17-value vocabulary in `schema/exercise.schema.json`.
- Every non-retired exercise needs non-empty instructions: second person, 3 to 6 plain steps.
- New exercises need a `mechanic` for strength, plyometrics, powerlifting, strongman and olympic weightlifting. `validate.py` has a closed allowlist (`KNOWN_LEGACY_MECHANIC_NULLS`, 7 ids) and one for blank steps (`KNOWN_LEGACY_BLANK_STEPS`, 2 ids) for original entries. Do not add to either.

## Images

The 878 images bundled in the app are not copied here. This repo starts with no remote images. New and missing images are generated with AI tools (see `image-style.md`), so they will not exactly match the old photographs. The gym and lighting will be close but not identical, and the person now varies (gender, ethnicity, age) from a list in `image-style.md`. The mix is expected.

## Generating images in bulk (Gemini)

1. `export GEMINI_API_KEY=...` (never commit the key).
2. `python3 generate_images.py --missing --batch 5` (try a few first). It builds each prompt, calls the Gemini image API, saves the raw file to `staging/` and runs `process_image.py` (tool recorded as `gemini`). Safe to re-run: exercises that already have an image are skipped.
3. `python3 review_sheet.py --tool gemini`, then open `review.html` and note the ids with wrong anatomy, hands or equipment.
4. Redo any with `python3 generate_images.py --id <id> --force`.
5. `python3 validate.py`, bump `content_version` and `updated`, commit, push.

`--dry-run` prints the prompts without calling the API. The API is billed per image and has no free tier.
