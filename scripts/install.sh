#!/usr/bin/env bash
#
# agent-kb 安装脚本（bash，Linux / macOS）—— 与 scripts/install.ps1 功能对称
#
# 用法：
#   ./install.sh [-p <platform>] [-k <kb-path>] [-f] [-l] [-h]
#
#   -p <platform>  平台名，默认 trae。支持：
#                  trae | zcode | codex | claude | hermes | pi | opencode |
#                  openclaw | workbuddy | kimi | qoder
#   -k <dir>       经验库目录，默认 $HOME/.agents/kb
#   -f             覆盖已存在的配置（merge 型平台会保留其他键，先备份 .bak）
#   -l             只列出支持的平台与安装目标，不做任何改动
#   -h             显示帮助
#
# 退出码：0 成功；1 参数错误；2 环境不满足（缺 python / 文件缺失）

set -euo pipefail

# ------------------------------------------------------------------ 常量
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
HOOKS_SRC="$REPO_ROOT/hooks"
SKILL_SRC="$REPO_ROOT/skill"
LIB_SRC="$REPO_ROOT/library-template"
TEMPLATES_DIR="$REPO_ROOT/templates"

HOME_DIR="${HOME:-$(getent passwd "$(id -u)" 2>/dev/null | cut -d: -f6 || true)}"
if [ -z "$HOME_DIR" ]; then
  echo "[ERROR] 无法确定用户主目录（\$HOME 为空）" >&2
  exit 2
fi

PLATFORM="trae"
KB_PATH=""
FORCE=0
LIST_ONLY=0

PLATFORMS_ALL="trae zcode codex claude hermes pi opencode openclaw workbuddy kimi qoder"

# ------------------------------------------------------------------ 帮助
usage() {
  sed -n '3,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

# ------------------------------------------------------------------ 参数
while getopts ":p:k:flh" opt; do
  case "$opt" in
    p) PLATFORM="$OPTARG" ;;
    k) KB_PATH="$OPTARG" ;;
    f) FORCE=1 ;;
    l) LIST_ONLY=1 ;;
    h) usage; exit 0 ;;
    \?) echo "[ERROR] 未知参数 -$OPTARG（-h 看帮助）" >&2; exit 1 ;;
    :)  echo "[ERROR] -$OPTARG 需要取值" >&2; exit 1 ;;
  esac
done

# ------------------------------------------------------------------ 平台注册表
# 每个平台设置 4 个变量：
#   ADAPTER      hooks/ 下的适配器文件名
#   HOOKS_DST    适配器 .py 的落脚目录
#   CONFIG_FILE  待生成的 hook 配置路径（空 = 手工注册）
#   TEMPLATE     templates/ 下的模板名（空 = 无）
#   MERGE        1 = 模板需合并进已有 settings.json（保留其他键）
#   MANUAL       1 = 无 JSON 配置，需用户手工注册
ADAPTER=""; HOOKS_DST=""; CONFIG_FILE=""; TEMPLATE=""; MERGE=0; MANUAL=0

set_platform() {
  ADAPTER=""; HOOKS_DST=""; CONFIG_FILE=""; TEMPLATE=""; MERGE=0; MANUAL=0
  case "$1" in
    trae)
      ADAPTER="trae_zcode_adapter.py"; TEMPLATE="trae-hooks.json"
      HOOKS_DST="$HOME_DIR/.trae-cn/hooks/agent-kb"
      CONFIG_FILE="$HOME_DIR/.trae-cn/hooks.json"
      ;;
    zcode)
      ADAPTER="trae_zcode_adapter.py"; TEMPLATE="zcode-hooks.json"
      HOOKS_DST="$HOME_DIR/.zcode/hooks/agent-kb"
      CONFIG_FILE="$HOME_DIR/.zcode/hooks.json"
      ;;
    codex)
      ADAPTER="codex_adapter.py"; TEMPLATE="codex-hooks.json"
      HOOKS_DST="$HOME_DIR/.codex/hooks/agent-kb"
      CONFIG_FILE="$HOME_DIR/.codex/hooks.json"
      ;;
    claude)
      ADAPTER="claude_adapter.py"; TEMPLATE="claude-hooks.json"
      HOOKS_DST="$HOME_DIR/.claude/hooks/agent-kb"
      CONFIG_FILE="$HOME_DIR/.claude/settings.json"
      MERGE=1
      ;;
    qoder)
      ADAPTER="qoder_adapter.py"; TEMPLATE="qoder-hooks.json"
      HOOKS_DST="$HOME_DIR/.qoder/hooks/agent-kb"
      CONFIG_FILE="$HOME_DIR/.qoder/settings.json"
      MERGE=1
      ;;
    workbuddy)
      ADAPTER="workbuddy_adapter.py"; TEMPLATE="workbuddy-hooks.json"
      HOOKS_DST="$HOME_DIR/.codebuddy/hooks/agent-kb"
      CONFIG_FILE="$HOME_DIR/.codebuddy/settings.json"
      MERGE=1
      ;;
    hermes)
      ADAPTER="hermes_adapter.py"; TEMPLATE="hermes-hooks.json"
      HOOKS_DST="$HOME_DIR/.hermes/hooks/agent-kb"
      CONFIG_FILE="$HOME_DIR/.hermes/hooks.json"
      ;;
    pi)
      ADAPTER="pi_adapter.py"; TEMPLATE="pi-hooks.json"
      HOOKS_DST="$HOME_DIR/.pi/hooks/agent-kb"
      CONFIG_FILE="$HOME_DIR/.pi/hooks.json"
      ;;
    kimi)
      ADAPTER="kimi_adapter.py"; TEMPLATE="kimi-hooks.json"
      HOOKS_DST="$HOME_DIR/.kimi-code/hooks/agent-kb"
      MANUAL=1   # TOML [[hooks]]，写进 config.toml
      ;;
    opencode)
      ADAPTER="opencode_adapter.py"; TEMPLATE="opencode-hooks.json"
      HOOKS_DST="$HOME_DIR/.config/opencode/hook-bridge/agent-kb"
      MANUAL=1   # JS 插件桥
      ;;
    openclaw)
      ADAPTER="openclaw_adapter.py"; TEMPLATE="openclaw-hooks.json"
      HOOKS_DST="$HOME_DIR/.openclaw/hooks/agent-kb"
      MANUAL=1   # TS 插件桥
      ;;
    *)
      echo "[ERROR] 不支持的平台：$1" >&2
      echo "        支持：$PLATFORMS_ALL" >&2
      exit 1
      ;;
  esac
}

# ------------------------------------------------------------------ -l 列表
if [ "$LIST_ONLY" -eq 1 ]; then
  echo "agent-kb 支持的平台："
  for p in $PLATFORMS_ALL; do
    set_platform "$p"
    suffix=""
    [ "$MANUAL" -eq 1 ] && suffix="（需手工注册 hook）"
    printf '  %-10s -> %s %s\n' "$p" "$HOOKS_DST" "$suffix"
  done
  exit 0
fi

[ -z "$KB_PATH" ] && KB_PATH="$HOME_DIR/.agents/kb"

set_platform "$PLATFORM"

printf '=== agent-kb installer ===\n'
printf 'Platform : %s\n' "$PLATFORM"
printf 'Adapter  : %s\n' "$ADAPTER"
printf 'KbPath   : %s\n' "$KB_PATH"
printf 'Force    : %s\n\n' "$FORCE"

# ------------------------------------------------------------------ python
PYTHON="$(command -v python3 || command -v python || true)"
if [ -z "$PYTHON" ]; then
  echo "[WARN] 找不到 python，请手动编辑生成配置里的 PYTHON_EXECUTABLE" >&2
  PYTHON="python3"
fi

# ------------------------------------------------------------------ 1. Skill
SKILL_DST="$HOME_DIR/.agents/skills/kb"
if [ -f "$SKILL_SRC/SKILL.md" ]; then
  mkdir -p "$SKILL_DST"
  if [ ! -f "$SKILL_DST/SKILL.md" ] || [ "$FORCE" -eq 1 ]; then
    cp -f "$SKILL_SRC/SKILL.md" "$SKILL_DST/SKILL.md"
    printf '[OK] Skill 已安装 -> %s\n' "$SKILL_DST"
  else
    printf '[SKIP] Skill 已存在，加 -f 覆盖\n'
  fi
fi

# ------------------------------------------------------------------ 2. Hooks
mkdir -p "$HOOKS_DST"
for f in kb_core.py adapter_base.py "$ADAPTER"; do
  if [ ! -f "$HOOKS_SRC/$f" ]; then
    echo "[ERROR] 缺少 $HOOKS_SRC/$f" >&2
    exit 2
  fi
  cp -f "$HOOKS_SRC/$f" "$HOOKS_DST/$f"
done
printf '[OK] Hooks 已安装 -> %s\n' "$HOOKS_DST"
printf '     adapter: %s  (+ kb_core.py, adapter_base.py)\n' "$ADAPTER"

# ------------------------------------------------------------------ 3. 配置
if [ "$MANUAL" -eq 1 ]; then
  printf '\n[NEXT] %s 需手工注册 hook，模板见：%s\n' "$PLATFORM" "templates/$TEMPLATE"
  case "$PLATFORM" in
    kimi)
      printf '       写法：TOML，追加到 ~/.kimi-code/config.toml 的 [[hooks]] 数组\n'
      printf '       command = "%s %s/kimi_adapter.py"\n' "$PYTHON" "$HOOKS_DST"
      ;;
    opencode)
      printf '       写法：JS 插件 shell 调起桥接脚本\n'
      printf '       shell: "%s" "%s/opencode_adapter.py"\n' "$PYTHON" "$HOOKS_DST"
      ;;
    openclaw)
      printf '       写法：TS 插件（definePluginEntry）注册 session_start / before_prompt_build\n'
      printf '       shell: "%s" "%s/openclaw_adapter.py"\n' "$PYTHON" "$HOOKS_DST"
      ;;
  esac
else
  TEMPLATE_PATH="$TEMPLATES_DIR/$TEMPLATE"
  if [ -f "$TEMPLATE_PATH" ]; then
    # 占位符替换
    body="$(sed -e "s|PYTHON_EXECUTABLE|$PYTHON|g" -e "s|HOOKS_DIR|$HOOKS_DST|g" "$TEMPLATE_PATH")"

    # 剥离模板里的 "_comment"（给人看的文档字段，不该进平台真实配置）
    if command -v python3 >/dev/null 2>&1; then
      stripped="$(printf '%s' "$body" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(1)
d.pop("_comment", None)
print(json.dumps(d, ensure_ascii=False, indent=2))
' 2>/dev/null)" && [ -n "$stripped" ] && body="$stripped"
    fi

    mkdir -p "$(dirname -- "$CONFIG_FILE")"

    if [ ! -f "$CONFIG_FILE" ] || [ "$FORCE" -eq 1 ]; then
      if [ "$MERGE" -eq 1 ] && [ -f "$CONFIG_FILE" ] && [ "$FORCE" -eq 1 ]; then
        # merge 型：只替换 hooks 子树，保留原有其他键
        cp -f "$CONFIG_FILE" "$CONFIG_FILE.bak"
        if printf '%s' "$body" | python3 -c '
import json, sys
tpl = json.load(sys.stdin)
path = sys.argv[1]
try:
    with open(path, encoding="utf-8") as fh:
        cur = json.load(fh)
except Exception:
    cur = {}
cur["hooks"] = tpl.get("hooks", {})
with open(path, "w", encoding="utf-8") as fh:
    json.dump(cur, fh, ensure_ascii=False, indent=2)
' "$CONFIG_FILE" 2>/dev/null; then
          printf '[OK] hooks 已合并进 -> %s\n' "$CONFIG_FILE"
          printf '     （保留了原有 settings.json 其他配置，备份 %s.bak）\n' "$CONFIG_FILE"
        else
          printf '[WARN] 合并失败，改为整文件写入（原文件已备份 .bak）\n'
          printf '%s\n' "$body" > "$CONFIG_FILE"
        fi
      else
        printf '%s\n' "$body" > "$CONFIG_FILE"
        printf '[OK] 配置已生成 -> %s\n' "$CONFIG_FILE"
      fi
    else
      printf '[SKIP] %s 已存在，加 -f 覆盖/合并\n' "$CONFIG_FILE"
      printf '       模板路径：%s\n' "$TEMPLATE_PATH"
    fi
  fi
fi

# ------------------------------------------------------------------ 4. 库模板
if [ ! -d "$KB_PATH" ]; then
  mkdir -p "$KB_PATH/pitfalls" "$KB_PATH/workflow" "$KB_PATH/tools"
  cp -f "$LIB_SRC/INDEX.md" "$KB_PATH/INDEX.md"
  # 目录可能为空，用 find 兜底避免 glob 未展开报错
  find "$LIB_SRC/pitfalls" -maxdepth 1 -name '*.md' -exec cp -f {} "$KB_PATH/pitfalls/" \;
  find "$LIB_SRC/workflow" -maxdepth 1 -name '*.md' -exec cp -f {} "$KB_PATH/workflow/" \;
  find "$LIB_SRC/tools"    -maxdepth 1 -name '*.md' -exec cp -f {} "$KB_PATH/tools/" \;
  printf '[OK] 空库模板已安装 -> %s\n' "$KB_PATH"
else
  printf '[SKIP] KbPath 已存在，保留用户内容不动\n'
fi

# ------------------------------------------------------------------ 完成
printf '\n=== 安装完成 ===\n'
printf '目标路径：%s\n' "$HOOKS_DST"
printf '下一步  ：重启 Agent 会话让新 hook/skill 生效\n'
if [ "$MANUAL" -eq 0 ] && [ -n "$CONFIG_FILE" ]; then
  printf '          配置文件：%s\n' "$CONFIG_FILE"
fi
printf '          覆盖默认库路径：export AGENT_KB_PATH=<dir>\n'
printf '          排查问题      ：export AGENT_KB_DEBUG=1 看 stderr\n'
