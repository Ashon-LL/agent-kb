---
name: ffmpeg-jpeg-sequence-color-range
description: JPEG/PNG 帧序列用 ffmpeg 编码默认输出 yuvj420p/pc 全范围；-pix_fmt yuv420p 只定色度采样不切范围，必须 scale=in_range=full:out_range=tv + -color_range tv -colorspace bt709，并用 ffprobe 验 pix_fmt/color_range/color_space 三项
type: pitfall
source: 10years-humanity EP06 v2（2026-11-09，code-render → JPEG 帧序列 → ffmpeg）
date: 2026-11-10
verified: 2026-11-09
topic: toolchain
---

## 经验

代码逐帧渲染出的 JPEG/PNG 序列（Remotion、手写 render.js、Playwright 截图）用 ffmpeg 编码时，
**默认会带 full range 标记**：`ffprobe` 看到 `pix_fmt=yuvj420p`、`color_range=pc`。
只写 `-pix_fmt yuv420p` 不够——它改的是色度采样，不是范围；输出仍可能是 `yuvj420p/pc`。

正确命令（8M 暗场示例）：

```bash
ffmpeg -framerate 30 -i frames/f%05d.jpg \
  -vf "scale=in_range=full:out_range=tv:out_color_matrix=bt709" \
  -c:v libx264 -b:v 8M -threads 4 -preset medium \
  -pix_fmt yuv420p -color_range tv \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -movflags +faststart out.mp4
```

判据（三项同时满足）：

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=pix_fmt,color_range,color_space -of default=nw=1 out.mp4
# pix_fmt=yuv420p / color_range=tv / color_space=bt709
```

## Why

- JPEG 帧本身是 full range；ffmpeg 默认按输入色彩空间打 `pc` 标记。播放器若按 limited 解，会把黑位抬高/白位压缩；若按 full 解而平台转码按 limited，画面会发灰或对比过强。
- `-color_range tv` **只改标记不转换像素**；必须先用 `scale=in_range=full:out_range=tv` 做 0–255→16–235 的实际映射，否则是「标 limited、内容是 full」的错配。
- 系列交付规范要 `yuv420p/tv/bt709`；v1/EP05 历史交付实测是 `yuvj420p/pc`，属于漏检，不是有意的风格选择。

## How to apply

- 任何「代码渲染帧序列 → ffmpeg」的管线，编码后先跑上面的 ffprobe 三项，再进 QC/上传。
- 如果已经用错范围出了片，不要只补 `-color_range tv` 重封装；必须带 `scale=in_range=full:out_range=tv` 重编，否则像素值不变。
- 抽一帧对比重编前后的亮度直方图：正确转换后 limited 文件的 Y 范围应落在约 16–235（源有纯黑/纯白时；以直方图实测为准），显示时应与母版一致。
- 相关：[[remotion-project-gotchas]]（Remotion 自身输出 yuvj420p 的 config 修法）。
