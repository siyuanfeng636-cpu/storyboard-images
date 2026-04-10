# 配置文件结构

`scripts/generate_panels.py` 同时兼容旧版 `panels` 配置和新版 `shots` 配置。

## 推荐使用的新版结构

```json
{
  "project_name": "city-night-launch",
  "global_style": "电影感赛博都市，潮湿路面，霓虹反射，材质清晰。",
  "global_negative": "不要额外文字，不要多余人物，不要水印，不要变形手部。",
  "default_aspect_ratio": "16:9",
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
        "潮湿柏油路",
        "街边翻倒的塑料凳"
      ],
      "reference_images": [
        "./refs/shot_01_pose.png"
      ],
      "aspect_ratio": "21:9"
    }
  ]
}
```

## 字段说明

- `project_name`: 项目名，仅用于输出目录标识。
- `global_style`: 全局风格前缀，适用于全部镜头。
- `global_negative`: 全局禁止项。
- `default_aspect_ratio`: 未单独指定时的默认画幅。
- `global_reference_images`: 对全部镜头生效的风格或场景参考图。
- `shots`: 任意数量的镜头列表。

### `shots[]` 字段

- `id`: 推荐写成 `shot_01` 这类稳定标识。
- `filename`: 输出图片文件名。
- `scene`: 镜头的一句话场景摘要。
- `prompt`: 补充细节、构图、镜头语言、质感要求。
- `required_text`: 画面中必须清晰渲染的文字。支持字符串数组或对象数组。
- `visual_elements`: 画面中必须出现的重要元素。支持字符串数组。
- `reference_images`: 仅对当前镜头生效的参考图列表。
- `aspect_ratio`: 当前镜头单独指定画幅。

## 旧版兼容结构

旧版仍可使用：

```json
{
  "style": "旧版全局风格",
  "panels": [
    {
      "id": 1,
      "filename": "panel_01.png",
      "prompt": "完整 prompt"
    }
  ]
}
```

脚本会将 `panels` 视为 `shots` 处理。

## 图片分析输出结构

`scripts/analyze_image_scene.py` 会生成：

- `scene_analysis.json`: Gemini 返回的结构化理解结果。
- `scene_prompt.md`: 光影、环境、风格、一致性提示词。
- `asset_manifest.md`: 素材用途和裁切说明。
- `assets/*.png`: 按框裁切后的素材图。
- `assets/background_reference.png`: 原图拷贝，作为背景参考。

## 视频分析输出结构

`scripts/analyze_video_story.py` 会生成：

- `video_analysis.md`: 面向人阅读的完整分析。
- `video_analysis.json`: 结构化分析结果，方便后续继续处理。
