---
name: video-terminal-failure-needs-upstream-error-before-retry
description: 视频任务返回终态 failed 时，先保留 task_id 与 status.json、查上游原始错误码，再决定改提示词；不要把 MCP schema 修复或同一提示词重提当根因验证，更不要自动连续创建付费任务
type: pitfall
source: 2026-11-07 APIShow MiniMax H3「绝望之舞」10 秒视频两次提交失败
date: 2026-11-07
verified: 2026-11-07
topic: mcp, verification
---

**经验**：视频任务进入终态 `failed` 后，优先记录 `task_id`、`created_at`/`updated_at`、`credit_actual`、`files`、成片 URL 状态与 `status.json` 全文；若只有网关写的 `upstream video task failed` 而没有上游错误码，就不能断定是提示词、审核、模型故障还是账号问题。**修好 MCP schema 只验证了「字段能进草稿」，不能解释「上游生成失败」**；要改提示词，应先取得上游原始错误或经用户明确同意做一次最小对照，且每次新任务都单独确认。

**Why**：2026-11-07 两次提交同一 `minimax-video-h3` / 10 秒 / 9:16 / 768P 任务，分别在 20 秒和 19 秒后返回终态失败：`error=upstream video task failed`、`credit_actual=0`、`files=[]`、content URL 404。第一次时 `apishow_prepare_video` 尚未暴露 `negative_prompt`，确认阶段才补传；用户部署 `2026.11.7.1100` 后第二次在 prepare 阶段就传入并确认 `negative_prompt` 原样回显/落库，但失败仍完全一致。MiniMax 官方文档把 `1026 / video description contains sensitive content / HTTP 422` 列为可能的上游错误，第三方实测提示具名 IP 容易触发输入审核；可是网关的 `status.json` 没保留 `request_id` 或 1026，因此最多只能把审核列为高概率假设，不能写成已证实根因。两次失败都没有 `credit_actual` 扣费，但仍不应无限重提。

**2026-11-07 改词对照补记**：用户明确同意按「具名 IP / 高风险语义疑似触发审核」做一次对照后，把具名电影、角色、歌曲、艺人及「崩溃/癫狂/失控」等词全部移除，负面提示词也缩成纯画质约束；同模型、10 秒、9:16、768P、同步音频不变。第三次 `vt_bd76b1822404c4d4ca0c1261061e8f68` 在约 2 分 41 秒后 `completed`，`credit_actual=144.29`，产出 1,848,354 字节 MP4，本地 `ffprobe` 为 10.125 秒、768×1344、24 fps、H.264 + AAC 立体声。该对照令「提示词内容触发上游拒绝」成为**强相关但无原始错误码的推断**；不能排除同时间段上游状态变化，更不能把成功反推成已取得 1026 日志。结论仍应表述为「改词后成功」，不是「已证明审核根因」。

**2026-11-07 参考图与音频补记**：后续返修把成功稿的人物/服装改成白人少女与白底青花瓷旗袍，要求不写高风险情绪词、不用歌曲。直接把含具名角色的小丑台阶图放进 `reference_images` 后，`mode` 从 `text-to-video` 变成 `image-to-video`，任务 `vt_cd70d134c37fa2bfea9189e708f3f120` 约 16 秒后终态失败、`credit_actual=0`；用户选择去掉参考图、把同样的台阶舞姿写成纯文字后，`vt_5b99f0690cd84d49a70168439f8d2f7e` 成功（`credit_actual=144.29`，2,252,938 字节）。这说明参考图不仅改变模式，还可能引入素材审核或 URL 链路问题；**同类返修优先维持已成功的链路，只逐项改文字**。另外该网关对 MiniMax H3 明确警告 `该模型音频固定开启，已忽略 enable_audio=false`；服务端原片仍带 AAC，用户要后期配乐时可在下载后用 `ffmpeg -map 0:v:0 -c:v copy -an` 生成无声副本，不要声称工具层已关掉音频。

**2026-11-07 用户肖像参考图补记**：同一 `image-to-video` 链路并非必然失败。用户明确授权上传一张真人照片、要求保留脸与整套服装后，通过 `POST /video-api/assets` 取得约 1 小时有效、随机 token 的临时素材 URL，GET 校验字节与本地 SHA-256 一致，再放进 `reference_images`；`vt_b711eaa3fabb3d8444d657cff764b0ab` 成功，`credit_actual=144.29`，2,427,076 字节。因此小丑参考图失败更可能与素材内容/公网 URL 有关，而不是「只要传参考图就失败」。`watch_video` 对该任务在 180 秒工具层超时后，直接 GET `status.json` 发现已 `completed`；**轮询超时不等于任务失败，必须先查终态再决定是否重提**。真人照片是对外发送内容，上传前要确认授权、临时 URL 有效期与隐私边界。

**2026-11-07 15 秒额度护栏补记**：把时长从 10 秒改到 15 秒后，`credit_estimate=214.35` 超过站点阈值 200，第一次 `apishow_confirm_video` 返回 `confirmation_required` 且未创建任务、未扣费；按用户已确认的同一估算补 `confirm=true` 后一次提交成功。`watch_video` 返回 `status=polling`、`terminal=false`、`timeout=true`，继续只读 GET `status.json` 约 7 分钟后得到 `completed`、`credit_actual=216.43`。**高额度草稿要预期二次布尔确认；`polling + timeout=true` 不是终态，绝不能据此重提任务**，应继续查状态 JSON 直到 `terminal=true`。

**How to apply**：
1. 终态失败先查 `status.json` 与 content URL，记录完整字段；网关若吞掉上游错误，明确写「根因未取证」。
2. 把候选原因分层：schema/参数传递、上游输入审核、账号/额度、上游服务故障、提示词中的具名 IP/敏感语义。用已有证据逐项排除，缺哪层证据就补哪层。
3. 修复了 schema 后，用免费 `prepare_video` 验证字段回显即可；**不要把它等同于生成链路已修复**。同一提示词原样重提只能证明可复现，不能定位原因。
4. 若怀疑审核，改写时先显式删掉具名电影、角色、歌曲、艺人名及「崩溃/癫狂/失控」等高风险语义，只保留镜头、动作与节奏描述；但仍需用户看过新提示词并确认后才建新的付费任务。
5. 参考 MiniMax 官方 CLI 指南：终态 `failed/cancelled/expired` 应报告 taskId、状态与错误，创建另一个付费任务前要求用户批准；敏感内容、限流、5xx 也不要自动跨区重试。
6. 模型/端点/网关版本变更时重查错误码与规格，不要把特定版本的文案当永久结论。

> ⏰ 时效状态（2026-11-07 记录，**已复核源码、未复核生产日志**）：`https://api.apigogo.cyou/mcp` 的两次失败任务 `status.json` 都只返回 `upstream video task failed`，未见 `request_id`、1026 或 HTTP 状态码。本机 APIShow 源码副本 `internal/videotask/manager.go:389-390` 在上游 `status=failed` 时固定写入该文案；`internal/upstream/video.go:115-133` 只解析 `Status`/`URLs`/`Credit`，`Task` 结构也只有通用 `Error`，故网关本身不保存上游原始错误。后续四季任务已实际收到 `1026: input new_sensitive, input text sensitive`，见 [[negative-prompt-is-also-moderated]]。
> ⚠️ 用前必须实测：对失败 task 调 `apishow_watch_video(task_id)`，GET `status_json_url`，并在生产容器 `/data/video-tasks` 与上游网关日志按 task_id / upstream_id 查原始响应；不要仅凭固定文案判定 1026。

关联 [[negative-prompt-is-also-moderated]]、[[mcp-instructions-may-name-undeclared-tool-fields]]、[[defect-localization-methodology]]、[[no-assertion-without-measurement]]。
