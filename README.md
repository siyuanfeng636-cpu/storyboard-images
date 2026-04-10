# Storyboard Studio

`Storyboard Studio` 是一个面向分镜、场景一致性和视频拆解的 Gemini 工作流技能。它解决的不是单一的“9 宫格出图”，而是一整套内容生产前期流程：

- 根据分镜脚本、提示词和参考图批量生成任意数量的高清分镜图
- 理解单张或多张图片，拆出可复用素材并沉淀场景一致性提示词
- 理解视频的镜头结构、风格、特效和转场，输出可复用的分析文档

适合这类任务：

- 给 Seedance、分镜设计、动态包装、视频生成链路准备高质量前置素材
- 从现有参考图中抽取人物、道具、背景和光影规则，保证场景一致性
- 从已有视频中提炼镜头语言、转场和特效，为复刻或二次创作提供依据

## 能力概览

### 1. 任意数量分镜图生成

使用 [`scripts/generate_panels.py`](./scripts/generate_panels.py)：

- 支持任意数量 `shots`
- 支持全局参考图和单镜头参考图
- 支持必须清晰渲染的文字约束
- 支持把最终 prompt 另存为 `.md`

典型输入：

- 分镜脚本
- 镜头列表
- 风格提示词
- 角色定妆图、色板图、已有分镜图

典型输出：

- `shots/*.png`
- `prompts/*.md`

### 2. 图片理解与素材拆解

使用 [`scripts/analyze_image_scene.py`](./scripts/analyze_image_scene.py)：

- 调用 Gemini 理解场景、主体、道具、背景和光影
- 输出结构化 JSON
- 根据模型返回的框选结果裁切出素材图
- 生成场景一致性提示词和素材清单

典型输出：

- `scene_analysis.json`
- `scene_prompt.md`
- `asset_manifest.md`
- `assets/*.png`

### 3. 视频理解与镜头分析

使用 [`scripts/analyze_video_story.py`](./scripts/analyze_video_story.py)：

- 支持本地视频文件
- 支持公开视频 YouTube URL
- 输出镜头拆解、风格总结、特效/转场建议和 Seedance 素材建议

典型输出：

- `video_analysis.json`
- `video_analysis.md`

## 目录结构

```text
storyboard-images/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── config_schema.md
│   ├── gemini_workflows.md
│   └── prompt_template.md
└── scripts/
    ├── analyze_image_scene.py
    ├── analyze_video_story.py
    ├── common.py
    └── generate_panels.py
```

## 环境要求

- Python 3.9+
- 已安装 `google-genai`
- 已安装 `Pillow`
- 已设置环境变量 `GEMINI_API_KEY`

## 默认模型策略

- 视频理解：`models/gemini-3-flash-preview`
- 图片理解：`models/gemini-3-flash-preview`
- 图像生成优先：`models/gemini-3.1-flash-image-preview`
- 图像生成备选/高质量终稿：`models/gemini-3-pro-image-preview`

默认清晰度策略：

- 首轮生成默认 `1K`
- 用户确认构图、文字和素材细节后，再生成 `4K`

说明：

- 我已按你要求把技能默认值改成上面的模型选择。
- 截至 2026-04-10，我能从 Google 官方资料对齐到 `gemini-3-flash-preview` 和 `gemini-3-pro-image-preview` 的命名；`gemini-3.1-flash-image-preview` 我没有检索到明确的公开模型页，因此脚本保留了 `--model` 与 `--fallback-model` 覆盖能力，便于你按实际可用账号/配额调整。

示例：

```bash
export GEMINI_API_KEY="your_api_key"
python3 -m pip install google-genai Pillow
```

## 本地安装为 Codex Skill

如果仓库在本地路径 `/Users/fengsiyuan/storyboard-images`，可以这样挂到 Codex skills 目录：

```bash
ln -sfn /Users/fengsiyuan/storyboard-images /Users/fengsiyuan/.codex/skills/storyboard-studio
```

之后即可通过 `$storyboard-studio` 调用。

## 使用方法

### 1. 批量生成分镜图

先准备配置文件，推荐结构见 [`references/config_schema.md`](./references/config_schema.md)。

示例：

```json
{
  "project_name": "city-night-launch",
  "global_style": "电影感赛博都市，潮湿路面，霓虹反射，材质清晰。",
  "global_negative": "不要额外文字，不要水印，不要多余人物，不要错误手指。",
  "global_reference_images": [
    "./refs/world_view.png",
    "./refs/color_script.jpg"
  ],
  "shots": [
    {
      "id": "shot_01",
      "filename": "shot_01_establishing.png",
      "scene": "雨夜高空俯拍，主角所在街区被蓝紫霓虹包围。",
      "prompt": "强调纵深透视与路面反光，镜头情绪紧张但克制。",
      "required_text": [
        {
          "label": "招牌",
          "text": "云上面馆",
          "style": "暖橙霓虹手写体，边缘清晰"
        }
      ],
      "visual_elements": [
        "黑色长伞",
        "红色尾灯拖影",
        "潮湿柏油路"
      ],
      "reference_images": [
        "./refs/shot_01_pose.png"
      ],
      "aspect_ratio": "21:9"
    }
  ]
}
```

执行：

```bash
python3 scripts/generate_panels.py \
  --config /path/to/storyboard.json \
  --output-dir ~/storyboard_output/project_name \
  --aspect-ratio 16:9 \
  --image-size 1K \
  --save-prompts
```

确认后再出终稿：

```bash
python3 scripts/generate_panels.py \
  --config /path/to/storyboard.json \
  --output-dir ~/storyboard_output/project_name_4k \
  --model models/gemini-3-pro-image-preview \
  --image-size 4K \
  --save-prompts
```

### 2. 分析图片并拆素材

```bash
python3 scripts/analyze_image_scene.py \
  --image /path/to/scene.png \
  --output-dir ~/storyboard_output/project_name/scene_pack
```

如果要联合分析多张图，可重复传入 `--image`：

```bash
python3 scripts/analyze_image_scene.py \
  --image /path/to/scene_a.png \
  --image /path/to/scene_b.png \
  --output-dir ~/storyboard_output/project_name/scene_pack
```

### 3. 分析视频结构和风格

本地视频：

```bash
python3 scripts/analyze_video_story.py \
  --video /path/to/video.mp4 \
  --output-dir ~/storyboard_output/project_name/video_report
```

YouTube 视频：

```bash
python3 scripts/analyze_video_story.py \
  --youtube-url "https://www.youtube.com/watch?v=..." \
  --output-dir ~/storyboard_output/project_name/video_report
```

## 输出说明

推荐输出结构：

```text
~/storyboard_output/{YYYY-MM-DD}_{project_name}/
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

## 参考文档

- 配置结构：[`references/config_schema.md`](./references/config_schema.md)
- Prompt 组织方式：[`references/prompt_template.md`](./references/prompt_template.md)
- Gemini 工作流说明：[`references/gemini_workflows.md`](./references/gemini_workflows.md)

Gemini 官方文档：

- [图片生成](https://ai.google.dev/gemini-api/docs/image-generation?hl=zh-cn)
- [图片理解](https://ai.google.dev/gemini-api/docs/image-understanding?hl=zh-cn)
- [视频理解](https://ai.google.dev/gemini-api/docs/video-understanding?hl=zh-cn)

## 当前边界

- 当前“拆素材”是基于模型理解后的框选裁切，不是精细抠图或真实分层 PSD。
- 当前“背景分离”是保留背景参考图并生成背景重建 prompt，不等同于自动无损分层。
- 图片生成质量仍受模型当期可用版本、参考图质量和 prompt 精度影响。
- 如果 `models/gemini-3.1-flash-image-preview` 在当前账号或地区不可用，脚本会继续尝试 `models/gemini-3-pro-image-preview`。

## 建议的下一步

- 增加统一的 `sample_configs/` 示例目录
- 增加批处理任务入口，把“生成分镜图 + 拆素材 + 视频分析”串成完整流水线
- 增加真实样例回归测试，验证不同类型项目的输出稳定性
