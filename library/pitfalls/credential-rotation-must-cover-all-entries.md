---
name: credential-rotation-must-cover-all-entries
description: git 报凭据失效但远端明明在=凭据管理器里有**抢先命中的 host 级条目**；⛔ 但"擦掉所有条目"是过宽建议——有些条目是别的仓库在用的合法凭据，正确做法是按库隔离（URL 级 helper），并把 CLI token 提到链首
type: pitfall
source: mh-agent-open（2026-09-15 CNB 令牌轮换实锤）；APIShow（2026-09-21 同一坑二次踩：host 级条目抢走 APIShow 的推送，而那条恰是 mh-agent-open 的合法专用 key）
date: 2026-09-21
verified: 2026-09-15
topic: git, security
---

**经验**：git 报凭据失效/仓库不存在、但仓库明明还在时，第一嫌疑是**凭据链里有个更早的 host 级条目抢先命中**（`credential.useHttpPath` 默认 false ⇒ 优先 host 级查找；path 级新条目**完全不参与** host 级查找，救不了这个场景）。

**⚠️ 但"必须轮掉所有条目"是过宽的建议，会导致误删**（2026-09-21 修正）：凭据管理器里的条目**可能属于不同仓库、持有互不相同且各自合法的凭据**。本例中那条"抢先命中的 host 级条目"经实测**确实是有效的**——它是限定到 `mh-agent-open` 的仓库级 key（对该库 API 与 git 都有权限），**删了那个库就推不了**。所以正确做法不是"一律清除"，而是**按库隔离**：给目标库配 URL 级 helper 把它顶掉，其余库的条目原样保留。

**Why**：2026-09-15 首次实锤：CNB 令牌轮换只更新了 path 级与 `~/.cnb/token`，GCM 里更早的 host 级条目（旧 token）没擦 → 命中旧 token → `remote: Your Credentials have Expired` + 400。当时把它误判成"远端没有新分支"，差点漏掉 NPC 已交付的事实。

**2026-09-21 二次踩（同一坑，且新增两层认知）**：`git push` 报 `Repository Not Found`，而仓库在、凭据也在。逐步取证：

- `credential.helper manager`（GCM）在**链首**，Windows 凭据管理器里有 host 级条目 `git:https://cnb.cool`（**无 path**）持有 **27 字符**凭据；CLI 的 `~/.cnb/token` 是 **94 字符**。
- 用 94 字符直打 CNB git 端点 → **200**；用 27 字符打 `APIShow` → **404**。⇒ 仓库与正确凭据都没问题，纯粹是 git 用错了。
- ⚠️ **私有仓库鉴权失败的表现是 `Repository Not Found`（不是 401）**——极具误导性，容易去查仓库是否被删/改名。
- 修法（实测闭环，两个形态都要配）：先 `helper ""` 清空该库默认 helper，**再**挂专用 helper；`.git` 后缀形态要**单独再配一次**，否则 `apigogo/X.git` 仍走旧路径：
  ```
  git config --global "credential.https://cnb.cool/<owner>/<repo>.helper" ""
  git config --global --add "credential.https://cnb.cool/<owner>/<repo>.helper" '!<...cnb.cmd> git-credential'
  # 再对 <owner>/<repo>.git 重复上面两行
  ```

**How to apply**：
1. 症状 = "Your Credentials have Expired" / 400 / ls-remote 空输出 / **git 突然弹 GCM 凭据窗口**——先查凭据链路再下结论，别急着信"远端没有"。
2. ⛔ **验证工具本身要先验证**：Git Bash 裸跑 `cmdkey /list` 会被 MSYS 路径转换破坏（`/list` 被当路径）→ 假"查无条目"（20260915 实锤：凭此假阴性错怪 `git credential approve` 没落盘，事后 `cmd //c "cmdkey /list"` 证实 approve 成功、条目正常持有新 token）。探测各条目实际持有哪些 token：`printf "protocol=https\nhost=cnb.cool\npath=<owner>/<repo>\n\n" | git credential fill`（掩码输出）。
3. **根治（20260915 实测闭环，手册同日修订为按库作用域）**：给**本库**配 URL 级专用凭据助手，直接读该平台 CLI 自己的 token 文件（cnb = `~/.cnb/token` 的 JSON `access_token`），GCM 出局、零弹窗。⛔ 别配成 cnb.cool 全域 helper——本机 `credential.https://cnb.cool.useHttpPath true` 是按库隔离设计，全域配置会把一个库的 token 塞给其他库：
   ```
   git config --global credential.https://cnb.cool/<owner>/<repo>.helper ""          # 清空该库的默认 helper
   git config --global --add credential.https://cnb.cool/<owner>/<repo>.helper '!sh "C:/Users/<user>/.cnb/git-cred.sh"'
   ```
   助手脚本内容（不含 token，查询时现读）：`echo username=cnb; echo password=$(python -c "...读 token 文件...")`
4. 验证必须**禁弹窗**跑：`GIT_TERMINAL_PROMPT=0 git fetch <remote> branch` 静默通过才算修好；弹窗=没修好。
5. 令牌轮换时只需更新 token 文件一处，git 与 CLI 共用。
6. **反向定位杂散条目（20260915 agent-guard 实锤）**：怀疑某库 git 静默用旧 token 时——①枚举凭据管理器：`cmdkey //list > $TEMP/ck.txt` 后**必须 `iconv -f GBK -t UTF-8`**（中文版 Windows 控制台输出是 GBK，按 UTF-16/UTF-8 解会得到 0 行假"查无条目"）；②逐 path 探测谁供给什么：`printf "protocol=https\nhost=<域名>\npath=<owner>/<repo>\n\n" | git credential fill` 管道进 python 只打 `sha256(v)[:16]`（明文不落屏）。同域各库的 path 条目可能持有**互不相同**的 token。
7. **定性前先看平台密钥清单（同日教训，防误判）**：哈希比对发现两处分叉只是"线索"，不是"欠账"——平台按库发的**专用 key 本来就每库一把**（如 CNB 设置→访问密钥的"仅应用于 <owner>/<repo>"），git 走 GCM 里该库专属条目可能恰是现行合法凭据。下结论前去托管平台的密钥列表核对：哪把在用、哪把已删、scope 是什么；已删除的才算旧。CLI token 文件一次只装一把库级 key，跨库调用 API 的正确姿势 = `CNB_TOKEN` 环境变量注入目标库的 key（可从目标库的 path 级凭据条目 `git credential fill` 现读，明文不落屏），⛔ 别把目标库的 key 换进 CLI 默认 token 文件——那会污染默认身份、下次轮到默认库反而被打反；git 凭据走各库 path 级条目互不干扰。
8. **⛔「凭据失效」≠「凭据废弃」——先测它的能力边界，别急着删**（2026-09-21）：本例那条"抢先命中"的 27 字符凭据经实测是**有效的**，只是**权限范围受限**：`GET /user` 返 `403 Missing scopes: account-profile:r`（**明确说这是 scope 问题，不是凭据无效**），而它对自己那个库的 API 与 git 都返 200。⇒ **401/403 只说明"这条凭据对你这个请求没权限"，不说明它废了**。删之前必须逐库测一遍它到底能访问什么，否则会**删掉别的仓库正在用的凭据**。
9. **⭐ 验证权限必须做对照组**（2026-09-21 实锤，我第一版判据错了）：我最初用「无效凭据测 git 端点返 200」推断"该凭据有权限"，**结论是错的**——那 5 个库里有两个是 **Public**，**无凭据也返 200**。加上对照组才分辨出来：
   ```
   # 同端点三种身份各测一次，对比才有意义
   凭据有效性 = f(有目标凭据, 无效凭据, 无凭据)
   # 无凭据也 200 ⇒ 公开资源，与凭据无关
   # 无效凭据 404 / 无凭据 401 / 目标凭据 200 ⇒ 该凭据确有权限
   ```
   单看"目标凭据返 200"会把**公开库**误当成"凭据有权限"，进而误判凭据的作用范围。
10. **改动前先枚举"这条链上谁排在前面"**：`git config --get-regexp "^credential"` 拿到完整顺序。URL 级 helper 是**插入链中**，若全局 helper 仍排更前，加了也没用——**必须先把该库的 helper 清空**（`helper ""`），否则会出现"配置改了但行为没变"。
11. **推送后独立核实远端，别只信本地输出**（2026-09-21）：`git push` 本地打印成功不等于远端收到。用 `git ls-remote <remote> <branch>` 取远端 sha 与本地 `git rev-parse HEAD` 比对。（本例对应用户曾质疑我"之前报的推送成功"，确实存在只信本地输出的问题。）

关联 [[credential-helper-empty-value-blocks-git-fetch]]。
