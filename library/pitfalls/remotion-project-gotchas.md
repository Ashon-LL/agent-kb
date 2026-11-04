---
name: remotion-project-gotchas
description: Remotion 4 工程实测坑合集——默认输出 yuvj420p(full range) 要显式 --pixel-format=yuv420p --color-space=bt709 才是标准 yuv420p；LightLeak 组件是全屏不透明叠加须 mixBlendMode/opacity 包裹；effects prop 只挂在 Img/HtmlInCanvas/AnimatedImage/CanvasImage/Solid；eslint 的 non-pure-animation 会拦对象里名为 transition 的键；npm 11.17 下 create-video 内置装依赖报 EALLOWSCRIPTS
type: pitfall
source: 10年人间 EP01 P0（2026-10-29 本机 Windows，Remotion 4.0.539 实测）
date: 2026-10-29
verified: 2026-10-29
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

**Why**：这些都是「默认值不合预期」型静默失败——像素格式不报错但成片在部分播放器偏色；LightLeak 不报错但画面被盖；effects 传错位置不报错只是没效果；eslint 那条会让人误以为是缓动写法有问题。全部要主动验证才会暴露。

**How to apply**：新建或接手 Remotion 工程时先按 1、3、4、5 过一遍配置与 lint；做光效前先按 2、3 确认 API 形状；渲染链路改完用「ffprobe 看像素格式/色彩空间 + 抽帧目视」双验，别只看「渲染成功」。相关：[[zcode-plugin-python-runtime-isolation]]、[[no-assertion-without-measurement]]。

关联 [[no-assertion-without-measurement]]、[[zcode-plugin-python-runtime-isolation]]。
