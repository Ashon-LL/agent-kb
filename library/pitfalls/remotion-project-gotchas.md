---
name: remotion-project-gotchas
description: Remotion 4 工程实测坑合集——默认输出 yuvj420p 要显式 pixel-format/color-space；LightLeak 全屏不透明需 mixBlendMode 包裹；effects prop 只挂部分组件；eslint 拦 transition 键；npm 11.17 create-video 报 EALLOWSCRIPTS；EP02 补充 Google Fonts 900+ 请求、端口占用、r3f postprocessing 黑帧、粒子字幕密度、freeze 与渲染预算
type: pitfall
source: 10年人间 EP01 P0（2026-10-29）+ EP02（2026-11-06），本机 Windows，Remotion 4.0.539 实测
date: 2026-10-29
verified: 2026-11-06
topic: toolchain
---

**经验**（Remotion 4.0.539 实测，多条独立小坑，合集收录）：

1. **默认输出像素格式是 `yuvj420p`（full range）**，不是标准 `yuv420p`。要拿到 tv range + bt709 必须显式：`--pixel-format=yuv420p --color-space=bt709`；长期做法是写进 `remotion.config.ts` 的 `Config.setPixelFormat("yuv420p")` + `Config.setColorSpace("bt709")`。判据用 `ffprobe -show_entries stream=pix_fmt,color_range,color_space`。
2. **`@remotion/light-leaks` 的 `<LightLeak>` 是整屏不透明叠加**：直接铺会把底层 three/文字全部盖住（第一次实测整帧只剩橙色光斑）。要用外层容器 `style={{opacity, mixBlendMode:'screen'}}` 包住，或改用 `@remotion/effects` 的 `lightLeak` descriptor。
3. **`effects` prop 不是所有组件都能吃**：实测只挂在 `Img` / `HtmlInCanvas` / `AnimatedImage` / `CanvasImage` / `Solid` 上（`remotion/dist/cjs/*.d.ts` 里 grep `EffectsProp`），给普通 `AbsoluteFill` 传 effects 不生效。
4. **eslint `@remotion/non-pure-animation` 会拦「对象里名为 `transition` 的键」**：因为它按属性名匹配 CSS 简写（`transition` / `transition-*` 等），一个普通的时长常量 `{transition: 0.5}` 会报 warning。改名（如 `sceneSwitch`）即可，不必加 disable 注释。
5. **`create-video` 在 npm 11.17 下自动装依赖会失败**：报 `EALLOWSCRIPTS: --allow-scripts is not allowed in project-scoped installs`。工程文件其实已生成，`cd` 进去手动 `npm i --loglevel=error` 即可，不影响后续。
6. **Three.js 无头渲染开箱可用**：`@remotion/three` 的 `<ThreeCanvas>` + `@react-three/fiber` 在默认 SwiftShader 下能出金属反射与双色补光，不必额外配 GL flag；风险在 shader/粒子量，不在能不能跑。
7. 验证环境别只渲染一帧就下结论：three、中文字体、音频轨、paths 描边要**各验一项**（本项目做法=一个 `EnvSmoke` composition 同时挂这几样，45 帧 720p 约 19 s）。中文字体走 `@remotion/google-fonts/NotoSansSC` 时会**在渲染期联网拉字体**，断网跑长渲染前先把字体落本地。
8. **Google Fonts 不传 options 会请求爆炸**：`loadNotoSansSC()` 不传 weights/subsets 时，单个渲染 tab 实测 **909 次**字体请求；Noto Serif SC 808 次；Inter 63/126 次。6 个并发 tab × 长片 = 启动和每帧都慢。修法：`loadFont("normal", {weights:["400","600","700"], subsets:["chinese-simplified","latin"]})`，或直接做本地子集字体（pyftsubset + `@remotion/fonts`）。没改之前先接受「长片渲染 30–40 分钟」。
9. **`No available ports found` 不一定是端口真被占**：`netstat` 看不到 3000 段监听，Remotion 仍可能报无可用端口。直接传 `--port=6789`（渲染/still 都支持）；多个渲染并行时各用不同端口，否则后一个会失败。
10. **`@react-three/postprocessing` 在本机 SwiftShader 下输出纯黑**：3.2.2 + postprocessing 6.39.6，连**空 EffectComposer**（不加任何 effect）也是黑帧；同场景 three 官方 `EffectComposer + RenderPass + BokehPass + UnrealBloomPass + OutputPass` 正常。先用「一个亮立方 + composer」的探针确认，再决定用哪套；不要拿复杂场景 debug 黑帧。
11. **粒子字幕的密度决定成败**：Canvas 采样 `step=2` + 粒子 1.8–4px + 停留抖动 0.55 → 笔画有洞、像被腐蚀。可用参数：`step=1`、粒子 1.4–2.8px、停留抖动 0.25、底字 alpha 0.15、canvas 加 `drop-shadow(0 0 6px rgba(245,196,81,.3))`；入场 12 帧（0.4s）比 20 帧更跟得上字幕节奏。
12. **数据段 5 秒静止会被 freezedetect 抓**：`freezedetect=n=-60dB:d=1.5` 对「只有字幕在换」的段落会连续报 freeze。要么给图表/背景加 1–3px 的相机漂移/呼吸/扫描光，要么在 QC 说明里标为设计内；不要静默忽略。
13. **渲染预算要提前算**：本机 1080p 实测 3D 段约 **0.83s/帧**（15s = 6 分钟），2.5D 数据段约 0.3–0.5s/帧；155s 全片约 **38 分钟**。迭代期用 720p/CRF23，终版再 1080p/CRF18；不要在 1080p 上反复试错。
14. **母带用 loudnorm 线性模式会保留原 LRA**：155s 全片初版 LRA 4.6（偏平），把段落增益从 0.3–0.9 拉开后到 **7.8**；目标 TP 设 −1.5 留余量。音频先渲成 WAV，视频渲完再 `ffmpeg -c:v copy` 混流，改音频不用重渲视频。
15. **有独显的机器，Remotion 默认 GL 仍可能退化成 SwiftShader**：实测 720p 3D 段 0.92 s/帧（300 帧 276s，12 核 6 tab）；显式 `--gl=angle` 后同样 300 帧 **17s**（含打包/编码），1080p 100 帧约 10s——**6–9 倍差距**，且不像「渲染成功但偏色」那样有可见症状，只会表现为「渲染慢到不合理」。长期写进 `remotion.config.ts`：`Config.setChromiumOpenGlRenderer("angle")`（无 GPU 时 Chromium 自动回退）。排期必须按 GPU 后端算。
16. **`@remotion/fonts` 的 `loadFont` 传公共目录 URL 必须套 `staticFile()`**：直接写 `/fonts/x.woff2` 会 404（公共目录有 hash 前缀，形如 `/public/fonts/x.woff2`）。另外它在模块作用域调用会失败/时序不稳，应在组件渲染中调用。**验收字体请求数**：`performance.getEntriesByType('resource')` 拿不到（Remotion 渲染上下文里几乎为空），可靠做法是临时劫持 `window.fetch` 计数，或用「入口不 import google-fonts + 只有 N 个本地字体文件」做上界估算。
17. **Reflector（three 官方平面镜）的 `color` 参数在暗色下会变色**：`blendOverlay(base, color)` 在暗部吃掉绿通道，金色反射变成纯红（实测像素 (81,0,0)）。要「暗一点的镜面」应把 Reflector 设成白色，再用一张半透明的暗色板叠在上面控制强度。
18. **多分辨率预览用「固定舞台 + transform: scale」比逐分辨率重写令牌省事**：设计令牌按 1080p 写，外层 `<div style={{width:1920,height:1080,transform:scale(height/1080)}}>` 包一层，720p 预览版式正确、终版 1080p scale=1 原生。**但**舞台内的 canvas/字幕组件若用 `useVideoConfig()` 取尺寸，会拿到实际分辨率而不是舞台分辨率，导致内容偏左/偏小——必须显式传 1920×1080。

19. **`--scale=0.6667` 会因非整数高度直接失败**：`TypeError: The "height" prop passed to stitchFramesToVideo() must be an integer, but is 720.036`。要 720p 预览**不要用 `--scale`**，用 `--width=1280 --height=720`（CLI 支持 `--width/--height` 覆盖），或 `--scale=0.5`。
20. **分段预览用 `--frames=<start>-<end>`**：`--start/--end` 实测没有把渲染限制到区间（仍渲了 4800 帧）。逐段验收（G3）就按 `--frames=0-639 / 640-1759 / …` 一条段一条命令，配合 `--width/--height` 出 720p；每段再 `ffmpeg -vf "fps=1,tile=6x7"` 出接触表 + `freezedetect`，才算「每段预览 + 抽帧 QC」。
21. **渲染是否完成看日志 `Encoded N/N`，不要看进程退出码**：后台 `nohup` 场景下进程可能先退出、日志尾部还停在中途计数（缓冲区未刷），或反过来进程还在跑；以最后一行 `Encoded <总帧数>/<总帧数>` + 输出文件 mtime/时长双向确认。

**Why**：这些都是「默认值/环境不合预期」型静默失败——像素格式不报错但成片偏色；LightLeak 不报错但画面被盖；effects 传错位置只是没效果；eslint 那条会被误认为缓动写法有问题；字体请求爆炸、端口、黑帧 composer、字幕腐蚀、GL 退化、字体 404、反射变色、多分辨率错位都只在真渲长片时暴露。全部要主动探针才看得见。

**How to apply**：新建或接手 Remotion 工程先按 1、3、4、5 过配置与 lint；先跑 8（字体请求）、9（端口）、10（composer 探针）、15（GL 后端实测）再开长渲；粒子字幕按 11 调密度；QC 按 12 看 freeze；排期按 13+15 算（确认走 GPU）；音频按 14 先 WAV 后混流；本地字体按 16 套 `staticFile` 并实测请求数；3D 反射按 17 用白板叠暗板；多分辨率按 18 用舞台缩放并显式传舞台尺寸给 canvas/字幕。渲染链路改完用「ffprobe 像素格式/色彩空间 + 抽帧目视」双验，别只看「渲染成功」。相关：[[zcode-plugin-python-runtime-isolation]]、[[no-assertion-without-measurement]]、[[code-animation-vs-html-video]]。

关联 [[no-assertion-without-measurement]]、[[zcode-plugin-python-runtime-isolation]]。
