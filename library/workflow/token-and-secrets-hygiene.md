---
name: token-and-secrets-hygiene
description: 凭据卫生：token 不内联命令行、公开内容零站点/密钥/逆向痕迹、真实域名在文档记忆里一律占位符化
type: workflow
source: ailika + mh-agent-open（用户多次强调）
date: 2026-09-14
verified: 2026-09-14
topic: security
---

**经验**：

1. **token 永远不上命令行/URL**（每次工具调用是新 shell，别图省事内联 `TOKEN=xxx`）：一次配置持久存储——工具自带凭据文件（如 `~/.cnb/token` JSON）或系统凭据管理器（`git credential approve` → GCM），之后裸命令直接可用。
2. **安装包/仓库/公开内容零敏感**：不含 .db、真实站点域名、密钥、源项目与逆向表述；Git 历史含敏感必须 `git filter-repo --replace-text` 重写 + force push，不能只删当前文件；发布前检查（安装包内容清单、`git log -S`、文档扫描）。
3. **记忆/文档里的上游域名与 key 前缀一律占位符**（`<上游站点>`、`<key前缀>`），换站只沉淀"协议 × 能力"结论；需复现时从 DB 取真值——注意管理 API 返回的是**掩码 key**，别把掩码导致的"未认证"误判成 key 失效。
