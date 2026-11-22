#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["google-genai>=3.6.1"]
# ///
"""Generate and edit images with Gemini Nano Banana 2.1 via the Interactions API.

Examples:
  nano-banana "A cinematic travel poster of Kyoto in autumn" -a 2:3 -s 2K
  nano-banana "Make the lighting warmer. Do not change any other elements." --continue
  nano-banana "Put the product from image 1 on the table in image 2" -r product.png -r table.jpg
  nano-banana "Wallpaper of a resplendent quetzal" --search -a 16:9 -s 4K -t high

API key: GEMINI_API_KEY env var, else ~/.nano-banana/.env.
Outputs go to ./out/ (override with -d or NANO_BANANA_OUT_DIR). The last interaction ID
(for --continue) is kept in <out>/.nano_banana_last.json.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
from datetime import datetime
from pathlib import Path

DEFAULT_MODEL = "gemini-nano-banana-2.1"
MODEL_ALIASES = {
    "2.1": "gemini-nano-banana-2.1",
    "nb21": "gemini-nano-banana-2.1",
    "pro": "gemini-3-pro-image",
    "nb2": "gemini-3.1-flash-image",
    "lite": "gemini-3.1-flash-lite-image",
}
# USD per 1M tokens: (input, image output). From Google's Gemini API price list, Nov 2026.
# Thinking/text output tokens are billed too but are not included in the estimate.
PRICES = {
    "gemini-nano-banana-2.1": (1.50, 30.0),
    "gemini-3.1-flash-image": (0.50, 60.0),
    "gemini-3.1-flash-lite-image": (0.25, 30.0),
    "gemini-3-pro-image": (2.00, 120.0),
}
# Sizes each model accepts (others return HTTP 400).
SUPPORTED_SIZES = {
    "gemini-nano-banana-2.1": {"1K", "2K", "4K"},
    "gemini-3.1-flash-image": {"512", "1K", "2K", "4K"},
    "gemini-3.1-flash-lite-image": {"1K"},
    "gemini-3-pro-image": {"1K", "2K", "4K"},
}
ASPECTS = ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9",
           "1:4", "4:1", "1:8", "8:1"]
DEFAULT_OUT_DIR = os.environ.get("NANO_BANANA_OUT_DIR", "out")


def load_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    env_file = Path.home() / ".nano-banana" / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip("\"'")
    sys.exit("No API key. Set GEMINI_API_KEY or write GEMINI_API_KEY=... to ~/.nano-banana/.env\n"
             "Get one at https://aistudio.google.com/apikey")


def image_part(path: str) -> dict:
    p = Path(path)
    if not p.is_file():
        sys.exit(f"Reference image not found: {path}")
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    return {"type": "image", "mime_type": mime,
            "data": base64.b64encode(p.read_bytes()).decode()}


def detect_ext(data: bytes) -> str:
    if data.startswith(b"\x89PNG"):
        return ".png"
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return ".bin"


def image_tokens(usage) -> int:
    for m in (getattr(usage, "output_tokens_by_modality", None) or []):
        if str(getattr(m, "modality", "")).lower().endswith("image"):
            return m.tokens or 0
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prompt", help="What to generate, or the edit to make")
    ap.add_argument("-m", "--model", default=DEFAULT_MODEL,
                    help=f"Model ID or alias {list(MODEL_ALIASES)} (default: {DEFAULT_MODEL})")
    ap.add_argument("-a", "--aspect", default=None, choices=ASPECTS,
                    help="Aspect ratio (default: match input image, else 1:1)")
    ap.add_argument("-s", "--size", default="1K", choices=["512", "1K", "2K", "4K"],
                    help="Output resolution (default: 1K)")
    ap.add_argument("-t", "--thinking", default=None, choices=["minimal", "medium", "high"],
                    help="Thinking level (2.1 default: medium). Use high for complex scenes")
    ap.add_argument("-r", "--ref", action="append", default=[],
                    help="Reference image (repeatable, up to 14). Refer to them as image 1, image 2...")
    ap.add_argument("-c", "--continue", dest="cont", action="store_true",
                    help="Continue editing the last image from this script (multi-turn)")
    ap.add_argument("--prev", help="Continue from a specific interaction ID")
    ap.add_argument("--search", action="store_true", help="Ground with Google web + image search")
    ap.add_argument("-n", "--count", type=int, default=1, help="Number of independent variations")
    ap.add_argument("-o", "--output", help="Output file name without extension (default: timestamp)")
    ap.add_argument("-d", "--dir", default=DEFAULT_OUT_DIR,
                    help="Output directory (default: $NANO_BANANA_OUT_DIR or ./out)")
    ap.add_argument("--image-only", action="store_true",
                    help="Append 'output only the final image' (fixes NO_IMAGE on wordy prompts)")
    ap.add_argument("--dry-run", action="store_true", help="Print the request and exit")
    args = ap.parse_args()

    model = MODEL_ALIASES.get(args.model.lower(), args.model)
    if model in SUPPORTED_SIZES and args.size not in SUPPORTED_SIZES[model]:
        sys.exit(f"{model} does not support size {args.size}. "
                 f"Supported: {sorted(SUPPORTED_SIZES[model])}")

    out_dir = Path(args.dir).expanduser()
    state_file = out_dir / ".nano_banana_last.json"

    prev_id = args.prev
    if args.cont and not prev_id:
        if not state_file.exists():
            sys.exit(f"Nothing to continue: no previous run recorded in {out_dir}/.")
        prev_id = json.loads(state_file.read_text())["interaction_id"]

    prompt = args.prompt
    if args.image_only:
        prompt += "\n\nImportant: output only one final image. Do not output any written analysis."
    content = [image_part(r) for r in args.ref] + [{"type": "text", "text": prompt}]

    response_format = {"type": "image", "image_size": args.size}
    if args.aspect:
        response_format["aspect_ratio"] = args.aspect
    request = {"model": model, "input": content, "response_format": response_format}
    if args.thinking:
        request["generation_config"] = {"thinking_level": args.thinking}
    if prev_id:
        request["previous_interaction_id"] = prev_id
    if args.search:
        request["tools"] = [{"type": "google_search", "search_types": ["web_search", "image_search"]}]

    if args.dry_run:
        shown = json.loads(json.dumps(request))
        for part in shown["input"]:
            if part.get("type") == "image":
                part["data"] = f"<{len(part['data'])} base64 chars>"
        print(json.dumps(shown, indent=2))
        return

    from google import genai  # imported late so --help / --dry-run work without a key

    client = genai.Client(api_key=load_api_key())
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = args.output or f"nb-{datetime.now():%Y%m%d-%H%M%S}"
    in_rate, img_rate = PRICES.get(model, (0.0, 0.0))

    for i in range(args.count):
        start = time.time()
        try:
            it = client.interactions.create(**request)
        except Exception as e:  # surface API errors (400 bad size/aspect, auth, quota) cleanly
            sys.exit(f"API error: {e}")
        elapsed = time.time() - start

        if it.output_text:
            print(f"[model text] {it.output_text.strip()}")
        if not it.output_image or not it.output_image.data:
            print(f"No image returned (status: {getattr(it, 'status', '?')}). "
                  "Make the image request explicit, try --image-only, or rephrase "
                  "if it hit a safety filter.", file=sys.stderr)
            sys.exit(2)

        raw = it.output_image.data
        data = base64.b64decode(raw) if isinstance(raw, str) else bytes(raw)
        name = stem if args.count == 1 else f"{stem}-{i + 1}"
        path = out_dir / f"{name}{detect_ext(data)}"
        path.write_bytes(data)

        u = it.usage
        in_tok = (u.total_input_tokens or 0) if u else 0
        img_tok = image_tokens(u) if u else 0
        thought_tok = (u.total_thought_tokens or 0) if u else 0
        cost = in_tok * in_rate / 1e6 + img_tok * img_rate / 1e6

        print(f"saved {path}  ({elapsed:.1f}s, ~${cost:.4f} + {thought_tok} thinking tokens)")
        print(f"interaction id: {it.id}   (edit it next with --continue)")

        state_file.write_text(json.dumps({"interaction_id": it.id, "file": str(path)}))


if __name__ == "__main__":
    main()
