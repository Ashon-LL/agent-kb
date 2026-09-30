---
name: env-claims-must-be-reverified
description: 环境变更与验证结论必须命令实测复核，不信陈述与"通过"字样
type: pitfall
source: apishow + default（2026-08-22 私钥 ACL 实锤；429 限流实测）
date: 2026-09-14
---

**经验**：收到"已锁定/已迁移/已收紧/已切换"类环境变更陈述（用户说的或自己做的），用实际命令独立核验后才算完成：icacls 看 ACL、`ssh -G` 看解析、`git config --list` 看 helper。尤其 SSH 私钥与凭据文件——实测曾发现"已收紧"的私钥仍有孤立 SID 与组持修改权。

同理，API 验证不信"通过"字样：429 是**按模型**限流，换 Key 不换模型照样 429，以真实响应体为准。

**How to apply**：任何权限/凭据/配置变更任务的最后一步固定为回显核验命令输出。
