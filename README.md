# kfirfer's Claude Code plugins

A [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugins/overview).

## Install

```bash
claude plugin marketplace add kfirfer/claude-plugins
claude plugin install nano-banana-studio@kfirfer
```

Or inside a Claude Code session: `/plugin marketplace add kfirfer/claude-plugins`, then `/plugin install nano-banana-studio@kfirfer`.

Updates: `claude plugin update nano-banana-studio@kfirfer`, or turn on auto-update for the `kfirfer` marketplace in `/plugin` → Marketplaces.

## Plugins

| Plugin | What it does |
|---|---|
| [nano-banana-studio](plugins/nano-banana-studio) | Generate and edit images with Google Gemini Nano Banana 2.1 |

## Nano Banana Studio

Ask Claude for any image ("make a 16:9 hero image of…", "edit this photo so…") and the `nano-banana` skill writes a detailed prompt, calls Gemini Nano Banana 2.1 through the Interactions API, checks the result and refines it over several turns.

### Requirements
- [uv](https://docs.astral.sh/uv/) (`brew install uv`). The script declares its own Python dependencies, so there is nothing else to install.
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey). Image generation needs billing enabled; there is no free API tier.

```bash
# either
export GEMINI_API_KEY=your_key            # e.g. in ~/.zshrc
# or
mkdir -p ~/.nano-banana && echo "GEMINI_API_KEY=your_key" > ~/.nano-banana/.env && chmod 600 ~/.nano-banana/.env
```

### Features
- Nano Banana 2.1 by default. `-m pro`, `nb2`, `lite` or any model ID switches model.
- 1K / 2K / 4K output and 14 aspect ratios, including 1:4, 4:1, 1:8 and 8:1.
- Thinking level control (`minimal`, `medium`, `high`).
- Up to 14 reference images, for style transfer, product placement and consistent characters.
- Multi-turn editing (`--continue`) without re-uploading the image.
- Google web and image search grounding (`--search`).
- Several variations at once (`-n`).
- A per-run JSONL log with token counts and estimated cost.

### Use it directly
While the plugin is enabled, Claude can also run `nano-banana` as a shell command:

```bash
nano-banana "A cinematic travel poster of Kyoto in autumn, torii gate at golden hour" -a 2:3 -s 2K
nano-banana "Make the lighting warmer. Do not change any other elements." --continue
nano-banana "The product from image 1 on the marble table from image 2" -r product.png -r table.jpg
nano-banana --help
```

Images are saved to `./out/`. Change this with `-d <dir>` or `NANO_BANANA_OUT_DIR`, and consider adding `out/` to your `.gitignore`.

### Approximate cost per image (Nano Banana 2.1)
| 1K | 2K | 4K |
|---|---|---|
| $0.034 | $0.050 | $0.113 |

Thinking tokens and reference images add a little. Check Google's [pricing page](https://ai.google.dev/gemini-api/docs/pricing) for current rates.

## License
MIT
