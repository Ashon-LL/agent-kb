# 全局经验库 · 版本/环境复审清单

> 生成：2026-09-30（kb 治理 P1-1）。
> 口径：正文命中 `\d+\.\d+|\brc\.?\d+`（任务书宽松口径）者 **47 / 110**。
> ⚠ 该口径会误收**量化数据**（对比度 3.55/5.40、112.1M tokens、585.4MB…），并非软件版本；
> 已在下面「P3」单列，**无需版本复审**。
> 复审 = **核对不是重测**：未实际重跑者不擅改结论；`verified:` 字段只记录「最近一次有记录的实测日期」，
> 不等于「治理日已确认仍在效」。发现无法确认的标为待验证，不删条目。

## 优先级

- **P1 高**：明确依赖某**活跃更新**软件的版本行为，升版后可能静默失效 → 换版本/遇异常时优先复核。
- **P2 中**：依赖版本/环境，但接口较稳或影响面小。
- **P3 低**：正则误报（量化数据），非版本依赖，无需复审。

## P1（高）— 13 条

| 条目 | 版本/环境串 | 依赖 |
|---|---|---|
| `pitfalls/newapi-rc26-channel-crud-shapes.md` | rc.26 | New API 渠道 API |
| `pitfalls/newapi-rc26-token-crud-shapes.md` | rc.26 | New API 令牌 API |
| `pitfalls/newapi-disable-must-sync-abilities.md` | rc.26 | New API abilities 路由事实源 |
| `pitfalls/silent-continue-masks-lost-check-coverage.md` | rc26 | New API 校验逻辑 |
| `pitfalls/third-party-db-columns-typed-by-reading-code.md` | rc.26 | New API DB 列类型 |
| `pitfalls/llm-context-window-is-input-plus-output.md` | AstrBot tdp + qwen3.8-27b | 网关窗口校验 |
| `pitfalls/dsh-llm-pi-ai-reasoning-config-traps.md` | DSH pi-ai | 推理配置 |
| `pitfalls/zcode-provider-config-no-reasoning-enabled-schema.md` | ZCode | provider_config schema |
| `tools/zcode-platform-verified-facts.md` | ZCode | 平台资源落点 / hooks |
| `tools/zcode-session-delete-is-soft-delete-two-dbs.md` | ZCode | 会话存储双库 |
| `tools/mcp-stdio-install-smoke-test.md` | uvx / mcp<2 | MCP stdio 安装 |
| `pitfalls/tauri-linux-ci-needs-webkit-41-and-target-override.md` | webkit2gtk-4.1 / tauri 2.0 | Tauri Linux CI |
| `pitfalls/tauri-remote-url-has-no-ipc.md` | tauri 2.11 | Tauri ACL |

## P2（中）— 16 条

| 条目 | 版本/环境串 | 依赖 |
|---|---|---|
| `pitfalls/config-field-name-is-not-spec-read-consuming-code.md` | 4.27 | AstrBot 配置字段 |
| `pitfalls/container-image-source-patches-need-replay-script.md` | 4.27 | CNB 基础镜像 |
| `pitfalls/persisting-files-also-requires-exempting-cleanup.md` | 4.27 | CNB 基础镜像 |
| `pitfalls/verify-with-real-pipeline-and-readonly-probes.md` | 4.27 | CNB 基础镜像 |
| `pitfalls/layered-service-credentials-must-match-layer.md` | 4.1 | 多层凭据服务 |
| `pitfalls/dont-handroll-spec-encoders-use-libraries-plus-fallback.md` | 1.3 | segno（QR 库） |
| `pitfalls/reasoning-model-max-tokens-shares-budget.md` | 6.8 | 推理模型 |
| `pitfalls/p256-ecdsa-handrolled-pitfalls.md` | 3.2 / 6.1 | Python / cryptography |
| `pitfalls/windows-titlebar-theme-dictated-by-system.md` | 10.0.26200 | Win11 build |
| `pitfalls/powershell-tool-stdout-empty-write-files-instead.md` | 5.1 / 7.6 / 26100 | PowerShell |
| `pitfalls/powershell-herestring-grammar-and-runtime-divergence.md` | 5.1 / 7.6 / 26100 | PowerShell |
| `pitfalls/powershell-start-process-argumentlist-strips-quotes.md` | 5.1 / 24.19 | PowerShell |
| `pitfalls/windows-scripting-terminal-gotchas.md` | 5.1 | PowerShell / Windows |
| `tools/cnb-secret-repo-imports.md` | 3.11 / 3.12 / 3.13 | Python |
| `tools/html-to-docx-windows-venv-layout.md` | 3.12 | uv / venv |
| `tools/electron-builder-nsis-silent-install-fallback.md` | 64.7 | electron-builder |

## P3（低）— 正则误报 / 量化数据，无需版本复审 — 18 条

| 条目 | 命中的「版本串」实为 |
|---|---|
| `pitfalls/agent-loop-follow-progress-not-liveness.md` | 9.5（同错阈值） |
| `pitfalls/backlog-records-rot-verify-before-dispatch.md` | 9.0（计数） |
| `pitfalls/bare-wait-deadlocks-on-long-lived-children.md` | 0.5（时长） |
| `pitfalls/dynamic-workflow-agent-identity-and-gates.md` | 112.1、3.55/5.40（tokens、对比度） |
| `pitfalls/figure-placement-and-legend-occlusion.md` | 0.5 / 0.20 / 6.1（尺寸阈值） |
| `pitfalls/kb-entry-source-scope-is-the-boundary.md` | 4.28 / 3.8 / 5.3（比例） |
| `pitfalls/ooxml-layout-attributes-silently-ignored.md` | 2.97 / 1.05 / 70.87（尺寸） |
| `pitfalls/periodically-overwritten-state-file-cannot-be-hand-edited.md` | 46.634 / 51.634（PID） |
| `pitfalls/same-config-key-different-semantics-per-step-type.md` | 121.01… （时长） |
| `pitfalls/verification-script-ua-can-fake-a-config-failure.md` | 3.13 / 8.4（比例） |
| `tools/cnb-npc-dispatch-essentials.md` | 0.125（换算） |
| `tools/github-china-network-workarounds.md` | 140.82（curl 版本，弱） |
| `tools/github-git-data-api-push-without-git-transport.md` | 1.1（序号） |
| `tools/mathmodel-paper-visual-baseline.md` | 10.5 / 9.5（字号/版式） |
| `workflow/ai-disclosure-consistency.md` | 3.11（计数） |
| `workflow/numeric-claims-need-baseline-and-subject.md` | 1.5 / 5.1 / 22.13（数值） |
| `workflow/openclaw-real-upstream-fire.md` | 26.9（版本，弱） |
| `workflow/pre-delivery-text-selfcheck.md` | 57.2682（CV） |
| `workflow/taskbook-write-the-property-not-your-guessed-mechanism.md` | 2.3（版本，弱） |

> 注：上表 `tools/github-china-network-workarounds.md`、`workflow/openclaw-real-upstream-fire.md`、
> `workflow/taskbook-...md` 三条命中的可能是真实版本号，但影响面小，暂列低位。

---

## 作用域复审（P1-2）

判据（沿用）：**只有当 `description` 里出现具体的数值上限 / 错误码 / 返回结构 / 字段名，
却没有点名它属于哪个网关 / 模型 / 平台时，才需要标 `【作用域=…】`**；通用规律**不标**。

### 已点名作用域（正例，无需动作）

`llm-context-window-is-input-plus-output`（AstrBot tdp + qwen3.8-27b）、
`quota-exhausted-vs-banned-distinguish`（New API）、
`kb-entry-source-scope-is-the-boundary`、`defect-localization-methodology`。

### 引用了具体产品+版本、但结论为通用规律（按判据**不标**，已评估）

| 条目 | source 中的产品/版本 | 判定 |
|---|---|---|
| `pitfalls/config-field-name-is-not-spec-read-consuming-code.md` | AstrBot v4.27.4 | 通用规律（相似字段各管一事），不标 |
| `pitfalls/persisting-files-also-requires-exempting-cleanup.md` | AstrBot v4.27.4 | 通用规律（持久化须连清理一起放开），不标 |
| `pitfalls/third-party-db-columns-typed-by-reading-code.md` | AstrBot v4.27.4 | 通用规律（列类型由读它的代码决定），不标 |
| `pitfalls/verify-with-real-pipeline-and-readonly-probes.md` | AstrBot v4.27.4 | 通用方法（用应用自己的类验证），不标 |
| `pitfalls/p256-ecdsa-handrolled-pitfalls.md` | 纯标准库 / 规范 | 规范事实（a=-3、ES256 裸 r‖s），不标 |
| `pitfalls/generated-credential-files-default-permissive.md` | 通用 | 通用规律（umask 644），不标 |
| `pitfalls/bind-mount-owner-must-match-container-uid.md` | 通用 | 通用规律（属主由宿主决定），不标 |
| `pitfalls/dont-handroll-spec-encoders-use-libraries-plus-fallback.md` | segno 1.3 | 通用规律（强规范别自造），不标 |

> 结论：现状**不需要**大规模补标（本库多数是通用规律，硬贴标签正是任务书警告的误用）。
> 缺口在**机制**：`hooks/kb_validate.py` 已加 `[scope]` 规则——description 引用强版本/模型签名
> 却未点名作用域即报错；写入流程（`skill/SKILL.md` 第 6 步）会跑校验器。模板要求见 `schema/entry.md`。
