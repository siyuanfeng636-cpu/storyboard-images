# Storyboard Prompt 构建模板

适用于批量分镜图生成、参考图控场景一致性，以及需要画面中文字清晰的场景。

## 通用结构

```
{GLOBAL_STYLE}

Scene:
{镜头的一句话摘要}

Shot intent:
{镜头语言、构图、情绪、镜头运动或补充视觉要求}

Required visual elements:
- {元素 1}
- {元素 2}

Required text (render exactly these characters, nothing else):
- {标签}: {文字内容} | {字体/材质/位置要求}

Image quality requirements:
- ultra-detailed
- crisp materials and edges
- production-ready high resolution
- legible typography

Forbidden:
- no extra text
- no watermark
- no logo unless explicitly requested
- no unrelated props
```

## 全局风格建议

- 场景/时代/地理环境。
- 时间段、天气、空气状态。
- 光源方向、色温、反射和阴影层次。
- 镜头语言：远景、近景、俯拍、跟拍、长焦、广角等。
- 材质要求：皮肤、布料、金属、玻璃、雾气、水面等的表现方式。
- 统一限制：不要多余人物、不要额外文字、不要品牌水印、不要错误手指。

## 分镜脚本解析规则

- 提取全局视觉要求，合并进 `GLOBAL_STYLE`。
- 每个镜头只保留一条最核心的 `Scene` 句子，避免 prompt 失焦。
- 对已有分镜图片、色板图、角色定妆图，优先作为 `reference_images` 输入，而不是把所有信息都塞进文字。
- 对需要清晰渲染的中文、英文或数字，一律列入 `Required text`。

## 场景一致性提示词模板

```markdown
# 场景一致性包

## 场景摘要
{场景的一句话总结}

## 光影关键词
- 主光源：
- 辅助光源：
- 阴影层次：
- 色温：
- 空气透视：

## 环境关键词
- 地点：
- 时间：
- 天气：
- 空间结构：
- 背景元素：

## 材质关键词
- 人物材质：
- 道具材质：
- 地面/墙面材质：

## 连续性约束
- 必须保持：
- 避免出现：
```

## 视频分析输出建议章节

- 视频整体概览
- 镜头节奏和结构
- 分镜拆解表
- 视觉风格与光影
- 特效与转场
- 适合 Seedance 的素材建议
- 可直接复用的 prompt 建议
