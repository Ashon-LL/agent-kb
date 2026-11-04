---
name: bilibili-upload-flow
description: B站创作中心投稿流程与字段语义——视频用首个 input[type=file] 直传；创作声明是「含AI生成内容」单选 + 「内容为自制」独立勾选；封面用 hidden input[accept*=image] 上传后落在 archive.biliimg.com；合集需 Lv2；投稿后状态=转码完成/审核中，审核期列表显示「仅自己可见」并通过后自动公开
type: tool
source: 2026-11-02 《10年人间》EP01 投稿实测（ego-browser）
date: 2026-11-02
verified: 2026-11-02
topic: delivery
---

**经验**：

1. 入口：`https://member.bilibili.com/platform/upload/video/frame`（创作中心 → 投稿 → 视频投稿）。已登录时直接进表单。
2. 上传视频：页面有多个 `input[type=file]`，选第一个 accept 含 `.mp4/.mov` 的，`setInputFiles` 后等 `input[placeholder*="标题"]` 出现；20MB / 163s 约 10–20s 完成，显示「上传完成」。
3. 字段语义：
   - **标题**：`input[placeholder="请输入稿件标题"]`，上限 80 字。
   - **创作声明**：自定义下拉（`li.bcc-option`），选项为 `内容无需标注 / 含AI生成内容 / 含虚构演绎内容 / 内容含营销信息 / 个人观点，仅供参考 / 内容为转载` 单选；另有一个**独立的**「内容为自制：未经作者允许，禁止转载」可勾选项（`div.auth-content`，点一下出现对勾），它不进输入框的值。AI 辅助制作应选「含AI生成内容」+ 勾「内容为自制」。
   - **分区**：自定义选择器，只显示父级（如「知识」）也能提交成功；不需要强行找二级分区。
   - **标签**：input + Enter 创建；默认可能带一批无关标签（本次是李准基/爱情/影视剪辑），必须逐个人工清掉再填。
   - **简介**：Quill contenteditable，用 `page.keyboard.paste()` 粘贴多段文字；上限 2000 字。
   - **封面**：点「添加封面」开弹窗；真正的上传控件是 hidden `input[type=file][accept*="image"]`，直接 `setInputFiles` 即可；完成后表单里出现 `.cover-img`，背景是 `https://archive.biliimg.com/bfs/archive/<hash>.jpg`。有 4:3 / 16:9 双比例，勾「双比例同步改动」可只传一张。
   - **合集**：未到 Lv2 时只显示「开通合集功能需满足权益中心等级达Lv2」，没有可操作控件，不能提前建。
4. 提交：按钮是 `span.submit-add`（文字「立即投稿」）。**若创作声明的下拉还开着，点击会被下拉吃掉**——先 `document.body.click()` 关掉再点。
5. 提交成功后页面停在「稿件投递成功」，地址仍是 `upload/frame`，不会跳转；去 `member.bilibili.com/platform/upload-manager/article` 看稿件。列表状态先「转码完成 / 审核中」，此时可见性显示「仅自己可见」；**审核通过后自动转公开**。点「查询进度」可看转码分档（360/480/720/1080 均已完成）与审核「进行中」。

**Why**：B站投稿页大量自定义组件（不是原生 select/radio），按「找 select/radio」的常规写法会全部落空；创作声明与「自制」是两个独立控件，漏勾「自制」等于没声明；审核期的「仅自己可见」不是设置错误，别去改可见范围。

**How to apply**：投稿前核对标题/分区/标签/简介/封面五项；标签默认值必须清空重填；提交前关闭所有下拉；提交后到稿件管理核对「转码完成/审核中」，不要用列表的「仅自己可见」判断失败。相关：[[ego-browser-form-automation-dialogs-and-cache]]。
