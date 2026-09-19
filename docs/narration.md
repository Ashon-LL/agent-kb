# agent-kb 宣传视频 · 旁白脚本（Doro 风格）

## 配音提示

- **音色**：萌系女声，略带鼻音，活泼跳脱，像 Doro/Doki Doki 那种
- **语速**：稍快但吐字清晰，像在跟朋友安利宝贝
- **情绪**：好奇 → 兴奋 → 得意 → 萌系结尾
- **总时长**：约 23 秒
- **背景音乐**：轻快 8-bit / Lo-Fi 钢琴，音量 -12dB 以下不要盖过语音

---

## 逐段台词（按时间点）

| # | 时间 | 时长 | 对应画面 | 台词（中文） |
|---|---|---|---|---|
| 1 | 0:00–0:03 | 3s | **shot-1-home.png**（仓库首页，开场大字弹出"你的 AI Agent 还在重复踩坑？"） | 你的 AI Agent 还在重复踩坑？ |
| 2 | 0:03–0:05 | 2s | 首页切近仓库名区域，高亮 agent-kb 字样 | 我来救你啦～ 我是 Doro！ |
| 3 | 0:05–0:08.5 | 3.5s | **shot-2-skill.png**（Skill 规程文件） | agent-kb — 一个让 AI 终身不重复踩坑的全局经验库！ |
| 4 | 0:08.5–0:12 | 3.5s | **shot-3-hooks.png**（kb_core.py 代码） | 分四层：Hook 自动提醒，Skill 统一规程，命令直接检索，库是纯 Markdown。 |
| 5 | 0:12–0:15 | 3s | **shot-7-templates.png**（hooks.json 模板目录） | 最棒的是——零阻塞！钩子坏了也静默退出。 |
| 6 | 0:15–0:17.5 | 2.5s | **shot-5-library.png**（library-template 目录） | 空库模板一上来就有三条示例，照着改就行。 |
| 7 | 0:17.5–0:20 | 2.5s | **shot-4-install.png**（install.ps1） | Windows 上一行命令搞定，跨平台支持 Trae、ZCode、Codex。 |
| 8 | 0:20–0:23 | 3s | **shot-8-readme.png**（README 底部的仓库 URL 区域） | GitHub 搜 Ashon-LL/agent-kb，Star 一下嘛～ 拜拜！ |

---

## 剪辑要点（剪映 / 必剪 / CapCut）

1. **画面尺寸**：竖屏 9:16（B站推荐），1080×1920
2. **每张图的运动**：轻微 Ken Burns 缩放（0.8→1.0），不要过快
3. **字幕**：自动生成后对齐 SRT 时间点；字体用 "站酷快乐体" 或 "思源黑体 Heavy"；位置屏幕下方 1/3
4. **转场**：默认 "淡入淡出" 即可；最后一镜切黑配 "拜拜～" 语音
5. **贴纸/emoji**：第 1 镜加 💢 问号感叹号，第 2 镜加 ✨，最后一镜加 ⭐
6. **音效**：第 4 镜 "四层" 每层浮现时加 "咔哒" 音；第 7 镜 "一行命令" 后加 "叮" 音

---

## 本地试剪

截图已推送到仓库 `docs/screenshots/clean/` 目录：

```
docs/screenshots/clean/
├── shot-1-home.png          # 仓库首页
├── shot-2-skill.png         # Skill 规程文件
├── shot-3-hooks.png         # kb_core.py 代码
├── shot-4-install.png       # install.ps1
├── shot-5-library.png       # library-template 目录
├── shot-6-commands.png      # commands 目录
├── shot-7-templates.png     # templates 目录
└── shot-8-readme.png        # README 完整页面
```

SRT 字幕：`docs/video-subtitles.srt`
完整视频脚本：`docs/video-script.md`（架构图解版，给更专业的剪法参考）
