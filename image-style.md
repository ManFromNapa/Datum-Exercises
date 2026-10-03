# Image style

Datum shows one image per exercise: frame 0, the start position. The target is an 850x567 landscape JPEG, 60 to 70 KB.
Existing images are photographs of one man in a gym with a red wall and a wood floor. New images must match.

`prompts.py` reads the style block between the markers below and the `midjourney_params` line. Edit them here only.

<!-- style-block:start -->
Photorealistic photograph, 3:2 landscape. One fit adult man with short dark hair, wearing a fitted dark athletic t-shirt, dark shorts and grey and white training shoes. Bright commercial gym with a red wall, a wood-grain floor and dark rubber mats, natural indoor light. Full body in frame. Camera at about chest height from a side or three-quarter angle. Correct anatomy and hands, realistic equipment. No text, no logos, no watermark, no other people.
<!-- style-block:end -->

midjourney_params: --ar 3:2 --style raw

## Per-exercise scene

Each exercise that needs an image has an `image_prompt_scene` in its source file. It describes only the start position (frame 0): body position, grip, equipment and where it sits. Do not repeat the style block there.

## Workflow

1. `python3 prompts.py --missing --batch 10 --tool midjourney`
2. Generate each image in the tool, check anatomy, hands and equipment, and pick the best.
3. `python3 process_image.py <downloaded file> <id> --tool midjourney`
4. `python3 validate.py`, then bump `content_version` and `updated` in `manifest.json` and commit.
