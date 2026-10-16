---
name: importing-historical-runs-into-mh-agent-open
description: 把历史工作流/产物导进 MH-Agent-Open 的三个必须核对点——① 先确认"当前运行形态"（桌面数据根 %USERPROFILE%\.MHAgentOpen vs 容器数据根 /data），导错地方等于没导；② 文件必须落在**工作流契约声明的位置**（工作区根），不是归档目录结构；③ 校验手段 = 读 workflow_steps.output_files 逐个 test -f
type: workflow
source: MH-Agent-Open（2026-10-15 云环境实弹产物回迁，两次踩坑后总结）
date: 2026-10-15
verified: 2026-10-15
topic: cnb, database
---

**经验**：把云端/历史的工作流搬进用户正在用的软件，**不是"把文件拷过去"那么简单**，
三个点必须逐个核对，漏一个用户就"看不到"。

## ① 先确认当前运行形态（最容易白干的一步）

同一套软件有两种数据根，**导错等于没导**：

| 形态 | 数据根 | 判据 |
|---|---|---|
| 桌面形态（Tauri 壳） | `%USERPROFILE%\.MHAgentOpen` | 有桌面壳进程 / 双击 exe 启动 |
| **容器形态**（Docker） | **`/data`**（卷 `mh-data`） | `docker ps` 有 `mh-agent` 容器 |

⇒ **导入前先问/先查**：`docker ps` 里有容器吗？有 ⇒ 目标是从 `/data` 进，不是 `~/.MHAgentOpen`。
（实测教训：先导进了桌面根，用户"根本没看到"——他早转容器了。）

## ② 文件必须落在**契约声明的位置**

工作区的产物位置由**模板契约**决定（`<scene>/workflows/*.json` 的 `output_files`），
**不是**归档时那套 `products/`、`refine/`、`paper/` 目录结构。
⇒ 归档目录照原样拷进去，UI 的产物面板会**全部显示缺件**。

**实测**：AIG-QA 那条 19 个声明产物里 11 个"缺失"，一查全在 `products/` 和 `refine/` 子目录里
⇒ 补拷到工作区根后 **19/19 齐**。（⛔ 用 `cp -n` 复制不移动，保留原归档结构。）

## ③ 校验手段：按契约逐个 test -f（别凭"我看着文件都在"）

```python
import sqlite3, json, pathlib
WID = "<workflow_id>"
WS = pathlib.Path("/data/workspaces") / WID
con = sqlite3.connect("/data/db/mhagent.db")
for skill, of in con.execute("select skill_name, output_files from workflow_steps"
                             " where workflow_id=? order by step_order", (WID,)):
    for f in json.loads(of or "[]"):
        if not (WS / f).exists():
            print("MISSING", skill, f)
```

**判据读法**：缺失分两类，处置完全不同——
- **文件在别处** ⇒ 补到契约位置（真能修）；
- **文件本来就不存在**（旧环境回收丢的）⇒ **如实报告，⛔ 不要造空壳**（造假产物比缺件更糟）。

## ④ 建 DB 记录（否则界面根本不列这条工作流）

产物进目录只解决"产物面板"，**工作流列表**读的是 `workflows` 表：
需 `insert into workflows(...)` + `workflow_steps(...)`（步骤从模板 JSON 展开 + 末步 `capability-refine`）。
`current_step` 取末步 skill 名；`workspace_dir` 写**当前形态**的绝对路径。

关联 [[cnb-secret-repo-imports]]（同一体系的数据落点纪律）。
