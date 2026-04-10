#!/usr/bin/env python3
"""调用 Gemini 理解视频并输出镜头与风格分析。"""

from __future__ import annotations

import argparse
from pathlib import Path

from google.genai import types

from common import (
    DEFAULT_ANALYSIS_MODEL,
    build_client,
    parse_json_response,
    safe_response_text,
    wait_for_file_ready,
    write_json,
    write_text,
)


VIDEO_ANALYSIS_PROMPT = """
你是一名资深导演助理与分镜策划，请严格输出 JSON，不要输出 JSON 之外的内容。

目标：
1. 理解视频的整体叙事、镜头结构、节奏、风格、光影、环境和特效。
2. 为后续使用 Seedance、分镜图生成和素材准备提供明确建议。

输出 JSON 结构：
{
  "overview": "整体概览",
  "narrative_purpose": "视频主要表达目标",
  "pace": "节奏描述",
  "visual_style": {
    "style_summary": "",
    "lighting": "",
    "environment": "",
    "camera_language": ["关键词"],
    "color_keywords": ["关键词"]
  },
  "shots": [
    {
      "index": 1,
      "time_range": "00:00-00:03",
      "description": "镜头内容",
      "camera": "镜头与机位",
      "transition": "转场方式",
      "effects": ["特效"],
      "seedance_materials": ["需要准备的素材"]
    }
  ],
  "effects_and_transitions": ["整体特效与转场总结"],
  "seedance_guidance": {
    "materials": ["建议准备的素材"],
    "transitions": ["建议的转场"],
    "prompt_notes": ["可直接复用的提示词要点"]
  }
}
""".strip()


def build_markdown(payload: dict) -> str:
    visual_style = payload.get("visual_style", {})
    shots = payload.get("shots", [])
    lines = [
        "# 视频理解报告",
        "",
        "## 整体概览",
        payload.get("overview", ""),
        "",
        "## 叙事目的",
        payload.get("narrative_purpose", ""),
        "",
        "## 节奏",
        payload.get("pace", ""),
        "",
        "## 视觉风格",
        f"- 风格总结：{visual_style.get('style_summary', '')}",
        f"- 光影：{visual_style.get('lighting', '')}",
        f"- 环境：{visual_style.get('environment', '')}",
        f"- 镜头语言：{', '.join(visual_style.get('camera_language', []))}",
        f"- 色彩关键词：{', '.join(visual_style.get('color_keywords', []))}",
        "",
        "## 分镜拆解",
    ]
    for shot in shots:
        lines.extend(
            [
                f"### 镜头 {shot.get('index', '')} | {shot.get('time_range', '')}",
                f"- 内容：{shot.get('description', '')}",
                f"- 镜头：{shot.get('camera', '')}",
                f"- 转场：{shot.get('transition', '')}",
                f"- 特效：{', '.join(shot.get('effects', []))}",
                f"- Seedance 素材：{', '.join(shot.get('seedance_materials', []))}",
                "",
            ]
        )
    guidance = payload.get("seedance_guidance", {})
    lines.extend(
        [
            "## 特效与转场总结",
            *(f"- {item}" for item in payload.get("effects_and_transitions", [])),
            "",
            "## Seedance 建议",
            *(f"- 素材：{item}" for item in guidance.get("materials", [])),
            *(f"- 转场：{item}" for item in guidance.get("transitions", [])),
            *(f"- Prompt 要点：{item}" for item in guidance.get("prompt_notes", [])),
        ]
    )
    return "\n".join(lines).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze video structure and style via Gemini")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--video", help="Local video file path")
    source.add_argument("--youtube-url", help="Public YouTube URL")
    parser.add_argument("--output-dir", required=True, help="Directory to save report")
    parser.add_argument("--model", default=DEFAULT_ANALYSIS_MODEL, help="Gemini multimodal model")
    args = parser.parse_args()

    client = build_client()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.video:
        uploaded = client.files.upload(file=Path(args.video).expanduser())
        video_input = wait_for_file_ready(client, uploaded)
    else:
        video_input = args.youtube_url

    response = client.models.generate_content(
        model=args.model,
        contents=[video_input, VIDEO_ANALYSIS_PROMPT],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )
    payload = parse_json_response(safe_response_text(response))
    write_json(output_dir / "video_analysis.json", payload)
    write_text(output_dir / "video_analysis.md", build_markdown(payload))

    print(f"Video report saved to: {output_dir}")


if __name__ == "__main__":
    main()
