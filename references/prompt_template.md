# Storyboard Prompt 构建模板

## 结构

每个 Panel 的 prompt 由三部分组成：

```
{STYLE_PREFIX}

{PANEL_CONTENT}

{FORBIDDEN_SUFFIX}
```

## STYLE_PREFIX（全局风格前缀）

```
Create a single storyboard panel in ultra-premium sci-fi command center UI style.
Dark navy-blue background (#0a0e27) with cyan (#00e5ff), ice-blue (#7ec8e3), and subtle amber (#ffb300) glow accents.
Sleek, elite, high-tech cinematic infographic. Semi-flat futuristic UI mixed with cinematic interface rendering.
Background: subtle grid-dot matrix, faint digital particles, HUD interface lines, glowing data streams.
CRITICAL RULE: Render ONLY the exact Chinese text specified below. Do NOT add any extra text, labels, slogans, watermarks, or decorative words beyond what is explicitly listed.
The design must feel like a next-generation smart grid dispatch system — not a generic flowchart, not cartoonish, not childish.
Clean, polished, ultra-high-definition 4K presentation quality.
```

## PANEL_CONTENT 格式

每个面板的内容应包含：

1. **Scene** — 一句话描述场景
2. **REQUIRED TEXT** — 明确列出需要在图片中渲染的文字，格式为：
   ```
   REQUIRED TEXT (render exactly these characters, nothing else):
   - Main heading (large, bold, amber-glowing): 标题文字
   - Subheading (medium): 副标题文字
   ```
3. **Visual elements** — 视觉元素描述

## FORBIDDEN_SUFFIX（禁止后缀）

```
FORBIDDEN: Do not render any text other than the lines specified above.
```

## 分镜脚本解析规则

输入的分镜脚本文本通常包含以下结构：

1. 全局视觉要求（风格、色调、设计语言等）
2. 环境约束
3. 9 个 Panel 的描述（通常标记为 Panel 1 ~ Panel 9 或 ### Panel 1）

解析策略：
- 从脚本中提取「全局视觉要求」合并为 STYLE_PREFIX
- 每个 Panel 提取：标题/场景描述、需要渲染的文字、视觉元素
- 将脚本中的「Negative constraints」/「不得包含」内容加入 FORBIDDEN 后缀

## 文字渲染规范

为了确保 Gemini 正确渲染中文文字：
- 使用 `REQUIRED TEXT` 标签明确标记需要渲染的文字
- 每行文字用 `-` 列表项标出，并注明样式（large/bold/medium 等）
- 用 `FORBIDDEN` 标签明确禁止多余文字
- 文字内容用引号包裹，避免歧义
