#!/usr/bin/env python3
"""Storyboard 技能共用工具。"""

from __future__ import annotations

import json
import mimetypes
import os
import re
import time
from pathlib import Path
from typing import Any

from google import genai
from PIL import Image


DEFAULT_IMAGE_MODEL = "models/gemini-3.1-flash-image-preview"
DEFAULT_IMAGE_FALLBACK_MODEL = "models/gemini-3-pro-image-preview"
DEFAULT_ANALYSIS_MODEL = "models/gemini-3-flash-preview"


def require_api_key() -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("ERROR: GEMINI_API_KEY environment variable not set")
    return api_key


def build_client() -> genai.Client:
    return genai.Client(api_key=require_api_key())


def ensure_dir(path: str | Path) -> Path:
    path = Path(path).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: Any) -> None:
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_text(path: str | Path, text: str) -> None:
    Path(path).write_text(text.rstrip() + "\n", encoding="utf-8")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "item"


def open_images(paths: list[str] | None) -> list[Image.Image]:
    images: list[Image.Image] = []
    for raw_path in paths or []:
        image = Image.open(Path(raw_path).expanduser())
        images.append(image.copy())
        image.close()
    return images


def normalize_text_list(items: list[Any] | None) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for item in items or []:
        if isinstance(item, str):
            normalized.append({"label": "text", "text": item, "style": ""})
            continue
        if isinstance(item, dict):
            normalized.append(
                {
                    "label": str(item.get("label", "text")),
                    "text": str(item.get("text", "")),
                    "style": str(item.get("style", "")),
                }
            )
    return [item for item in normalized if item["text"].strip()]


def extract_json_text(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    raise ValueError("No JSON object found in model response")


def parse_json_response(raw_text: str) -> dict[str, Any]:
    return json.loads(extract_json_text(raw_text))


def safe_response_text(response: Any) -> str:
    text = getattr(response, "text", None)
    if text:
        return text
    pieces: list[str] = []
    for candidate in getattr(response, "candidates", []) or []:
        parts = getattr(getattr(candidate, "content", None), "parts", []) or []
        for part in parts:
            if getattr(part, "text", None):
                pieces.append(part.text)
    return "\n".join(pieces).strip()


def save_inline_images(response: Any, output_path: str | Path) -> list[Path]:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    saved_files: list[Path] = []

    for candidate in getattr(response, "candidates", []) or []:
        parts = getattr(getattr(candidate, "content", None), "parts", []) or []
        for index, part in enumerate(parts):
            inline_data = getattr(part, "inline_data", None)
            if not inline_data or not getattr(inline_data, "data", None):
                continue

            raw_bytes = inline_data.data
            if isinstance(raw_bytes, str):
                import base64

                raw_bytes = base64.b64decode(raw_bytes)

            mime_type = getattr(inline_data, "mime_type", "image/png")
            extension = mimetypes.guess_extension(mime_type) or ".png"
            target = output_path
            if len(saved_files) > 0 or output_path.suffix.lower() != extension:
                target = output_path.with_suffix(extension)
            if index > 0:
                target = target.with_name(f"{target.stem}_{index}{target.suffix}")

            target.write_bytes(raw_bytes)
            saved_files.append(target)

    return saved_files


def wait_for_file_ready(client: genai.Client, uploaded_file: Any, timeout_s: int = 300) -> Any:
    deadline = time.time() + timeout_s
    name = getattr(uploaded_file, "name", None)
    if not name:
        return uploaded_file

    while time.time() < deadline:
        current = client.files.get(name=name)
        state = getattr(current, "state", None)
        state_name = getattr(state, "name", str(state or ""))
        if state_name in {"ACTIVE", "PROCESSING", "READY"}:
            if state_name != "PROCESSING":
                return current
        if state_name == "FAILED":
            raise RuntimeError(f"File processing failed: {getattr(current, 'error', None)}")
        time.sleep(5)

    raise TimeoutError(f"Timed out waiting for uploaded file to become ready: {name}")
