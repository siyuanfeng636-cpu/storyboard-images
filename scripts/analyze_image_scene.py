#!/usr/bin/env python3
"""理解图片并输出素材包、场景提示词和结构化分析。"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Any

from google.genai import types
from PIL import Image

from common import (
    DEFAULT_ANALYSIS_MODEL,
    build_client,
    open_images,
    parse_json_response,
    safe_response_text,
    slugify,
    write_json,
    write_text,
)


ANALYSIS_PROMPT = """
你是一名分镜与动态设计前期分析师。请根据输入图片输出严格 JSON，不要输出 JSON 之外的任何文字。

目标：
1. 理解场景、主体、道具、背景、光影、材质和连续性约束。
2. 提取适合单独复用的素材项，并为每个素材给出归一化框选框 bbox。
3. 为后续保持场景一致性生成光影、环境和材质关键词。

输出 JSON 结构：
{
  "scene_summary": "一句话总结",
  "style_keywords": ["关键词"],
  "negative_keywords": ["关键词"],
  "continuity_notes": ["必须保持的一致性要求"],
  "lighting": {
    "time_of_day": "",
    "main_light": "",
    "fill_light": "",
    "color_temperature": "",
    "shadow_quality": "",
    "keywords": ["关键词"]
  },
  "environment": {
    "location": "",
    "weather": "",
    "atmosphere": "",
    "background_elements": ["关键词"],
    "keywords": ["关键词"]
  },
  "materials": ["关键词"],
  "background_rebuild_prompt": "用于重建背景空镜的详细 prompt",
  "assets": [
    {
      "name": "素材名",
      "type": "character|prop|text-region|background-region|fx",
      "description": "作用和识别说明",
      "animation_hint": "如何用于动态设计",
      "bbox": [left, top, right, bottom]
    }
  ]
}

约束：
- bbox 使用 0-1000 的归一化坐标。
- 只列出真正适合单独复用的素材。
- 如果画面内有文字区域，也单独作为 text-region。
""".strip()


def clamp(value: int, lower: int, upper: int) -> int:
    return max(lower, min(upper, value))


def denormalize_bbox(bbox: list[Any], width: int, height: int) -> tuple[int, int, int, int]:
    if len(bbox) != 4:
        raise ValueError("bbox must contain 4 values")
    left = clamp(int(float(bbox[0]) / 1000 * width), 0, width)
    top = clamp(int(float(bbox[1]) / 1000 * height), 0, height)
    right = clamp(int(float(bbox[2]) / 1000 * width), 0, width)
    bottom = clamp(int(float(bbox[3]) / 1000 * height), 0, height)
    if right <= left:
        right = min(width, left + 1)
    if bottom <= top:
        bottom = min(height, top + 1)
    return left, top, right, bottom


def build_scene_markdown(payload: dict[str, Any]) -> str:
    lighting = payload.get("lighting", {})
    environment = payload.get("environment", {})
    return f"""# 场景一致性包

## 场景摘要
{payload.get("scene_summary", "")}

## 风格关键词
{", ".join(payload.get("style_keywords", []))}

## 光影关键词
- 时间段：{lighting.get("time_of_day", "")}
- 主光源：{lighting.get("main_light", "")}
- 辅助光：{lighting.get("fill_light", "")}
- 色温：{lighting.get("color_temperature", "")}
- 阴影质感：{lighting.get("shadow_quality", "")}
- 补充关键词：{", ".join(lighting.get("keywords", []))}

## 环境关键词
- 地点：{environment.get("location", "")}
- 天气：{environment.get("weather", "")}
- 氛围：{environment.get("atmosphere", "")}
- 背景元素：{", ".join(environment.get("background_elements", []))}
- 环境关键词：{", ".join(environment.get("keywords", []))}

## 材质关键词
{", ".join(payload.get("materials", []))}

## 连续性约束
{chr(10).join(f"- {item}" for item in payload.get("continuity_notes", [])) or "- 无"}

## 负向约束
{chr(10).join(f"- {item}" for item in payload.get("negative_keywords", [])) or "- 无"}

## 背景重建 Prompt
```text
{payload.get("background_rebuild_prompt", "")}
```
"""


def build_asset_manifest(payload: dict[str, Any]) -> str:
    lines = ["# 素材清单", ""]
    for asset in payload.get("assets", []):
        bbox = asset.get("bbox", [])
        lines.append(f"## {asset.get('name', 'unnamed')}")
        lines.append(f"- 类型：{asset.get('type', '')}")
        lines.append(f"- 说明：{asset.get('description', '')}")
        lines.append(f"- 动效建议：{asset.get('animation_hint', '')}")
        lines.append(f"- 归一化框：{bbox}")
        lines.append("")
    return "\n".join(lines).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze image scene and export reusable assets")
    parser.add_argument("--image", action="append", required=True, help="Input image path, repeatable")
    parser.add_argument("--output-dir", required=True, help="Directory to save scene pack")
    parser.add_argument("--model", default=DEFAULT_ANALYSIS_MODEL, help="Gemini multimodal model")
    args = parser.parse_args()

    client = build_client()
    output_dir = Path(args.output_dir).expanduser().resolve()
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    pil_images = open_images(args.image)
    response = client.models.generate_content(
        model=args.model,
        contents=[ANALYSIS_PROMPT, *pil_images],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )
    payload = parse_json_response(safe_response_text(response))

    primary_image_path = Path(args.image[0]).expanduser().resolve()
    with Image.open(primary_image_path) as image:
        width, height = image.size
        for index, asset in enumerate(payload.get("assets", []), start=1):
            bbox = asset.get("bbox") or []
            try:
                left, top, right, bottom = denormalize_bbox(bbox, width, height)
            except Exception:
                continue
            crop = image.crop((left, top, right, bottom))
            stem = slugify(asset.get("name", f"asset-{index}"))
            crop.save(assets_dir / f"{index:02d}_{stem}.png")

    shutil.copy2(primary_image_path, assets_dir / "background_reference.png")
    write_json(output_dir / "scene_analysis.json", payload)
    write_text(output_dir / "scene_prompt.md", build_scene_markdown(payload))
    write_text(output_dir / "asset_manifest.md", build_asset_manifest(payload))

    print(f"Scene pack saved to: {output_dir}")
    print(f"Assets: {assets_dir}")


if __name__ == "__main__":
    main()
