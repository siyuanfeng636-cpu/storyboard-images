---
name: storyboard-studio
description: 分镜生成、参考图驱动出图、场景拆解和视频理解技能。用于根据分镜脚本、提示词、现有分镜图或视频素材，批量生成任意数量的高清分镜图；调用 Gemini API 理解图片并输出素材裁切、光影与环境提示词、一致性场景包；以及理解视频的镜头结构、风格、特效和转场并产出 Markdown 分析。触发词：分镜、storyboard、storyboard studio、参考图出图、拆素材、场景一致性、Seedance 素材、视频理解、镜头分析。
---

# Storyboard Studio

使用 Gemini 完成四类工作：

1. 根据分镜脚本、提示词和参考图生成任意数量的高清分镜图。
2. 理解单张或多张图片，输出素材清单、裁切素材、背景与光影提示词。
3. 为同一场景沉淀可复用的“场景一致性包”。
4. 理解视频的拍摄结构、镜头语言、风格、特效与转场，并输出供 Seedance 等后续工具使用的分析文档。

## 先决条件

- 设置 `GEMINI_API_KEY`。
- Python 依赖：`google-genai`, `Pillow`。
- 模型默认策略：
  - 图片生成首选 `models/gemini-3.1-flash-image-preview`
  - 图片生成复杂场景、高清终稿或主模型失败时切到 `models/gemini-3-pro-image-preview`
  - 图片理解默认 `models/gemini-3-flash-preview`
  - 视频理解默认 `models/gemini-3-flash-preview`
- 清晰度默认策略：首轮出图默认 `1K` 预览，确认构图、文字和素材无误后，再升到 `4K` 生成终稿。

## 任务路由

- 需要“根据脚本或提示词批量出图”时，使用 `scripts/generate_panels.py`。
- 需要“理解图片、拆出素材、生成场景提示词包”时，使用 `scripts/analyze_image_scene.py`。
- 需要“理解视频并输出镜头/风格/特效分析”时，使用 `scripts/analyze_video_story.py`。
- 构造配置文件前，先读 [references/config_schema.md](references/config_schema.md)。
- 编写分镜 prompt 时，先读 [references/prompt_template.md](references/prompt_template.md)。
- 需要确认模型、输入限制、文件上传方式时，读 [references/gemini_workflows.md](references/gemini_workflows.md)。

## 工作流程

### 1. 生成分镜图

适用场景：
- 用户给出分镜脚本，要批量生成多个镜头图。
- 用户给出已有分镜图或风格图，要保持镜头风格和场景一致性。
- 用户要求输出清晰文字、清晰材质和高清构图。

执行要求：
- 不再默认限制为 3×3 或 9 宫格。镜头数量由 `shots` 列表决定。
- 每个镜头都允许单独挂载 `reference_images`，并可叠加全局 `global_reference_images`。
- 对于画面内文字，必须显式写入 `required_text`，并加上“只渲染这些文字”的限制。
- 输出时同时保存生成图片和对应的最终 prompt `.md`，便于复用和追溯。
- 默认先跑 `1K`，让用户确认风格、构图、文字和素材清晰度；确认后再改成 `4K`。
- 默认先尝试 `models/gemini-3.1-flash-image-preview`；如果失败、质量不足，或用户明确要求更高质量，则改用 `models/gemini-3-pro-image-preview`。

推荐命令：

```bash
python3 scripts/generate_panels.py \
  --config /path/to/storyboard.json \
  --output-dir ~/storyboard_output/project_name \
  --aspect-ratio 16:9 \
  --image-size 1K
```

### 2. 拆解图片素材并沉淀场景包

适用场景：
- 用户给出单张场景图，希望拆出人物、道具、文字区、背景参考。
- 用户需要把光影、环境、材质写成稳定 prompt，方便后续保持一致。
- 用户需要为动态设计准备可复用素材和描述文档。

执行要求：
- 让 Gemini 先输出结构化分析，包括场景摘要、灯光、环境、连续性约束和素材框选。
- 本地根据模型给出的框选结果裁切素材，输出到 `assets/`。
- 同时生成 `scene_prompt.md`、`asset_manifest.md`、`scene_analysis.json`。
- 如果背景无法无损抠出，保留 `background_reference.png` 和“背景重建 prompt”，不要伪装成精确分层。

推荐命令：

```bash
python3 scripts/analyze_image_scene.py \
  --image /path/to/scene.png \
  --output-dir ~/storyboard_output/project_name/scene_pack
```

### 3. 理解视频并输出镜头分析

适用场景：
- 用户给出视频，希望拆解拍摄结构、镜头节奏、风格、特效与转场。
- 用户需要把视频分析整理成 `.md` 文档，给 Seedance 或后续生成链路复用。

执行要求：
- 本地视频优先走 Gemini Files API；公开视频可直接提供 YouTube URL。
- 输出 Markdown，至少包含：整体概览、镜头节奏、镜头清单、视觉风格、光影/环境、特效/转场、可复用 prompt、Seedance 素材建议。
- 如果视频较长，要求模型按时间段分段总结并标出关键时间点。

推荐命令：

```bash
python3 scripts/analyze_video_story.py \
  --video /path/to/video.mp4 \
  --output-dir ~/storyboard_output/project_name/video_report
```

## 输出目录约定

默认输出到：

```text
~/storyboard_output/{YYYY-MM-DD}_{项目关键词}/
```

推荐结构：

```text
project/
├── storyboard.json
├── shots/
├── prompts/
├── scene_pack/
│   ├── assets/
│   ├── scene_prompt.md
│   ├── asset_manifest.md
│   └── scene_analysis.json
└── video_report/
    ├── video_analysis.md
    └── video_analysis.json
```

## 关键约束

- 不要把“背景已无损分离”说成既成事实；当前流程是“理解 + 框选裁切 + 背景参考/重建提示词”。
- 不要默认任何固定宫格数量。只围绕用户实际镜头数构建 `shots`。
- 不要省略输出文件说明。每次执行后都要告诉用户生成数量、失败项和输出目录。
- 如果用户给的是模糊需求，先把镜头表或场景包结构整理成 JSON，再执行脚本。
- 对图片生成，默认遵循“先 1K 预览，确认后再 4K”的节奏，不直接上 4K 终稿。
