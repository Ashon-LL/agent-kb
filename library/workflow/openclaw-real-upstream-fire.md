---
name: openclaw-real-upstream-fire
description: OpenClaw 真实上游实弹验证（Windows 本机）——exec 可用、--local 不收敛
type: workflow
source: MH-Agent-Open D-17
date: 2026-09-18
---

**背景**：D-17 长期缺口 = 「默认 harness 已是 openclaw，但**从未在真实上游跑通完整回合**」。
2026-09-18 用本机已有凭证（`~/.MHAgentOpen/db/mhagent.db` 的 `executor_*`）实弹验证。

## 一、前置坑：读设置千万别打印值

`settings` 表是 `key/value` 两列。核凭证只报 `<非空>`/`<空>`，**不打印 value**。
本机实测这些**非空**：`executor_api_key`、`executor_base_url`、`reviewer_*`、
`vision_*`、`editor_ai_*`、`gpt_image_*`、`aminer_api_key`。

## 二、⛔ 两个立刻会踩的坑（实测）

1. **上游带 Cloudflare：不带浏览器 UA 直接 403 `error code: 1010`**，
   带上 UA 立刻 200。凡直连探活失败且是 403/1010，先加 UA 再怀疑 key。
2. **Git Bash 里跑 openclaw，`--state-dir` 会被 MSYS 转换**：
   `/c/Users/...` → `C:\c\Users\...`（报 `State directory does not exist`）。
   **必须 `export MSYS_NO_PATHCONV=1`**，且路径写 `C:/Users/...` 形态。

## 三、配置不要手写，用应用自己的函数

```python
sys.path.insert(0, 'backend')
from services import session_env as se
se.write_openclaw_config(settings_dict, wf_id)   # → <state-dir>/openclaw.json
```

`[实测]` 生成的 config：`gateway.mode=local`；`models.providers.mh-upstream`
（`baseUrl`/`apiKey`/`api=openai-completions`）；`agents.defaults.model.primary`；
`tools.profile=coding`。与主路径同源，避免手工拼出「看似对但不走同一条路」的配置。

## 四、实弹结果（Windows / Node v26.9.0 / OpenClaw 2026.9.4）

| 路径 | 命令形态 | 结果 |
| --- | --- | --- |
| **exec** | `agent exec --cwd <ws> --state-dir <st> --config <cfg> --json "<prompt>"` | ✅ **稳定成功**（复现 3 次）：`ok:true`、正文正确、`assistantTurns` |
| **exec + 工具** | 同上，prompt 要求读文件 | ✅ `toolSummary.calls=1`、`tools=["read"]`、`failures=0`，模型报出内容与文件**一致** |
| **--local** | `agent --local --session-key <k> --json --message "<text>"` | ❌ **不收敛**：上游两次 200 后挂死，300s 超时 exit 124，**两次复现** |

**⛔ `--local` 不接受位置参数 prompt**，必须 `-m/--message`（否则报
`has no command "..."`）。同理 `--local` **不接受 `--config`/`--cwd`**，
配置只能靠 `OPENCLAW_CONFIG_PATH` + `OPENCLAW_STATE_DIR` 环境变量。

**对照**：同 state-dir / config / 上游下，`exec` 稳定 exit 0、`--local` 稳定超时
⇒ 差异不在凭据/配置/上游可达性，在**两条子命令的后半程行为**。根因 `[未知]`
（无终局 envelope，stdout 空）。`--local` 侧伴随日志
`[memory] memory_index_chunks_vec not updated …`（`[推断，未验证]` 可能与挂死相关）。

## 五、顺带现实验证了另一条 kb 经验

`max_tokens=16` 时 `content=None`、`reasoning_content` 有 77 字符、
`finish_reason=length`；提到 `512` 时 `content="ok"`、`finish_reason=stop`。
→ 与 `pitfalls/reasoning-model-max-tokens-shares-budget.md` **逐条吻合**：
思考与正文共用预算，读正文必须 `.get` 并按合计留量。

## How to apply

- 要验证某个 harness/harness 路径是否真能用：**先直连上游探活**（带 UA），
  再跑最小回合，**再跑工具调用回合** —— 三层都过才算「实弹可用」。
- 遇到「进程不收敛」类问题：**必设 timeout 并做对照实验**（换个稳定路径复跑），
  用「同环境同配置下 A 稳 B 不稳」把变量锁死，别在单点上猜根因。
- 结论分档：现象（exit code / stdout）/ 对照 / 根因 —— 根因没定位就写 `[未知]`，
  不得把「本机不收敛」写成「该功能不支持」。
