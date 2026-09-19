# agent-kb 安装脚本（PowerShell，Windows）
# 用法：.\install.ps1 [-Platform trae|zcode|codex] [-KbPath ~/.agents/kb] [-Force]
# 功能：把本仓库的 Skill / Hooks / 命令 安装到对应平台的用户目录

param(
    [ValidateSet("trae", "zcode", "codex")]
    [string]$Platform = "trae",

    [string]$KbPath = "",      # 留空则默认 ~/.agents/kb

    [switch]$Force             # 覆盖已存在文件
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $KbPath) {
    $KbPath = Join-Path $env:USERPROFILE ".agents\kb"
}
$KbPath = [System.IO.Path]::GetFullPath($KbPath)

Write-Host "=== agent-kb installer ===" -ForegroundColor Cyan
Write-Host "Platform : $Platform"
Write-Host "KbPath   : $KbPath"
Write-Host "Force    : $Force"
Write-Host ""

# --- 1. 安装 Skill ---
$SkillSrc = Join-Path $RepoRoot "skill"
$SkillDst = Join-Path $env:USERPROFILE ".agents\skills\kb"

if (Test-Path $SkillSrc) {
    if (-not (Test-Path $SkillDst)) {
        New-Item -ItemType Directory -Path $SkillDst -Force | Out-Null
    }
    if (-not (Test-Path (Join-Path $SkillDst "SKILL.md")) -or $Force) {
        Copy-Item (Join-Path $SkillSrc "SKILL.md") (Join-Path $SkillDst "SKILL.md") -Force
        Write-Host "[OK] Skill 已安装 -> $SkillDst" -ForegroundColor Green
    } else {
        Write-Host "[SKIP] Skill 已存在，加 -Force 覆盖" -ForegroundColor DarkGray
    }
}

# --- 2. 安装 Hooks ---
$HooksSrc = Join-Path $RepoRoot "hooks"

if ($Platform -eq "trae" -or $Platform -eq "zcode") {
    $HooksDst = switch ($Platform) {
        "trae"  { Join-Path $env:USERPROFILE ".trae-cn\hooks\agent-kb" }
        "zcode" { Join-Path $env:USERPROFILE ".zcode\hooks\agent-kb" }
    }

    if (-not (Test-Path $HooksDst)) {
        New-Item -ItemType Directory -Path $HooksDst -Force | Out-Null
    }

    Copy-Item (Join-Path $HooksSrc "kb_core.py") (Join-Path $HooksDst "kb_core.py") -Force
    Copy-Item (Join-Path $HooksSrc "trae_zcode_adapter.py") (Join-Path $HooksDst "trae_zcode_adapter.py") -Force
    Write-Host "[OK] Hooks 已安装 -> $HooksDst" -ForegroundColor Green

    # 生成 hooks.json（替换 PYTHON_EXECUTABLE 和 HOOKS_DIR 占位符）
    $Python = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $Python) {
        Write-Host "[WARN] 找不到 python，请手动编辑 hooks.json" -ForegroundColor Yellow
        $Python = "python"
    }
    $TemplateName = switch ($Platform) {
        "trae"  { "trae-hooks.json" }
        "zcode" { "zcode-hooks.json" }
    }
    $TemplatePath = Join-Path $RepoRoot "templates\$TemplateName"
    $HooksJsonPath = switch ($Platform) {
        "trae"  { Join-Path $env:USERPROFILE ".trae-cn\hooks.json" }
        "zcode" { Join-Path $env:USERPROFILE ".zcode\hooks.json" }
    }

    if (Test-Path $TemplatePath) {
        $template = Get-Content $TemplatePath -Raw
        $template = $template.Replace("PYTHON_EXECUTABLE", $Python)
        $template = $template.Replace("HOOKS_DIR", $HooksDst)
        if (-not (Test-Path $HooksJsonPath) -or $Force) {
            Set-Content -Path $HooksJsonPath -Value $template -Encoding UTF8
            Write-Host "[OK] hooks.json 已生成 -> $HooksJsonPath" -ForegroundColor Green
        } else {
            Write-Host "[SKIP] hooks.json 已存在，加 -Force 覆盖（推荐手动合并）" -ForegroundColor DarkGray
            Write-Host "       模板路径：$TemplatePath" -ForegroundColor DarkGray
        }
    }
}

if ($Platform -eq "codex") {
    $CodexHooksDir = Join-Path $env:USERPROFILE ".codex\hooks"
    if (-not (Test-Path $CodexHooksDir)) {
        New-Item -ItemType Directory -Path $CodexHooksDir -Force | Out-Null
    }
    Copy-Item (Join-Path $HooksSrc "kb_core.py") (Join-Path $CodexHooksDir "kb_core.py") -Force
    Copy-Item (Join-Path $HooksSrc "codex_adapter.py") (Join-Path $CodexHooksDir "codex_adapter.py") -Force
    Write-Host "[OK] Codex hooks 已安装 -> $CodexHooksDir" -ForegroundColor Green

    Write-Host ""
    Write-Host "[NEXT] 请在 ~/.codex/hooks.json 里注册 hook，模板见" -ForegroundColor Yellow
    Write-Host "       templates/codex-hooks.json" -ForegroundColor Yellow
}

# --- 3. 安装库模板（仅当目标目录为空时） ---
$LibrarySrc = Join-Path $RepoRoot "library-template"
if (-not (Test-Path $KbPath)) {
    New-Item -ItemType Directory -Path $KbPath -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $KbPath "pitfalls") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $KbPath "workflow") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $KbPath "tools") -Force | Out-Null

    Copy-Item (Join-Path $LibrarySrc "INDEX.md") (Join-Path $KbPath "INDEX.md") -Force
    Copy-Item (Join-Path $LibrarySrc "pitfalls\*.md") (Join-Path $KbPath "pitfalls\") -Force
    Copy-Item (Join-Path $LibrarySrc "workflow\*.md") (Join-Path $KbPath "workflow\") -Force
    Copy-Item (Join-Path $LibrarySrc "tools\*.md") (Join-Path $KbPath "tools\") -Force
    Write-Host "[OK] 空库模板已安装 -> $KbPath" -ForegroundColor Green
} else {
    Write-Host "[SKIP] KbPath 已存在，保留用户内容不动" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "=== 安装完成 ===" -ForegroundColor Cyan
Write-Host "下一步：重启 Agent 会话让新 hook/skill 生效"
