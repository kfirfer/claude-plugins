---
name: nano-banana
description: Generate and edit images with Google Gemini Nano Banana 2.1 (gemini-nano-banana-2.1) through the Interactions API, using the bundled Python script. Use whenever the user asks to generate, create, draw, design or edit an image, photo, illustration, poster, ad, logo, icon, mascot, wallpaper, mockup or other visual, or mentions Nano Banana, Nano Banana 2.1 or Gemini image generation. Supports reference images, multi-turn edits, 1K/2K/4K, 14 aspect ratios, thinking levels, Google search grounding and variations.
---

# Nano Banana 2.1 image generation

Run the bundled script with uv. It declares its own dependencies, so no install step is needed:

```bash
uv run --quiet --script ${CLAUDE_SKILL_DIR}/scripts/nano-banana.py "prompt" [-a 16:9] [-s 1K|2K|4K] \
  [-t minimal|medium|high] [-r ref.png ...] [-c | --prev ID] [--search] [-n 3] [-o name] [-d dir] \
  [--image-only] [--dry-run]
```

While the plugin is enabled, the same script is also on PATH as `nano-banana "prompt" ...`.

**Requirements:**
- `uv` must be installed (`brew install uv` or https://docs.astral.sh/uv/).
- The API key comes from `GEMINI_API_KEY` in the environment, or else from `~/.nano-banana/.env`. If neither is set, tell the user to create a key at https://aistudio.google.com/apikey (billing must be enabled) and set it themselves. Never print the key or ask for it in the chat.

## Flags

| Flag | Meaning |
|---|---|
| `-a` | Aspect ratio: 1:1 2:3 3:2 3:4 4:3 4:5 5:4 9:16 16:9 21:9 1:4 4:1 1:8 8:1. Without it, the output matches the input image, or is 1:1 if there is none. |
| `-s` | `1K` (default), `2K`, `4K`. 2.1 rejects `512`; the script blocks it before calling the API. |
| `-t` | Thinking level. The 2.1 default is `medium`. Use `minimal` for quick drafts and `high` for complex scenes, text, or several references. |
| `-r` | Reference image, repeatable, up to 14 (2.1: ≤10 objects and ≤4 characters). Refer to them in the prompt as "image 1", "image 2", in the order given. |
| `-c` / `--prev ID` | Edit the last image (or a given interaction ID) without re-uploading it |
| `--search` | Google web and image search grounding, for real landmarks, products and current events |
| `-n` | Number of independent variations, saved with `-1`, `-2`, ... suffixes |
| `-o` / `-d` | Output name (no extension) and output folder. The folder defaults to `$NANO_BANANA_OUT_DIR` or `./out`. |
| `--image-only` | Adds "output only one final image". Use it when a prompt returns no image. |
| `-m` | Model: `pro` (gemini-3-pro-image: dense text, up to 3 style references), `nb2`, `lite`, or any model ID |

Each run prints the saved path and an estimated cost; nothing else is logged. The cost estimate does not include thinking tokens.

## Workflow
1. **Write the prompt** using the guide below. Turn the user's request into a descriptive paragraph rather than passing on a few keywords.
2. **Pick the settings** that fit the purpose: aspect ratio for where the image will be used, `1K` while drafting, `2K` or `4K` only for finals or when the user asks.
3. **Run the script**, then **look at the result with the Read tool** before reporting. Check that it matches the request, that any text is spelled correctly, and that nothing unrequested was added.
4. **Show the user** the file path and a one-line description of the image.
5. **For changes, use `-c`**, making one change per turn and ending with "Do not change any other elements of the image." Don't regenerate from scratch.
6. **Mention cost** when it's above trivial: `-n` above 2, any 4K output, or loops.

Approximate cost on 2.1: 1K $0.034 · 2K $0.050 · 4K $0.113 per image. Thinking and reference images add a little. Pro costs $0.134 at 1K and 2K, and $0.24 at 4K.

## Prompt guide
- **Formula:** Subject + Action + Location/context + Composition + Style. Add lighting, colour palette, mood, and what the image is for.
- **Use concrete words instead of praise:**
  - "golden-hour side-backlight" instead of "beautiful lighting"
  - "ornate elven plate armor etched with silver leaf" instead of "fantasy armor"
- **Photorealism:** say "photograph" and name the lens and depth of field ("85mm f/1.8, shallow depth of field"). Describe the light's source, direction, quality and colour temperature. Ask for natural detail ("visible pores", "natural color saturation") and avoid over-smoothed skin.
- **Illustration:** name the medium first ("flat vector icon, bold outlines", "watercolor with soft washes and paper texture").
- **Describe what you want rather than what you don't:** "an empty, deserted street" instead of "no cars". Short "No X" constraints at the end are fine for technical defects and stray text.
- **Text:** put the exact words in quotes, describe the font ("bold sans-serif") and say where it goes. Add "No other text." because the model tends to add taglines. For long or multi-line text, use `-m pro`.
- **Complex scenes:** describe them in order: "First, the background... Then... Finally..."
- **References:** give each image a role: "the product from image 1 on the table from image 2, matching the lighting of image 3." For a consistent character, send the original reference every time rather than chaining from the last output.
- **Edits:** state exactly what changes and what stays the same.

## Troubleshooting
- **No image returned:** start the prompt with "Generate an image of..." and add `--image-only`. Remove sentences that ask for written analysis.
- **Safety block:** change the subject or how it's depicted; retrying unchanged won't help.
- **400 errors:** the size or aspect ratio isn't supported by that model (Pro rejects 1:8 and 8:1; Lite is 1K only).
- **`--dry-run`** prints the request JSON without calling the API.
