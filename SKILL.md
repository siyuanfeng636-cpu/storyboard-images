---
name: storyboard
description: 3×3 分镜脚本图片生成技能。当用户提供分镜脚本（storyboard）文本并需要生成对应的高清图片时使用此技能。支持自动拆分 9 个面板、调用 Gemini API 生成 4K 图片、本地保存。触发词：分镜、storyboard、生成分镜图、生成图片面板。
---

# /storyboard — 3×3 分镜高清图生成

将用户的分镜脚本文本自动拆分为 9 个面板，调用 Gemini API 生成 4K 高清图片并保存到本地。

## 使用方式

1. 用户输入 `/storyboard` 后，提示用户粘贴完整的分镜脚本文本
2. 或者用户直接在消息中提供分镜脚本并说明要生成图片

## 工作流程

### Step 1: 接收与解析分镜脚本

从用户提供的文本中提取以下内容：

- **全局视觉要求**：风格、色调、设计语言、背景细节 → 合并为 `STYLE` 前缀
- **环境约束**：必须包含/不得包含的元素 → 加入对应面板的 prompt
- **Negative constraints**：禁止元素 → 加入 `FORBIDDEN` 后缀
- **9 个 Panel**：每个 Panel 的场景描述、文字内容、视觉元素

### Step 2: 构建 Prompt

先读取 `references/prompt_template.md` 了解模板规范。

每个 Panel 的 prompt 结构：

```
{STYLE}

Scene: {一句话场景描述}

REQUIRED TEXT (render exactly these characters, nothing else):
- {文字1}: {内容}
- {文字2}: {内容}

Visual elements: {视觉元素描述}

FORBIDDEN: Do not render any text other than the lines specified above.
```

**关键规则：**
- 每个 prompt 必须明确标注 `REQUIRED TEXT`，列出所有需要在图片中渲染的中文文字
- 必须以 `FORBIDDEN` 后缀禁止多余文字，避免 Gemini 添加衍生文字
- 文字用引号包裹，注明样式（large/bold/medium 等）

### Step 3: 生成配置文件

将拆分结果写入临时 JSON 配置文件：

```json
{
    "style": "全局风格前缀...",
    "panels": [
        {
            "id": 1,
            "filename": "panel_01_{简短英文描述}.png",
            "prompt": "完整 prompt..."
        }
    ]
}
```

保存到 `~/storyboard_output/{项目名}/panels_config.json`。

### Step 4: 调用生成脚本

```bash
python3 ~/.claude/skills/storyboard/scripts/generate_panels.py \
    --config ~/storyboard_output/{项目名}/panels_config.json \
    --output-dir ~/storyboard_output/{项目名}/ \
    --aspect-ratio 16:9 \
    --image-size 4K
```

**参数说明：**
- `--aspect-ratio`: 支持 "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"
- `--image-size`: 支持 "1K", "2K", "4K"（4K = 5504×3072）
- `--retry-failed`: 只重新生成输出目录中缺失的面板

**前提条件：**
- 环境变量 `GEMINI_API_KEY` 必须已设置
- Python 依赖：`requests`, `Pillow`

### Step 5: 补生成与验证

如果有面板生成失败，自动使用 `--retry-failed` 重试：

```bash
python3 ~/.claude/skills/storyboard/scripts/generate_panels.py \
    --config {同上} --output-dir {同上} --retry-failed
```

最后验证所有 9 张图片是否存在，报告结果。

### Step 6: 结果汇报

向用户汇报：
- 生成数量（成功/总数）
- 每张图片的分辨率
- 输出目录路径
- 可用 `open ~/storyboard_output/{项目名}/` 预览

## 默认输出路径

`~/storyboard_output/{YYYY-MM-DD}_{主题关键词}/`

例如：`~/storyboard_output/2026-04-10_drone_inspection/`

## 注意事项

- 每张 4K 图片约 1-3MB，生成时间约 15-30 秒/张
- API 有速率限制，脚本已内置 3 秒间隔
- 如遇到 SSL 或超时错误，脚本会自动重试最多 3 次
- 文字渲染质量取决于 prompt 的精确程度，务必在 `REQUIRED TEXT` 中列明所有文字
- 图片保存在本地，不会自动上传任何云服务
