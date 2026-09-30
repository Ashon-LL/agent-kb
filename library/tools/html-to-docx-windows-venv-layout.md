---
name: html-to-docx-windows-venv-layout
description: tencent-docx 插件的 setup-html-to-docx.sh 在 Windows/Git Bash 下按 `bin/python` 判断就绪，而 uv 建出的是 `Scripts/`，导致每次重建 venv + 依赖安装静默失败；用 Scripts/python.exe 手工装 requirements 即通
type: tool
source: 2026-09-23 WorkBuddy 参赛帖 md/html → docx
date: 2026-09-23
---

**事实（本机实测）**：`<plugin_root>/scripts/wb/local/setup-html-to-docx.sh` 第 86 / 94 行（及后续冒烟测试）一律用 `$VENV_DIR/bin/python`；**uv 在 Windows 上建出的 venv 是 `Scripts/`，根本没有 `bin/`** ⇒

- 判据永远为假 → 每次都 `rm -rf` 重建 venv；
- `uv pip install --python "$VENV_DIR/bin/python"` 指向不存在的路径，而该行带 `>/dev/null 2>&1` ⇒ **报错被吞**，脚本停在 `▶ Installing html-to-docx dependencies` 后无声结束，依赖一个没装；
- 表面症状极具误导：脚本打印过 `✓ venv ready`，随后 `python -m html_to_docx` 必然 `ModuleNotFoundError`。
- 另一个连带坑：`VENV_DIR` 默认 `$HOME/.venv-html-to-docx`（`/c/Users/...` 形态），经 MSYS 参数转换后可能落到别处（本机实测出现过 venv 不在预期路径）。**改用 Windows 风格路径最稳**。

**解法（照抄可用）**：
```bash
VENV="C:/Users/<user>/.venv-html-to-docx"      # Windows 风格路径，避开 MSYS 转换
uv venv --python 3.12 "$VENV"
uv pip install --python "$VENV/Scripts/python.exe" --only-binary=:all: \
  -r "<plugin_root>/skills/html-to-docx/scripts/requirements.txt"
PY="$VENV/Scripts/python.exe"                  # 之后一律用这个解释器
cd "<plugin_root>/skills/html-to-docx/scripts" && \
  "$PY" -m html_to_docx convert in.html -o out.docx
```
- `--only-binary=:all:` 必须保留（lxml 无 libxml2/libxslt 时源码构建会挂）。
- **验收别信脚本末尾输出**：`ls "$VENV/Scripts"` + 直接 `import docx` 才算数；管道里的退出码也不可信（`| tail` 会把 exit code 换成 tail 的）。
- 转换成功判定看 stdout 的 `{"success": true, ...}`，并核对 `word/media/` 图片数 == 正文 `a:blip` 引用数。

相关：[[windows-scripting-terminal-gotchas]]、[[powershell-tool-stdout-empty-write-files-instead]]
