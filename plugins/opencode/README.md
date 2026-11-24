# OpenCode V2 插件（agent-kb）

OpenCode V2 没有 stdin/stdout hook 协议，扩展点是 TS/JS 插件。本目录提供一个
最小的 V2 server 插件，把 kb 的提醒注入到 OpenCode 会话：

| 时机 | 注入内容 |
|---|---|
| 会话第一次模型调用 | `SessionStart` 开工提醒（先查 kb 再动手） |
| 用户输入命中 kb 触发词 | `UserPromptSubmit` 沉淀规程（查重、落盘、跑 `kb_validate`） |

Stop/收尾提醒**未实现**：OpenCode V2 没有等价的 Stop hook。`session.idle` 只能
在空闲时写状态，不能像 ZCode 那样把文本注入刚结束的那一轮；下一轮再注入会变成
过期提醒。需要收尾核验时，仍按 kb 技能规程手动执行。

## 依赖

- 插件只负责 OpenCode 的 hook 生命周期；提醒文案仍来自 `kb_core.py`。
- 插件通过 shell 调起 Python 桥 `hook-bridge/agent-kb/opencode_adapter.py`，
  因此需要：
  - `opencode_adapter.py`
  - `adapter_base.py`
  - `kb_core.py`
  这三个文件由安装器复制到 `~/.config/opencode/hook-bridge/agent-kb/`。

## 安装

```powershell
# 安装器会复制桥接脚本，并把本插件复制到 ~/.config/opencode/plugins/agent-kb
.\scripts\install.ps1 -Platform opencode
```

在 `~/.config/opencode/opencode.jsonc` 的 `plugins` 数组中注册：

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "plugins": ["./plugins/agent-kb"]
}
```

OpenCode 会热加载配置；保存后新会话/下一次模型调用生效。

## 环境变量

| 变量 | 作用 |
|---|---|
| `AGENT_KB_PYTHON` | Python 可执行文件；默认 Windows 用 `python`，其他平台用 `python3` |
| `AGENT_KB_OPENCODE_BRIDGE` | 覆盖 `opencode_adapter.py` 路径 |
| `AGENT_KB_PATH` | 透传给桥，覆盖默认 `~/.agents/kb` |
| `AGENT_KB_DEBUG=1` | 桥向 stderr 输出诊断；插件本身仍静默 |

## 验证

不启动 OpenCode 也能验证桥：

```bash
printf '%s' '{"hook_event_name":"SessionStart"}' \
  | python ~/.config/opencode/hook-bridge/agent-kb/opencode_adapter.py
printf '%s' '{"hook_event_name":"UserPromptSubmit","prompt":"记住这个坑"}' \
  | python ~/.config/opencode/hook-bridge/agent-kb/opencode_adapter.py
```

两条命令都应输出含 `hookSpecificOutput.additionalContext` 的 JSON。

## 设计约束

- 任何异常/超时都静默返回，绝不让 kb 阻塞 OpenCode。
- 不复制 `kb_core.py` 的文案或触发词；触发判断由 Python 桥完成。
- 每个会话只注入一次开工提醒；插件重载后会在下一次模型调用再注入一次。
