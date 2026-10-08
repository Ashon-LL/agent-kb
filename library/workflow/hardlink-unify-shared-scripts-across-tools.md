---
name: hardlink-unify-shared-scripts-across-tools
description: 同一脚本部署到多个工具目录时用硬链接统一（留一个真相源，其余 os.link/mklink /H 同 inode）；git checkout/reset 会断链，校验器须按内容比对兜底；改配置指向不消除副本漂移
type: workflow
source: kb 体系 kb_core 五副本统一（2026-10-04）
date: 2026-10-04
verified: 2026-10-04
topic: windows, git
---

**经验**：一份脚本（hook/skill/命令）要在多个工具的目录里各放一份时，**留一个真相源、其余全部硬链接**（Python `os.link(源, 副本)`，先 `unlink` 再链；Windows 须同卷）。改一处全体生效，`stat` 看 `nlink` 数验证。动手前三步：

1. **摊开地图**：`find` 全机副本 + 逐个打开各工具 config 看**实际指向**——"配了 hooks 目录"≠"配置指向它"（本次四工具中三个指向仓库路径、一个指向 home 副本，home 另三份纯孤儿）。
2. **只换文件不动配置**：适配器 `sys.path.insert(自己目录)` 后 import 同名模块，所以**改配置指向换不掉本地副本的漂移**——必须让副本本身与真源同 inode；这样配置一个字都不用改（改运行中应用的扩展点路径会全废）。
3. **链接（junction/symlink）上永远不要做「先删后链」**：链接路径与真身指向同一 inode，`dst.unlink()` 删掉的就是真身的唯一链接——实测 2026-10-04：junction 两端同名操作把 SKILL.md 直接删没了。部署脚本必须先 `Path.resolve()` 判定两端是否同一实体，同一实体直接跳过。
4. **校验器按内容兜底**：**任何原子替换式写文件都会断链**——不止 `git checkout/reset`，AI 编辑工具的 Edit（写临时文件再替换）同样会（2026-10-04 实测：Edit 仓库版 kb_core.py 后 nlink 5→1、库根内容原地落后，校验器当场报「副本与真源内容不一致」）。修法统一：改完真相源后对全部副本 `unlink + os.link` 重建，重建后 nlink 数应恢复满员。原警告：`git checkout/reset` 重写文件会**静默断链**，回到多版本漂移。校验逻辑：`os.path.samefile` → 理想态放行；内容相等但断链 → 提示重建；**内容不等 → ERROR**。修完注入反例（把一份副本换成假旧版）验证检查真的报红，再复原。

**Why**：副本靠注释/约定同步必漂移（kb_core 五副本曾漂出三个版本，且旧版沉淀规程缺校验器步骤 = 漏检口子）；硬链是 Windows 上唯一不引入间接层的"改一处全生效"手段；而断链风险只有内容比对能抓住。

**How to apply**：任何"同一文件出现在 ≥2 个工具目录"的场景（hooks、AGENTS.md、命令、skill）；统一后把副本路径列表写进校验器，闭环时跑一遍见 [PASS]。
