#!/usr/bin/env python3
"""
Generate 4K storyboard panel images via Gemini REST API.

Usage:
    python3 generate_panels.py --config panels.json --output-dir ./output [--aspect-ratio 16:9] [--image-size 4K]

The config JSON format:
{
    "style": "Global style prefix for all panels...",
    "panels": [
        {"id": 1, "filename": "panel_01.png", "prompt": "..."},
        ...
    ]
}

Requires env var: GEMINI_API_KEY
"""

import os
import sys
import json
import time
import base64
import argparse

import requests
from PIL import Image
import io


API_MODEL = "gemini-3-pro-image-preview"


def get_api_url(api_key: str) -> str:
    return (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{API_MODEL}:generateContent?key={api_key}"
    )


def generate_panel(
    panel: dict,
    api_url: str,
    output_dir: str,
    aspect_ratio: str,
    image_size: str,
    max_retries: int = 3,
) -> bool:
    """Generate a single panel image. Returns True on success."""
    print(f"\n{'='*60}")
    print(f"[Panel {panel['id']}] {panel['filename']}")
    print(f"{'='*60}")

    payload = {
        "contents": [{"parts": [{"text": panel["prompt"]}]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {
                "aspectRatio": aspect_ratio,
                "imageSize": image_size,
            },
        },
    }

    for attempt in range(1, max_retries + 1):
        try:
            print(f"  Attempt {attempt}/{max_retries}...", flush=True)
            resp = requests.post(
                api_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=180,
            )

            if resp.status_code != 200:
                print(f"  x HTTP {resp.status_code}: {resp.text[:300]}")
                if attempt < max_retries:
                    time.sleep(attempt * 5)
                continue

            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                print("  x No candidates in response")
                continue

            parts = candidates[0].get("content", {}).get("parts", [])

            for part in parts:
                inline_data = part.get("inlineData")
                if inline_data and inline_data.get("data"):
                    img_bytes = base64.b64decode(inline_data["data"])
                    output_path = os.path.join(output_dir, panel["filename"])
                    pil_img = Image.open(io.BytesIO(img_bytes))
                    pil_img.save(output_path)
                    w, h = pil_img.size
                    print(f"  + Saved: {output_path}")
                    print(f"    Resolution: {w}x{h}")
                    return True

            print("  x No image data in response")

        except requests.exceptions.Timeout:
            print(f"  x Timeout (attempt {attempt})")
        except Exception as e:
            print(f"  x Error: {e}")

        if attempt < max_retries:
            wait = attempt * 8
            print(f"    Retrying in {wait}s...")
            time.sleep(wait)

    return False


def main():
    parser = argparse.ArgumentParser(description="Generate storyboard panels via Gemini API")
    parser.add_argument("--config", required=True, help="Path to panels JSON config file")
    parser.add_argument("--output-dir", required=True, help="Directory to save generated images")
    parser.add_argument("--aspect-ratio", default="16:9", help="Image aspect ratio (default: 16:9)")
    parser.add_argument("--image-size", default="4K", choices=["1K", "2K", "4K"], help="Image resolution (default: 4K)")
    parser.add_argument("--retry-failed", action="store_true", help="Only retry panels that don't exist in output-dir")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit("ERROR: GEMINI_API_KEY environment variable not set")

    api_url = get_api_url(api_key)
    os.makedirs(args.output_dir, exist_ok=True)

    with open(args.config, "r", encoding="utf-8") as f:
        config = json.load(f)

    panels = config["panels"]

    # Filter to only missing panels if --retry-failed
    if args.retry_failed:
        panels = [p for p in panels if not os.path.exists(os.path.join(args.output_dir, p["filename"]))]
        if not panels:
            print("All panels already exist. Nothing to do.")
            return

    total = len(panels)
    print("=" * 60)
    print(f"  Storyboard Generation — {args.image_size} ({args.aspect_ratio})")
    print(f"  Model: {API_MODEL}")
    print(f"  Panels: {total}")
    print(f"  Output: {args.output_dir}")
    print("=" * 60)

    success, failed = 0, []
    for panel in panels:
        if generate_panel(panel, api_url, args.output_dir, args.aspect_ratio, args.image_size):
            success += 1
        else:
            failed.append(panel["id"])
        time.sleep(3)

    print(f"\n{'='*60}")
    print(f"  DONE  + {success}/{total}   x {len(failed)}")
    if failed:
        print(f"  Failed panels: {failed}")
        print(f"  Re-run with --retry-failed to regenerate them.")
    print(f"  Files in: {args.output_dir}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
