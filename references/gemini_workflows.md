# Gemini 工作流说明

本技能优先使用 Gemini 官方 Python SDK `google-genai`。

官方文档：

- 图片生成：https://ai.google.dev/gemini-api/docs/image-generation?hl=zh-cn
- 图片理解：https://ai.google.dev/gemini-api/docs/image-understanding?hl=zh-cn
- 视频理解：https://ai.google.dev/gemini-api/docs/video-understanding?hl=zh-cn

## 模型选择

- 图片生成：优先使用当前可用的 Gemini 图片模型，默认写成 `gemini-2.5-flash-image`，但脚本保留 `--model` 覆盖能力。
- 图片理解：默认 `gemini-2.5-flash`。
- 视频理解：默认 `gemini-2.5-flash`，本地视频通过 Files API 上传。

## 什么时候用哪种输入方式

- 单张或少量图片：直接本地读取并作为多模态输入。
- 大视频或可复用视频文件：先上传到 Files API，再让模型分析。
- 公网 YouTube 视频：可以直接提供 URL 给视频分析脚本。

## 实施原则

- 需要生成图片时，把“清晰文字、清晰材质、高清细节、不要额外文字”写进 prompt，不要依赖默认模型行为。
- 需要拆素材时，先让模型输出结构化素材清单和框选结果，再做本地裁切。
- 需要保持场景一致性时，同时保存 `scene_analysis.json` 和 `scene_prompt.md`，避免只保存图片不保存语言约束。
- 需要理解视频时，输出至少两份结果：
  - 人可读的 Markdown。
  - 机器可继续消费的 JSON。

## 失败处理

- 模型返回非 JSON 文本时，先提取代码块或首个 JSON 对象重试解析。
- 图片生成未返回图片时，记录响应文本并重试。
- 文件上传后若状态未就绪，轮询 `files.get` 直到可用或超时。
- 长视频分析失败时，缩短视频片段或改为分段分析。
