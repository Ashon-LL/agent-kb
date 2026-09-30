---
name: windows-scripting-terminal-gotchas
description: Windows 脚本/终端/跨语言互操作高频坑合集：MSYS 路径转换、bash 双引号吞 $、PS1 BOM、grep -a、NSIS 转义、heredoc/管道/CRLF、/tmp 三套文件系统、进程 spawn 与僵尸
type: pitfall
source: mh-agent-open + apishow + default
date: 2026-09-15
---

**经验**（共同特征：命令"成功"但啥也没发生，或报错被误判成工具不可用）：

## 路径 / 变量被 shell 抢处理

- **Git Bash 调原生 exe**：`/flag` 被 MSYS 当路径转换（icacls/cmdkey）→ 前缀 `MSYS_NO_PATHCONV=1`；icacls 一条命令多个 `/remove` 静默 no-op，逐个删，孤立 SID 改走 PowerShell `Get-Acl`/`Set-Acl`；`$USERPROFILE` 反斜杠喂 find 假阴性 → 一律 `/c/Users/…`。中文输出乱码 → `chcp 65001`。
- **bash 双引号吞 `$_`（今天连踩）**：`powershell -Command "... $_ ... $env:X ... $LASTEXITCODE"` 外层用**双引号**时，`$_`/`$var` 会被 **bash 先行展开**再交给 PS（实测 `$_` 被塞成启动脚本路径、`$LASTEXITCODE` 变空导致语法错）→ PS 内联命令一律用**单引号** `-Command '...$_...'`；含复杂引号/中文则 base64 走 `-EncodedCommand`（`python` 读脚本→`s.encode('utf-16-le')`→b64，彻底绕开 bash 插值）。
- **NSIS 内嵌 PowerShell**：字面 `$` 会被当 NSIS 变量吞掉（编译仍成功、命令静默变坏）→ 一律写 `$$`；复杂逻辑落独立 .ps1 用 `-File` 调；warning 6000 是信号。
- ⛔⛔ **裸名 `bash` 在 Windows 上不是 Git Bash，是 WSL**（实测 20260919，MH-Agent-Open）：`subprocess.run(["bash", script])` / 任何按 PATH 找 bash 的代码，会被 **CreateProcess 的搜索顺序**抢先命中 `C:\Windows\System32\bash.exe`（WSL 转发层）——因为 System32 **先于 PATH**。症状：
  ```
  rc: 127
  stderr: /bin/bash: C:UsersMECHREVOAppDataLocalTemptmpXXXX.sh: No such file or directory
  ```
  注意**反斜杠被吃光**（WSL/MSYS 参数解析把 `\` 当转义符）⇒ 看起来像"文件不存在"，实际是**跑错了 bash 且路径语义不兼容**（WSL 只认 `/mnt/c/...`，不认 `C:\...` 也不认 `/c/...`）。
  - ⛔ **极易误判成"代码坏了"**：Linux CI 全绿、Windows 本地必红，且报错文案（No such file or directory）指向的是**临时脚本路径**而不是 bash 本身 ⇒ 人会去查 tempfile 权限、文件是否写出，全是死路。
  - ✅ **取证一步定位**：`python -c "import subprocess;print(subprocess.run(['bash','-c','uname -a'],capture_output=True,text=True).stdout)"` —— 打出 `microsoft-standard-WSL2` 就确诊。⚠ 注意 `shutil.which('bash')` **会给出错误答案**（它只搜 PATH，会报 Git Bash）⇒ **别用 which 判断，要实跑**。
  - ✅ **修法**：显式路径候选表（`C:\Program Files\Git\bin\bash.exe` / `usr\bin\bash.exe` / `/usr/bin/bash`），并在 Windows 上把脚本路径转成 `/c/...` MSYS 形态；**同时用 `write_bytes` 强制 LF**（`NamedTemporaryFile("w")` 在 Windows 会写 CRLF）。
  - ⛔⛔ **改 PATH 顺序解决不了，别白试**（20260919 补实测）：CreateProcess 的搜索顺序是「exe 自身目录 → cwd → **System32** → SysWOW64 → Windows 目录 → **PATH**」⇒ System32 **永远先于 PATH**。⚠ **一个会骗人的观测**：在 Git Bash 里看 `PATH` 会发现 Git 在 `[3]~[8]`、System32 在 `[14]`，看着"Git 在前"—— 那是 **Git Bash 启动时把自己的目录前置**的结果；从注册表读**真实 Windows PATH** 是 `C:\WINDOWS\System32` 在 **[0]**。⇒ 两种观测都对，但**都不是 CreateProcess 的判据**。
  - ⛔ **也没有"禁用别名"这条捷径**：`System32\bash.exe` 是**真文件**（86KB，`Microsoft Bash Launcher`，WinSxS 硬链接，组件 `microsoft-windows-lxss-bash`），不是可禁用的「应用执行别名」（那是**另一个**文件：`%LOCALAPPDATA%\Microsoft\WindowsApps\bash.exe` → `wsl.exe`；禁了它 System32 那个照样赢）。只剩夺所有权改名/删除（要管理员、SFC 与 Windows 更新可能还原、还会干掉 `bash`→WSL 官方入口）⇒ **不建议**。
  - ✅ **正解 = 用显式配置/候选表，别依赖裸名**。宿主工具常提供显式变量（如 `CLAUDE_CODE_GIT_BASH_PATH`）—— 它比 PATH 推断可靠得多，**应作为第一候选**。⚠ 注意它**只影响宿主自己的 shell**，`python subprocess` 不解析它（普通环境变量而已）。
  - ⛔⛔ **写"能力探针"时的一个深层坑（本次差点漏）**：探针若只测「bash 语义正常」（`X=hello; printf "[%s]" "$X"`），它把 WSL 挡在外面**靠的是偶然** —— WSL 转发层恰好会把 `-c` 里的 `$X` 展开劫持为空（输出 `[]`）。那是转发层的参数处理怪癖，**不是判据**；怪癖一变，WSL 就会被选中，然后在真正要用的地方以 rc=127 炸掉。
    ⇒ **探针要测"真正要用的那个能力"**：本模块真正要做的是「跑一个 `/c/...` 形态的脚本文件」，就把它当入选条件（WSL 只认 `/mnt/c/...` ⇒ 必然失败）。**「碰巧拒绝」≠「判据正确」** —— 同类教训见 [[orphan-constants-and-import-warnings-are-not-blockers]] 的"环境依赖型假网"。
  - 📌 **同族纪律**：仓库里**已有的**平台适配 helper 就是为这个坑写的（MH-Agent-Open 的 `tests/test_skill_bash_gate.py::_find_sane_bash`，docstring 逐字记着这条）⇒ **新写平台相关测试前先 grep 仓库有没有现成 helper**，别重写（本次就是重写导致同一坑复发）。

## /tmp 是三套不同文件系统（合并自 write-tool-tmp 条目）

- **agent `Write`/`Read` 工具的 `/tmp` ≠ Git Bash 的 `/tmp` ≠ 远端服务器的 `/tmp`**：前一个是沙箱 FS，Git Bash 的 `/tmp` 解析为 `C:/Users/<用户>/AppData/Local/Temp`，远端又是独立一套。实测 bash 写 `/tmp/x` 后 python 原生 `open('/tmp/x')` 直接 FileNotFoundError。
- 凡要被**另一侧工具**摸到的临时文件，一律落**真实 Windows 路径**（`C:/Users/…`），别用裸 `/tmp`；验证完清理。

## 进程 spawn 与僵尸（接盘自 mcp-stdio 条目）

- **python `subprocess` 起 npm 的 `.cmd`（npx 等）必须 `shell=True`**，否则 WinError 2 找不到文件；路径串用 raw-string 或正斜杠，防 `\U` unicodeescape 炸（`'C:\Users…'` 里 `\U` 被当 unicode 转义）。
- **编译型 MCP 客户端不经 shell 起 stdio server 时**：Windows 上 command 写裸 `npx` → ENOENT，写 `.cmd` 绝对路径 → EINVAL（node 禁 shell-less 启动 .cmd）；通用解法 = `node.exe` + args 首项 `…\node_modules\npm\bin\npx-cli.js`，绕开 shell。
- **`shell=True` 起的进程，`p.kill()` 只杀 cmd 外壳，里面 npx/uvx 存活成僵尸**：实测 8 个残留 uv 进程把 `uv cache clean` 的锁占满 300s 超时。收尾用任务树杀 `taskkill /T /F /PID`，或测完 `Get-Process uv,npx` 扫残留。
- **npm 装的 CLI 是「三件套」、Python 只认 `.cmd`**：`cnb`/`npx` 这类裸命令是无扩展名 sh 脚本，`CreateProcess` 找不到 → `subprocess.run(["cnb",...])` 报 `FileNotFoundError`；要用同目录 `cnb.cmd`，或 `shutil.which("cnb.cmd") or shutil.which("cnb")`。另有隐形陷阱：调用失败若被 `return ""` 静默吞掉会误诊成「数据没解析出来」——必须带哨兵前缀（详见 [[cnb-cli-needs-cmd-suffix-when-spawned-from-python]]）。

## 编码 / 文本 / 检索

- **PS1 BOM**：PS 5.1 把无 BOM 的 UTF-8 .ps1 按 GBK 解析，中文必炸 → .ps1 必须带 BOM（`EF BB BF`，python 补：`b'\xef\xbb\xbf'+data`）；PS 写的 UTF-8 带 BOM，Python 读用 `utf-8-sig`。
- **二进制串检索**：Rust/Go exe 用 `grep -a` 或 strings 默认模式；`strings -el` 是 UTF-16 只适合 .NET——0 命中别误判"不含"；更硬的对比是文件哈希。
- **批量补丁**：heredoc 吃反斜杠/截断长文本（用 Write 落盘脚本）；管道吞退出码（`set -o pipefail` 或显式查 `$?`）；CRLF 文件配 LF 模式串必 MISS（先检测 EOL）；`grep -c … || echo 0` 产生"0\n0"（`VAR=$(grep -c); VAR=${VAR:-0}`）；字节级替换会改坏二进制（限文本扩展名）；Python Windows 文本模式写文件 LF→CRLF（写侧修法：`open(..., newline="\n")` 或 `write_text(..., newline="")`；只写 `encoding=` 不够）。
  - ⛔ **引号 heredoc 也吃反斜杠**（实测 20260919，MH-Agent-Open）：`python - <<'PYEOF'`（**带单引号**、按 POSIX 应当逐字传递）在本机 Git Bash 里仍把正文的 `\\` 折成 `\` ⇒ Python 源码里的 `'''...+ "\\n"'''` 变成**真换行**、`r'[\u4e00-\u9fff]'` 变成**字符「一」**。症状有两种，都不报语法错：① 补丁脚本的锚点字符串**静默不匹配**（`s.count(old) == 0` → AssertionError，看似"锚点写错了"，实为反斜杠被吃）；② 更糟——锚点碰巧命中，反斜杠进了**写入内容**，落盘文件语法坏掉才发现。
  - ✅ **对策**：补丁脚本里**别写含反斜杠的锚点或字面量**；必须写就用 `chr(92)` 拼（`BS = chr(92)`）；或者干脆改用编辑工具/Write 落盘，别走 heredoc。判据：Python 补丁脚本第一次 `count(old)` 得 0 而你在屏幕上"明明看到"那段文本时，**先怀疑反斜杠被吃，不要先怀疑锚点抄错**。
  - 📌 同批配套纪律：补丁脚本写完文件后**立刻** `ast.parse()` 或 `pytest -q` 小跑一次，别攒到最后——本例正是靠"写后即 parse"当场抓到坏文件。
- **curl**：Git Bash argv 内联中文 JSON 报解析错 → 落盘 `--data-binary @file`；PS 管道中文 → 输出按 GBK 解（`p.stdout.decode('gbk')`）或落文件再读。
- **`Path("a/b")` 的 `str()` 在 Windows 是 `a\b`**：拿 `Path` 集与字符串集比等号必假红（实测 20260918：`{'installer\\build_all.ps1'}` vs `{'installer/build_all.ps1'}`）→ 两侧都转 `Path` 再比，或用 `as_posix()`。同源坑：`git ls-files` 永远输出 `/` 分隔符，别拿它的字符串直接和 `Path` 比。
- **编辑工具会把 CRLF 写进工作区文件，撞上「仓库 LF 政策」的 hygiene 测试**（实测 20260918，MH-Agent-Open）：用编辑工具改 `.cnb.yml` 后，工作区文件变成**全 CRLF**（180 CR / 180 LF），而 `tests/test_repo_hygiene.py::test_no_cr_bytes_in_tracked_text_files` 是 `path.read_bytes()` 直读**工作区**（不是 git blob），于是报红。
  - ⛔ **关键鉴别点：git 侧其实是干净的** —— `git diff` 为空、`git show HEAD:.cnb.yml` 是 0 CR，因为 `core.autocrlf=input` + `.gitattributes` 的 `* text=auto eol=lf` 在入索引时已归一化。所以**别急着"修提交"，先分清是「提交内容脏」还是「仅本地工作区脏」**。
  - ✅ 取证三步：① `python -c "d=open(f,'rb').read(); print(d.count(b'\r'), d.count(b'\n'))"` 看工作区；② `git show HEAD:<f> | python -c "import sys; d=sys.stdin.buffer.read(); print(d.count(b'\r'))"` 看 HEAD；③ `git diff --stat <f>` 是否为空。**①脏 + ②干净 + ③空 ⇒ 仅本地**。
  - ✅ 原地归一化：`p.write_bytes(p.read_bytes().replace(b'\r\n', b'\n'))`；随后 `git add --renormalize <f>` + `git update-index --refresh` 清掉 stat-cache 伪改动（`git status` 里那行 ` M` 会消失）。
  - 📌 改完任何**受 LF 政策管辖**的文本文件（.yml/.py/.md/.json/.vue…）后，建议顺手跑一遍 `pytest tests/test_repo_hygiene.py -q`，别等全量。
  - ⛔⛔ **追加（20260921 第二次踩，同一天内反复）—— 还有两个"隐形写入者"，kb 原条目未覆盖**：
    1. **`git reset --hard` / `git checkout <branch>` 覆盖「已存在」的工作区文件时，
       不重新走 `.gitattributes` 的 eol 归一化** ⇒ 直接落 CRLF。
       ✅ 实测确认：`rm <f> && git checkout -- <f>`（**先删再检出**）才会走完整属性管道，落回 LF。
       ⇒ 切分支/回滚后，**别假设工作区行尾还是对的**，要复测。
    2. **编辑工具（Edit/Write）保留原文件行尾**：文件若已是 CRLF，编辑后仍是 CRLF；
       若编辑器按平台默认落行尾，也会写成 CRLF。
       ⇒ 「我明明转过 LF 了」之后**又脏**，多半是这两者之一，不是自己记错。
  - ⛔ **为什么这条会反复犯（根因不在知识，在执行顺序）**：
    kb 早在 20260918 就记全了鉴别与归一手法，但**动手前没查 kb** ⇒ 每次都靠测试报红才发现。
    ⇒ **硬动作**：本仓任何**改文件**的任务，收尾前**主动**跑
       `python -c "import pathlib;b=pathlib.Path('<f>').read_bytes();print(b.count(bytes([13])))"`，
       或直接 `pytest tests/test_repo_hygiene.py -q`。**别等全量 10 分钟才发现。**
  - ⛔⛔⛔ **终极定论（20260921 第三次踩，当天闭环）—— 完整因果与"为什么总觉得修了又有"**：
    **症状**：`git status` 一直显示文件 ` M`；`pytest test_repo_hygiene` 恒红；
    但 `git diff --stat` 为空 / `git diff --ignore-cr-at-eol` 为空。

    **实测四联证据（缺一不可，按此顺序取证）**：
    ```
    ① 工作区字节：  python -c "import pathlib;b=pathlib.Path(f).read_bytes();print(b.count(b''))"
                    → 618（脏）
    ② 索引字节：    git show :f | python -c "import sys;print(sys.stdin.buffer.read().count(b''))"
                    → 0（干净）
    ③ 内容差异：    git diff --ignore-cr-at-eol --stat f
                    → 空（**除行尾外完全相同**）
    ④ 属性：        git check-attr -a f
                    → text: auto / eol: lf（属性**是对的**）
    ```
    ⇒ **①脏 + ②净 + ③空 ⇒ 纯行尾问题，索引/提交内容无罪。**

    ⛔ **两个真正的原因（此前 kb 只记了"编辑工具写 CRLF"，不完整）**：
    1. **`git add` 会重写工作区文件**：它按 `eol` 属性产出新字节
       （输出那句 `CRLF will be replaced by LF the next time Git touches it`
       就是它在预告这次重写）。**所以"转换 → git add"之后工作区可能又变 CRLF**，
       让人误以为"转换无效"。**顺序必须反过来**：先 `git add`（让 git 定稿索引），
       **再**转工作区字节，**最后**直接 commit 不再 add。
       ⛔ 或者更省事：`git add` 之后**再单独跑一次转换**，然后 commit 时用
       `git commit -o <files>`（只提交指定路径，不重新 add 全部）。
    2. **`git update-index --refresh` 是清 stat-cache 的正解**：
       `git status` 里那行 ` M` 常常只是 **mtime 变了**、内容一模一样。
       `--refresh` 之后 `git status` 立刻干净（实测：只剩无关的 `??` 行）。
       ⛔ 别用 `git checkout -- <f>` 去"修" —— 那会把你**未提交的改动一起冲掉**
       （本次真的丢过一次侧栏修复，只能重做）。

    ✅ **闭环操作序列（照抄）**：
    ```bash
    # 1) 先让 git 定稿索引（它会顺手重写工作区行尾）
    git add <files>
    # 2) 再把工作区字节归一（此时没人会再改它）
    python -c "import pathlib,sys
    for f in sys.argv[1:]:
        p=pathlib.Path(f); p.write_bytes(p.read_bytes().replace(b'
', b'
'))
    " <files>
    # 3) 直接提交指定路径（不重新 add ⇒ 不会触发第二次重写）
    git commit -o <files> -m "..."
    # 4) 清 stat-cache + 复核
    git update-index --refresh
    python -c "import pathlib,sys
    print([pathlib.Path(f).read_bytes().count(b'') for f in sys.argv[1:]])" <files>
    # 5) 跑纪律测试（8 条，1 秒）
    python -m pytest tests/test_repo_hygiene.py -q
    ```

    📌 **一句话**：**`git add` 会改工作区字节，所以要「先 add 后转」；` M` 常常只是
    stat-cache 过期，用 `--refresh` 清，别用 `checkout` 冲掉自己的改动。**

  - ⛔ 另一个陷阱：`git add` 会用 `.gitattributes` 重写工作区文件（`git add` 输出会提示
    `CRLF will be replaced by LF the next time Git touches it`）——
    **这条提示出现时，工作区那一刻可能仍是 CRLF**（测试直读工作区 ⇒ 照样红）。
    ⇒ 看到该提示就**以为已修**是错的；要按上面的取证三步复核字节。

**How to apply**：Windows 上写任何 bash/powershell/python 交织的命令，先想 `$` 归谁、`/` 归哪个 FS、进程几层。相关：[[mcp-stdio-install-smoke-test]]、[[env-claims-must-be-reverified]]。
