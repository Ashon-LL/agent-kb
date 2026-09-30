---
name: persisting-files-also-requires-exempting-cleanup
description: 把临时文件改成"持久"要同时改三处——落盘目录、清理豁免、清理函数自己枚举的目录；只改落盘目录仍会被每轮清理钩子删掉。诊断：历史记录里的文件路径批量 MISSING 就顺 track_/cleanup_ 找
type: pitfall
source: APIShow/AstrBot v4.27.4（2026-09-18 收到的图片每轮被清，历史图片全部失效）
date: 2026-09-18
---

**经验**："文件不持久"往往不是存错了地方，而是**有人定时删它**。换成持久目录只是第一步，还要把清理链路一起放开。

**Why**：本次现象是"机器人看不到用户之前发的图"。排查发现历史消息里的图片路径**全部 MISSING**——根因不在读图代码，而在事件生命周期：每条消息处理时 `event.track_temporary_local_file(path)` 登记媒体文件，处理完 `cleanup_temporary_local_files()` 把它们删掉；而登记逻辑只认临时目录下的文件，**清理函数自己也会按目录枚举并删除**，所以只把落盘目录换掉是无效的。改完落盘目录后历史图片仍全是空路径，就是这个原因。

**How to apply**：

1. **诊断先看文件在不在**：拿历史记录里的路径直接 `ls`。批量 MISSING ⇒ 是清理问题，别去查解码、协议或客户端。
2. `grep -rn "track_temporary\|cleanup_temporary\|os.remove\|unlink" <应用源码>`，把**写入路径**和**清理路径**两处一起改。
3. **清理函数要加"豁免目录"判断**，且用 `os.path.abspath(p).startswith(abspath(persist_dir) + os.sep)` 这类**带分隔符**的前缀比较——裸 `startswith(dir)` 会把 `media_old/` 一起放行。
4. **只豁免目标类型**（本次 png/jpg/jpeg，gif 与音视频继续走临时），别图省事把整个清理函数关掉——磁盘会无声上涨。
5. 改完必须**实打验证**：发一条带图消息 → 等清理钩子跑完 → 回查文件仍在；只改代码不验证等于没改。

**相邻**：验证要走应用自己的管线见 [[verify-with-real-pipeline-and-readonly-probes]]；"改了文件 ≠ 新代码在跑"见 [[file-change-not-code-running]]。
