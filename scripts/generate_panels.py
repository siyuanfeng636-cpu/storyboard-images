#!/usr/bin/env python3
"""根据分镜配置批量生成任意数量的高清镜头图。"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any

from google.genai import types

from common import (
    DEFAULT_IMAGE_MODEL,
    build_client,
    normalize_text_list,
    open_images,
    read_json,
    save_inline_images,
    slugify,
    write_text,
)


QUALITY_HINTS = {
    "1K": "high-resolution, crisp and clean.",
    "2K": "very high-resolution, crisp materials and typography.",
    "4K": "ultra-detailed, production-ready, crystal-clear typography and materials.",
}


def load_shots(config: dict[str, Any]) -> list[dict[str, Any]]:
    if config.get("shots"):
        return list(config["shots"])
    if config.get("panels"):
        return list(config["panels"])
    raise ValueError("Config must contain either 'shots' or 'panels'")


def build_prompt(config: dict[str, Any], shot: dict[str, Any], image_size: str) -> str:
    if shot.get("scene") or shot.get("visual_elements") or shot.get("required_text"):
        required_text = normalize_text_list(shot.get("required_text"))
        visual_elements = shot.get("visual_elements") or []
        lines = [
            str(config.get("global_style") or config.get("style") or "").strip(),
            "",
            "Scene:",
            str(shot.get("scene", "")).strip(),
            "",
            "Shot intent:",
            str(shot.get("prompt", "")).strip(),
            "",
            "Required visual elements:",
        ]
        if visual_elements:
            lines.extend(f"- {item}" for item in visual_elements)
        else:
            lines.append("- Keep the core subject and environment consistent.")

        lines.extend(["", "Required text (render exactly these characters, nothing else):"])
        if required_text:
            for item in required_text:
                suffix = f" | {item['style']}" if item["style"] else ""
                lines.append(f"- {item['label']}: {item['text']}{suffix}")
        else:
            lines.append("- No visible text.")

        lines.extend(
            [
                "",
                "Image quality requirements:",
                f"- {QUALITY_HINTS[image_size]}",
                "- Keep text legible and free of hallucinated extra characters.",
                "- Keep prop edges, materials, and lighting transitions clear.",
                "",
                "Forbidden:",
                f"- {config.get('global_negative', 'No extra text, watermark, unrelated props, or extra characters.')}",
            ]
        )
        return "\n".join(line for line in lines if line is not None).strip()

    return str(shot.get("prompt", "")).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate storyboard shots via Gemini image model")
    parser.add_argument("--config", required=True, help="Path to storyboard JSON config")
    parser.add_argument("--output-dir", required=True, help="Directory to save generated images")
    parser.add_argument("--model", default=DEFAULT_IMAGE_MODEL, help="Gemini image model")
    parser.add_argument("--aspect-ratio", default=None, help="Fallback aspect ratio")
    parser.add_argument(
        "--image-size",
        default="4K",
        choices=["1K", "2K", "4K"],
        help="Quality hint to inject into the prompt",
    )
    parser.add_argument("--retry-failed", action="store_true", help="Only regenerate missing files")
    parser.add_argument("--save-prompts", action="store_true", help="Save final prompt markdown for each shot")
    parser.add_argument("--sleep-seconds", type=float, default=2.0, help="Pause between requests")
    args = parser.parse_args()

    client = build_client()
    config = read_json(args.config)
    shots = load_shots(config)
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    prompts_dir = output_dir / "prompts"
    if args.save_prompts:
        prompts_dir.mkdir(parents=True, exist_ok=True)

    global_refs = list(config.get("global_reference_images") or [])
    total = len(shots)
    success = 0
    failed: list[str] = []

    print("=" * 60)
    print(f"Storyboard generation")
    print(f"Model: {args.model}")
    print(f"Shots: {total}")
    print(f"Output: {output_dir}")
    print("=" * 60)

    for index, shot in enumerate(shots, start=1):
        shot_id = str(shot.get("id", index))
        filename = shot.get("filename") or f"{slugify(shot_id)}.png"
        output_path = output_dir / filename

        if args.retry_failed and output_path.exists():
            print(f"[{shot_id}] skip existing: {output_path.name}")
            success += 1
            continue

        prompt = build_prompt(config, shot, args.image_size)
        ref_images = open_images(global_refs + list(shot.get("reference_images") or []))
        aspect_ratio = shot.get("aspect_ratio") or config.get("default_aspect_ratio") or args.aspect_ratio or "16:9"

        print(f"[{shot_id}] {output_path.name}")
        try:
            response = client.models.generate_content(
                model=args.model,
                contents=[prompt, *ref_images],
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
                    temperature=0.6,
                ),
            )
            saved_files = save_inline_images(response, output_path)
            if not saved_files:
                raise RuntimeError("No image returned by model")

            if args.save_prompts:
                prompt_path = prompts_dir / f"{Path(filename).stem}.md"
                write_text(prompt_path, f"# {shot_id}\n\n```text\n{prompt}\n```")

            print(f"  saved: {saved_files[0].name}")
            success += 1
        except Exception as exc:
            failed.append(shot_id)
            print(f"  failed: {exc}")

        if index < total and args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)

    print("=" * 60)
    print(f"Done: {success}/{total}")
    if failed:
        print(f"Failed shots: {failed}")
    print(f"Files in: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
