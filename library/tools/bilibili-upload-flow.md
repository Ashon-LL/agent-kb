---
name: bilibili-upload-flow
description: B站创作中心投稿流程与字段语义——视频用首个 input[type=file] 直传；创作声明是「含AI生成内容」单选 + 「内容为自制」独立勾选；封面用 hidden input[accept*=image] 上传后落在 archive.biliimg.com；合集需 Lv2；投稿后状态=转码完成/审核中，审核期列表显示「仅自己可见」并通过后自动公开；标题会被上传文件名覆盖，需编辑页 page.fill 重填
type: tool
source: 2026-11-02 《10年人间》EP01 投稿实测（ego-browser）；2026-11-09 EP06 补标题被文件名覆盖
date: 2026-11-02
verified: 2026-11-09
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

**2026-11-06 EP03 补充（ego-browser 实测，372 MB 视频）**：
1. 上传控件是 **hidden `input[type=file]`**，`page.waitForSelector` 默认等 visible 会超时 → 必须 `{ state: "attached" }`。
2. **直接 `page.setInputFiles()` 不会触发上传**（文件挂上了但上传器没反应，页面始终停在「点击上传或将视频拖拽到此区域」）。正确做法：先真实点击 dropzone 打开原生 file chooser，再 `chooser.setFiles()`：
   ```js
   const p = page.waitForFileChooser({ timeout: 10000 });
   await page.mouse.click(box.x, box.y);   // dropzone 中心坐标
   const ch = await p;
   await ch.setFiles(VIDEO);
   ```
   封面（`添加封面` → `上传封面`）同理；`input[type=file][accept*="image"]` 有 3 个同名 accept，直接 setInputFiles 也不触发。
3. 上传进度看页面文本 `已经上传：X.XMB/YYY.YMB`；372 MB 约 4 分钟（~1.5 MB/s）。标题输入框在上传开始后就可用（自动填文件名），不用等上传完。
   - **标题坑（2026-11-09 实测）**：上传完成后标题框会自动填成文件名（如 `EP06_谁在种地_1080p`）。用原生 setter + `input` 事件只改了 DOM value，Vue 内部状态没更新，投递后 API 的 title 仍是文件名。修法：进编辑页 `upload/video/frame?type=edit&bvid=<BV>`，用浏览器自动化的 `page.fill()`（真实输入事件）重填标题，再点「立即投稿」；重提后到稿件管理核对标题。
4. **默认标签会在页面重载后回来**：上传前清掉的「影视剪辑/爱情」等推荐标签，如果中途 reload 会恢复。提交前必须再核对一次标签。
5. 改稿：稿件管理 → 每行的 `编辑`（anchor，无 href）→ 打开 `upload/video/frame?type=edit&bvid=<BV>`，表单数据（标题/分区/标签/简介/封面/视频）全部保留，改完点 `立即投稿` 重新走审核。
6. 稿件行的 anchor 顺序：视频链接（含 BV 号）、标题链接、`编辑`、`数据`。BV 号从编辑 URL 或视频链接里取。

**2026-11-06 EP03 v2 补充（CC 字幕上传）**：
1. 页面路径：创作中心 → 内容管理 → 字幕管理（`/platform/upload-manager/audience-zimu`）→ 点视频行 → `＋ 添加语言` → 选「中文」→ `添加字幕` 跳到 `/platform/zimu/my-zimu/zimu-editor?aid=<aid>&cid=<cid>`，编辑器在跨域 iframe（`www.bilibili.com/web/player/index.html#/editor`）里，**页面上点「提交」经常无反应**（下拉/按钮被 iframe 与视口宽度卡住，模拟点击不生效）。
2. 可靠做法：直接调 API（权限校验 `GET api.bilibili.com/x/v2/dm/subtitle/permission?type=1&oid=<cid>&bvid=<BV>` 返回 code 0 即可投稿）：
   ```
   POST https://api.bilibili.com/x/v2/dm/subtitle/draft/save?x-bili-device-req-json=...&x-bili-locale-json=...
   body(x-www-form-urlencoded):
     type=1, oid=<cid>, lan=zh, submit=true, sign=false, bvid=<BV>, csrf=<bili_jct>,
     data={"font_size":0.4,"font_color":"#FFFFFF","background_alpha":0.5,
           "background_color":"#9C27B0","stroke":"none",
           "body":[{"from":秒,"to":秒,"location":2,"content":"字幕文本"}]}
   ```
   语言代码表：`subtitle_lan_v3.json`（中文=zh、繁体=zh-Hant、英语=en…）。`submit=true` 即送审，`false` 为草稿。
3. 验证：`GET api.bilibili.com/x/player/v2?aid=<aid>&cid=<cid>` 的 `data.subtitle.subtitles` 出现 `lan=zh` 即成功；字幕文件 `subtitle_url` 可取回 JSON 核对内容与时间轴。
4. 相关接口：`x/v2/dm/subtitle/assit/audit`（送审状态）、`del`（删除）、`lock`（锁定）、`show`（详情）。

5. **评论可以通过 API 直接发（含 @ 提及）**：
   `POST https://api.bilibili.com/x/v2/reply/add?x-bili-device-req-json=...&x-bili-locale-json=...`
   body（x-www-form-urlencoded）：`oid=<aid>&type=1&message=<文本>&plat=1&ordering=heat&csrf=<bili_jct>&jsonp=jsonp`；
   成功返回 `{"code":0,...,"success_toast":"发送成功","data":{"rpid":...}}`。
   `message` 里直接写 `@昵称` 即可（不需要先查 mid）；验证见 `GET /x/v2/reply?type=1&oid=<aid>&ps=10&order=heat`。
   用途：给自家视频做「@ AI 机器人来评论」的触发（机器人按 @ 自己的昵称响应，而不是按简介关键词）。

**2026-11-08 EP04 补充（ego-browser 实测）**：
1. **字幕/评论等需登录的 API 必须 api.bilibili.com 同源**：从 member.bilibili.com 或 www.bilibili.com 用 `page.fetch` 调 `api.bilibili.com/x/v2/dm/subtitle/*`、`x/v2/reply/add` 会报 `code:-101 账号未登录`（跨源不带 SameSite cookie；公开的 `x/web-interface/view` 却能过，极易误判已登录）。修法：先 `page.goto("https://api.bilibili.com/x/web-interface/nav")`（顶层 GET 带 cookie，页面显示 isLogin:true），此后 `page.fetch` api.bilibili.com 即同源带登录态。
2. **封面 16:9 同步确认**：封面制作弹窗里上传图（hidden image input 可 `page.setInputFiles` 加载，但只初始化 4:3）→ 点「完成」会弹「检测到个人空间封面(16:9)未修改，是否将 4:3 同步到 16:9」→ 点「确认同步」→ **再点一次「完成」**才落到主表单（背景变 `archive.biliimg.com/bfs/archive/<hash>.jpg`）。漏掉第二次完成会以为封面没传上。
3. **「开启通知」说明弹窗挡路**：投稿页有个 bcc-dialog「开启后视频上传完成第一时间通知」，里面「禁止/允许」是**示意图**（点了没用），真按钮是底部蓝色「知道了」；它盖在封面弹窗上，先 DOM 点「知道了」关掉才能操作封面。
4. 触发评论 `reply/add` 的 `message` 直接写 `@昵称` 即可召唤 DSH 机器人；评论以账号本人昵称发出（本轮「寻梦省兰」），rpid 返回即成功，`x/v2/reply?type=1&oid=<aid>` 可回看。

**2026-11-08 EP04 扩大采集补充**：
1. **单条评论 @ 人数上限**：实测 10 个 @ 能过、17 个报 `code 12013 at人数过多`，上限约 10–15。要 @ 大量账号就分多条、每批 ≤10（本轮 67 账号分 7 条均 code 0 无风控）。
2. **识别 DSH 机器人要看评论内容，不能只按昵称**：很多机器人名字不带鱼（呼啊hu/kujirachan/蛮子程程），很多带鱼名的是人类玩梗。真机器人在评论里自认「本鱼/我是大肥鱼AI/作为一只在B站自己刷视频的AI」、提「主人」、分析视频数据（百分比/源插件/npm）、自述被 DSH 教程养出来。
3. **找机器人扎堆处**：搜「大肥鱼」→ DSH 现象复盘/养鱼教程类视频（如鱼灾复盘、DeepSeek Harness 教程）评论区机器人最密集；`x/v2/reply?type=1&oid=<aid>&ps=20&pn=N&sort=2` 翻页抓评论全文（含楼中楼 r.replies），登录态下每页可达 20+ 条。

**2026-11-08 EP05 发布补充（ego-browser 实测）**：
1. **浏览器级通知权限气泡**：点掉 bcc-dialog「知道了」后会触发 Chrome 原生通知权限气泡，ego 报 stopForUserControl 交还控制权。修法：`takeOverTaskSpace(spaceId)` 接管 → `page.cdp("Browser.setPermission",{permission:{name:"notifications"},setting:"denied",origin:"https://member.bilibili.com"})` 拒绝即消除气泡 → 继续。
2. **file chooser 后窗口最小化**：上传视频/封面打开原生文件选择器后浏览器窗口会最小化，截图报 minimized、trusted click 失效。`Browser.getWindowForTarget` 取 windowId → 若 minimized 先 `setWindowBounds{windowState:"normal"}` 再 `{windowState:"maximized"}`（minimized 不能直接 maximized，会报错）。
3. **Vue 自定义控件 DOM click 比真实点击稳**：创作声明 bcc-select 选项（`li.bcc-option`）、自制 `.auth-content`、分区 `.drop-list-v2-item[title="知识"]`（按 title 属性定位整行，不是文字节点）用 `el.dispatchEvent(new MouseEvent('click',{bubbles:true}))` 生效；真实 mouse.click 坐标点击这些组件有时落空。分区下拉跨 ego 进程会关闭，开+选要在同一脚本内。
4. **封面双比例同步**：勾「双比例同步改动」后上传 16:9 图，点「完成」（是 `div.button.submit` 不是 button，DOM click）直接落主表单 archive URL，不再弹「确认同步」二次确认。
5. **标签逐个回车**：清空默认芯片（`.label-item-v2-container svg.close` DOM click）后，focus 标签 input + `keyboard.type` + Enter 逐个加；首个标签偶尔漏（本轮「楼市」漏一次），加完核对数量补漏。
