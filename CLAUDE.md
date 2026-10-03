# Working conventions

Repo for the Datum exercise library, at github.com/ManFromNapa/Datum-Exercises (public). Push only when Alex asks.

- The served URL contract is fixed: `exercises.json`, `manifest.json` and `images/<id>.jpg` at the site root. Do not rename or move them.
- Ids are permanent. Never delete an exercise or change its id. Retire it with `retired: true`.
- `exercises/<id>.json` is the source of truth. Never hand-edit `exercises.json`; run `python3 build.py`.
- Run `python3 validate.py` before every commit. It must print OK.
- Do not bump `content_version` unless content changed, and do it by hand after `build.py`.
- Do not add enum values or muscles until the shipped app supports them.
- Do not add ids to the legacy allowlists in `validate.py`.
- Do not modify the datum or Aminolog repos from here.
- Style for text, comments and commit messages: no em dashes, concise, Markdown.
- Commit trailer: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
