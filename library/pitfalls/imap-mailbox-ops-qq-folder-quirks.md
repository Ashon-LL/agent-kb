---
name: imap-mailbox-ops-qq-folder-quirks
description: 用 IMAP 管 QQ 邮箱建夹/删夹/合并的真实坑：中文夹名服务端归一化会建出同名夹；删夹要求夹内邮件数为0而非仅标Deleted；COPY+标Deleted 不会让邮件离开收件箱，需客户端 EXPUNGE
type: pitfall
topic: methodology
source: APIShow 邮箱整理任务（2026-10-19 用户授权自动执行，QQ 邮箱 mail.qq.com）
date: 2026-10-19
verified: 2026-10-19
---

**场景**：通过 IMAP（`imaplib` + QQ 邮箱授权码）给一个 660 封的收件箱做分类归档，
并在此过程中建夹、合并夹、删夹。

**踩到的四个坑，每个都让"我以为做完了"和"实际做完"不一致**：

1. **中文夹名会被服务端归一化，可能建出"两个同名夹"**。
   我 `CREATE "其他文件夹/APIShow"` 返回 OK，但随后的 `LIST` 里出现了
   `APIShow&VEqLZg-` 和 `APIShow` 两个条目——QQ 把中文段按 modified UTF-7 自己编码，
   客户端传入的编码与它内部使用的编码不一致时，**它不会报错，而是另建一个**。
   ⇒ 建完夹必须 `LIST` 回读、解码、点数，不能只看 `CREATE` 的 OK。
2. **删夹要求"夹内邮件数为 0"，仅标 `\Deleted` 不算**。
   对还有邮件的夹发 `DELETE` 会返回 `NO`（不是报错，是拒绝）。
   ⇒ 删夹前要先 `EXPUNGE`（或客户端彻底删除）把夹清空；反过来，
   想"先标删除、让用户在客户端收尾"时，夹是删不掉的——这两件事会互相卡住。
3. **`COPY + STORE +FLAGS (\Deleted)` 不会让邮件离开收件箱**。
   这是最安全的 IMAP 移动方式（可回滚），但邮件仍留在 INBOX 里，
   用户看到的收件箱毫无变化。要真正空箱必须 `EXPUNGE`（物理删除）。
   ⇒ 动手前就跟用户说清楚"归档完你还要在客户端点一次彻底删除"，
   或者直接用 `MOVE`（若服务端支持，一步到位但不可回滚）。
4. **`/tmp` 在 Git Bash 与 Windows Python 之间不是同一个目录**（详见
   [[cross-env-file-handoff-must-use-native-mechanism]]）——传凭据时踩过一次。

**正确姿势**：
- 中文夹名往返：本地编码（连续非 ASCII 段整体 base64，ASCII 段原样，`/` 不转义）
  只用于**发送**；**接收侧一律用 `LIST` 返回的原始名**去 `SELECT`，不要本地重编码
  （我按名重编码后两个夹打不开，用原始编码名一开就成）。
- 合并文件夹：逐源夹 `COPY` → 目标夹，再对源夹 `STORE +FLAGS (\Deleted)` + `EXPUNGE`，
  然后 `DELETE`。**EXPUNGE 前必须逐封做指纹比对**（如 MD5 of
  `MESSAGE-ID+SUBJECT+DATE`），确认源夹邮件在目标夹都有副本——本次 327 封全有副本才动手。
- 分类规则按"顺序首次命中"判定，一封只归一个夹；匹配不到就留在 INBOX，
  不要硬塞进"其他"（真人往来混进垃圾夹比不整理更糟）。
- 无 From 地址的发件人（如 `Microsoft 帐户团队`）要按**显示名**判，
  别当退信——我一开始把 37 封安全通知误判成退信。

**Why**：IMAP 的标记模型（`\Deleted` 只是标记，`EXPUNGE` 才是删除）与
QQ 邮箱自建的夹名归一化，都会让"命令返回 OK"和"用户看到的效果"脱节；
邮箱是用户的生产数据，误删不可逆。

**How to apply**：写 IMAP 批处理脚本时，把「LIST 回读 → 逐夹点数 → 指纹比对 → 分批(50)
操作 → 总数守恒核对」做成固定流程；每轮只做一类操作并打印前后计数；
预演模式（无 `--apply`）必须**连 CREATE 都不做**，否则"预演"就已经改了邮箱。

关联 [[email-html-alignment-must-be-inline]]。
