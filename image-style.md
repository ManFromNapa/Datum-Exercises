# Image style

Datum shows one image per exercise: frame 0, the start position. The target is an 850x567 landscape JPEG, 60 to 70 KB.
Existing images are photographs of one man in a gym with a red wall and a wood floor. New images keep that gym, clothing and camera, but the person varies in gender, ethnicity, age and build (see People below).

`prompts.py` reads the style block between the markers below and the `midjourney_params` line. Edit them here only.

<!-- style-block:start -->
Photorealistic photograph, 3:2 landscape. {person}, wearing a fitted dark athletic t-shirt, dark shorts and grey and white training shoes. Bright commercial gym with a red wall, a wood-grain floor and dark rubber mats, natural indoor light. Full body in frame. Camera at about chest height from a side or three-quarter angle. Correct anatomy and hands, realistic equipment. No text, no logos, no wall graphics, no watermark, and no other people anywhere in the frame, including the background.
<!-- style-block:end -->

midjourney_params: --ar 3:2 --style raw

## People

`prompts.py` replaces `{person}` in the style block with one line from the list below. An exercise always gets the same person (its position in the sorted list of all exercise ids, modulo the list length), so re-running a prompt never changes who is in it. Force a different one with `--person N` (1-based) or your own text with `--person-text "..."`. Add or edit lines freely; keep one adult per line, in good athletic shape, with no mention of clothing.

<!-- people:start -->
One fit adult man with short dark hair
One fit adult woman with dark hair in a ponytail
One fit adult Black man with short hair
One fit adult East Asian woman with shoulder-length black hair
One fit adult Latina woman with long brown hair
One fit adult South Asian man with short black hair and a trimmed beard
One fit adult white woman with a blonde bun
One fit adult Black woman with short natural curls
One fit adult Middle Eastern man with short dark hair
One fit adult East Asian man with short black hair
One fit adult Latino man with short brown hair
One fit adult South Asian woman with a long dark braid
One fit adult white man with short light brown hair
One fit middle-aged woman with short grey-streaked hair
One fit middle-aged man with short grey hair
<!-- people:end -->

## Per-exercise scene

Each exercise that needs an image has an `image_prompt_scene` in its source file. It describes only the start position (frame 0): body position, grip, equipment and where it sits. Do not repeat the style block there.

## Workflow

1. `python3 prompts.py --missing --batch 10 --tool midjourney`
2. Generate each image in the tool, check anatomy, hands and equipment, and pick the best.
3. `python3 process_image.py <downloaded file> <id> --tool midjourney`
4. `python3 validate.py`, then bump `content_version` and `updated` in `manifest.json` and commit.
