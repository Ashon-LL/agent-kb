---
name: skills-cli-install-scope-and-agent
description: `npx skills add <repo>` 的安装作用域与目标平台——默认装到**项目级** `<cwd>/.zcode/skills`，`-g` 才是用户级；`-a <agent>` 指定平台（ZCode 传 `-a zcode`），Windows 加 `--copy` 免符号链接；先用 `-l` 列出仓库里的技能再决定
type: tool
source: 10年人间 EP01 P0（2026-10-29 本机 Windows 实测，装 remotion-dev/skills）
date: 2026-10-29
verified: 2026-10-29
topic: zcode
---

**经验**：`npx skills add <owner/repo>`（Agent Skills 官方 CLI）的行为要点：

1. **默认是项目级**：不加 `-g` 时装到 `<当前目录>/.zcode/skills/<skill>/`；`-g/--global` 才装用户级。想要「工作区级」就是默认行为，**不要加 -g**。
2. **`-a <agent>` 指定装机目标**：ZCode 传 `-a zcode` 会落到 `.zcode/skills`（帮助里 `-a '*'` 表示所有已识别 agent）。不指定时会弹交互选择。
3. **`--copy` 而非符号链接**：默认往各 agent 目录建链接，Windows 上容易受权限/长路径影响；`--copy` 直接拷实体文件，稳。
4. **`-l/--list` 先看仓库里有什么**：只列不装，确认技能清单和数量再动手。
5. 一次可装整包：实测 `npx skills add remotion-dev/skills -a zcode --copy -y` 装下 12 个 `remotion-*` 技能（约 2.9 MB），并在安装目录留 `skills-lock.json` 记录来源，供 `experimental_install` 复现。
6. 要在「工作区根」和「项目工程目录」两处都能被发现，就把两处都装一份（ZCode 的技能发现是**从当前目录向上**扫描到仓库根，不会向下进入子目录）。

**Why**：加错 `-g` 会把项目技能塞进用户级目录，跨项目互相污染、且团队无法随仓库共享；不加 `--copy` 在 Windows 上可能装出坏链接导致技能静默缺失；只装在工作区根而实际会话 cwd 在子目录（或反之）会「装了却读不到」。

**How to apply**：装任何 agent skills 前先 `ls <目标目录>/.zcode/skills` 看既有形态，再按上面参数装；装完用 `npx skills list`（项目级默认；用户级加 `-g`）确认条目与路径。相关：[[cross-agent-skill-dir-semantics]]、[[zcode-platform-verified-facts]]。

关联 [[cross-agent-skill-dir-semantics]]、[[zcode-platform-verified-facts]]。
