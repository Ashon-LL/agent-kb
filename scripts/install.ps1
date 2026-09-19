# agent-kb 安装脚本（PowerShell，Windows）
#
# 用法：
#   .\install.ps1 [-Platform <name>] [-KbPath <dir>] [-Force] [-List]
#
#   -Platform  trae | zcode | codex | claude | hermes | pi | opencode |
#               openclaw | workbuddy | kimi | qoder        （默认 trae）
#   -KbPath    经验库目录，默认 %USERPROFILE%\.agents\kb
#   -Force     覆盖已存在的 hooks 配置 / 文件
#   -List      只列出支持的平台与安装目标，不做任何改动
#
# 功能：把本仓库的 Skill / Hooks / 库模板安装到对应平台的用户目录。

param(
    [ValidateSet("trae", "zcode", "codex", "claude", "hermes", "pi", "opencode",
                 "openclaw", "workbuddy", "kimi", "qoder")]
    [string]$Platform = "trae",

    [string]$KbPath = "",       # 留空则默认 ~/.agents/kb

    [switch]$Force,             # 覆盖已存在文件

    [switch]$List               # 只列平台清单
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $RepoRoot   # scripts/ 的上一级 = 仓库根

# 用户主目录：Windows 用 USERPROFILE，*nix 下 pwsh 回退到 HOME
$HomeDir = if ($env:USERPROFILE) { $env:USERPROFILE }
           elseif ($env:HOME) { $env:HOME }
           else { [Environment]::GetFolderPath("UserProfile") }

# ---------------------------------------------------------------- 平台注册表
# adapter   : hooks/ 下的适配器文件名
# hooksDir  : 适配器 .py 的落脚目录
# configFile: 待生成的 hooks 配置路径（$null = 不自动生成，见 $ManualConfig）
# template  : templates/ 下的模板文件名（$null = 无模板）
# merge     : $true 表示模板需"合并"进已有 settings.json（Claude/Qoder/WorkBuddy）
# manual    : $true 表示无 JSON 配置，需用户按提示手工注册（Codex/Kimi/OpenClaw/OpenCode）
$Platforms = @{
    "trae" = @{
        Adapter = "trae_zcode_adapter.py"; Template = "trae-hooks.json"
        HooksDir = Join-Path $HomeDir ".trae-cn/hooks/agent-kb"
        ConfigFile = Join-Path $HomeDir ".trae-cn/hooks.json"
        Merge = $false; Manual = $false
    }
    "zcode" = @{
        Adapter = "trae_zcode_adapter.py"; Template = "zcode-hooks.json"
        HooksDir = Join-Path $HomeDir ".zcode/hooks/agent-kb"
        ConfigFile = Join-Path $HomeDir ".zcode/hooks.json"
        Merge = $false; Manual = $false
    }
    "codex" = @{
        Adapter = "codex_adapter.py"; Template = "codex-hooks.json"
        HooksDir = Join-Path $HomeDir ".codex/hooks/agent-kb"
        ConfigFile = Join-Path $HomeDir ".codex/hooks.json"
        Merge = $false; Manual = $false
    }
    "claude" = @{
        Adapter = "claude_adapter.py"; Template = "claude-hooks.json"
        HooksDir = Join-Path $HomeDir ".claude/hooks/agent-kb"
        ConfigFile = Join-Path $HomeDir ".claude/settings.json"
        Merge = $true; Manual = $false
    }
    "qoder" = @{
        Adapter = "qoder_adapter.py"; Template = "qoder-hooks.json"
        HooksDir = Join-Path $HomeDir ".qoder/hooks/agent-kb"
        ConfigFile = Join-Path $HomeDir ".qoder/settings.json"
        Merge = $true; Manual = $false
    }
    "workbuddy" = @{
        Adapter = "workbuddy_adapter.py"; Template = "workbuddy-hooks.json"
        HooksDir = Join-Path $HomeDir ".codebuddy/hooks/agent-kb"
        ConfigFile = Join-Path $HomeDir ".codebuddy/settings.json"
        Merge = $true; Manual = $false
    }
    "hermes" = @{
        Adapter = "hermes_adapter.py"; Template = "hermes-hooks.json"
        HooksDir = Join-Path $HomeDir ".hermes/hooks/agent-kb"
        ConfigFile = Join-Path $HomeDir ".hermes/hooks.json"
        Merge = $false; Manual = $false
    }
    "pi" = @{
        Adapter = "pi_adapter.py"; Template = "pi-hooks.json"
        HooksDir = Join-Path $HomeDir ".pi/hooks/agent-kb"
        ConfigFile = Join-Path $HomeDir ".pi/hooks.json"
        Merge = $false; Manual = $false
    }
    "kimi" = @{
        Adapter = "kimi_adapter.py"; Template = "kimi-hooks.json"
        HooksDir = Join-Path $HomeDir ".kimi-code/hooks/agent-kb"
        ConfigFile = $null; Merge = $false; Manual = $true
    }
    "opencode" = @{
        Adapter = "opencode_adapter.py"; Template = "opencode-hooks.json"
        HooksDir = Join-Path $HomeDir ".config/opencode/hook-bridge/agent-kb"
        ConfigFile = $null; Merge = $false; Manual = $true
    }
    "openclaw" = @{
        Adapter = "openclaw_adapter.py"; Template = "openclaw-hooks.json"
        HooksDir = Join-Path $HomeDir ".openclaw/hooks/agent-kb"
        ConfigFile = $null; Merge = $false; Manual = $true
    }
}

if ($List) {
    Write-Host "agent-kb 支持的平台：" -ForegroundColor Cyan
    foreach ($k in ($Platforms.Keys | Sort-Object)) {
        $p = $Platforms[$k]
        $suffix = if ($p.Manual) { "（需手工注册 hook）" } else { "" }
        Write-Host ("  {0,-10} -> {1} {2}" -f $k, $p.HooksDir, $suffix)
    }
    exit 0
}

if (-not $KbPath) {
    $KbPath = Join-Path $HomeDir ".agents/kb"
}
$KbPath = [System.IO.Path]::GetFullPath($KbPath)

$cfg = $Platforms[$Platform]

Write-Host "=== agent-kb installer ===" -ForegroundColor Cyan
Write-Host "Platform : $Platform"
Write-Host "Adapter  : $($cfg.Adapter)"
Write-Host "KbPath   : $KbPath"
Write-Host "Force    : $Force"
Write-Host ""

# --- 1. 安装 Skill ---
$SkillSrc = Join-Path $RepoRoot "skill"
$SkillDst = Join-Path $HomeDir ".agents/skills/kb"

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

# --- 2. 安装 Hooks（adapter + kb_core + adapter_base） ---
$HooksSrc = Join-Path $RepoRoot "hooks"
$HooksDst = $cfg.HooksDir

if (-not (Test-Path $HooksDst)) {
    New-Item -ItemType Directory -Path $HooksDst -Force | Out-Null
}

foreach ($f in @("kb_core.py", "adapter_base.py", $cfg.Adapter)) {
    Copy-Item (Join-Path $HooksSrc $f) (Join-Path $HooksDst $f) -Force
}
Write-Host "[OK] Hooks 已安装 -> $HooksDst" -ForegroundColor Green
Write-Host "     adapter: $($cfg.Adapter)  (+ kb_core.py, adapter_base.py)" -ForegroundColor DarkGray

# 找 python
$Python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $Python) {
    $Python = (Get-Command python3 -ErrorAction SilentlyContinue).Source
}
if (-not $Python) {
    Write-Host "[WARN] 找不到 python，请手动编辑生成配置里的 PYTHON_EXECUTABLE" -ForegroundColor Yellow
    $Python = "python"
}

# --- 3. 生成 hook 配置 ---
if ($cfg.Manual) {
    Write-Host ""
    Write-Host "[NEXT] $Platform 需手工注册 hook，模板见：" -ForegroundColor Yellow
    Write-Host "       templates/$($cfg.Template)" -ForegroundColor Yellow
    switch ($Platform) {
        "kimi" {
            Write-Host "       写法：TOML，追加到 ~/.kimi-code/config.toml 的 [[hooks]] 数组" -ForegroundColor Yellow
            Write-Host "       command = `"$Python $HooksDst/kimi_adapter.py`"" -ForegroundColor Yellow
        }
        "opencode" {
            Write-Host "       写法：JS 插件（loadable）shell 调起桥接脚本" -ForegroundColor Yellow
            Write-Host "       shell: `"$Python`" `"$HooksDst/opencode_adapter.py`"" -ForegroundColor Yellow
        }
        "openclaw" {
            Write-Host "       写法：TS 插件（definePluginEntry）注册 session_start / before_prompt_build" -ForegroundColor Yellow
            Write-Host "       shell: `"$Python`" `"$HooksDst/openclaw_adapter.py`"" -ForegroundColor Yellow
        }
    }
}
else {
    $TemplatePath = Join-Path $RepoRoot "templates/$($cfg.Template)"
    if (Test-Path $TemplatePath) {
        $body = Get-Content $TemplatePath -Raw
        $body = $body.Replace("PYTHON_EXECUTABLE", $Python)
        $body = $body.Replace("HOOKS_DIR", $HooksDst)

        # 模板里的 "_comment" 是给人看的文档字段，不能写进平台真实配置
        try {
            $parsed = $body | ConvertFrom-Json
            if ($parsed.PSObject.Properties.Name -contains "_comment") {
                $parsed.PSObject.Properties.Remove("_comment")
                $body = $parsed | ConvertTo-Json -Depth 20
            }
        }
        catch {
            Write-Host "[WARN] 模板 JSON 解析失败，按原文写入" -ForegroundColor Yellow
        }

        $ConfigFile = $cfg.ConfigFile
        $ConfigDir = Split-Path -Parent $ConfigFile
        if (-not (Test-Path $ConfigDir)) {
            New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
        }

        $exists = Test-Path $ConfigFile
        if (-not $exists -or $Force) {
            if ($cfg.Merge -and $exists -and $Force) {
                # merge 型：解析已有 settings.json，只替换 hooks 子树，保留其他键
                try {
                    $existing = Get-Content $ConfigFile -Raw | ConvertFrom-Json
                    $template = $body | ConvertFrom-Json
                    $existing | Add-Member -NotePropertyName "hooks" `
                                          -NotePropertyValue $template.hooks -Force
                    $merged = $existing | ConvertTo-Json -Depth 20
                    Set-Content -Path $ConfigFile -Value $merged -Encoding UTF8
                    Write-Host "[OK] hooks 已合并进 -> $ConfigFile" -ForegroundColor Green
                    Write-Host "     （保留了原有 settings.json 其他配置）" -ForegroundColor DarkGray
                }
                catch {
                    Write-Host "[WARN] 合并失败，改为整文件写入（原文件已备份 .bak）" -ForegroundColor Yellow
                    Copy-Item $ConfigFile "$ConfigFile.bak" -Force
                    Set-Content -Path $ConfigFile -Value $body -Encoding UTF8
                }
            }
            else {
                Set-Content -Path $ConfigFile -Value $body -Encoding UTF8
                Write-Host "[OK] 配置已生成 -> $ConfigFile" -ForegroundColor Green
            }
        }
        else {
            Write-Host "[SKIP] $ConfigFile 已存在，加 -Force 覆盖/合并" -ForegroundColor DarkGray
            Write-Host "       模板路径：$TemplatePath" -ForegroundColor DarkGray
        }
    }
}

# --- 4. 安装库模板（仅当目标目录为空时） ---
$LibrarySrc = Join-Path $RepoRoot "library-template"
if (-not (Test-Path $KbPath)) {
    New-Item -ItemType Directory -Path $KbPath -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $KbPath "pitfalls") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $KbPath "workflow") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $KbPath "tools") -Force | Out-Null

    Copy-Item (Join-Path $LibrarySrc "INDEX.md") (Join-Path $KbPath "INDEX.md") -Force
    Copy-Item (Join-Path $LibrarySrc "pitfalls/*.md") (Join-Path $KbPath "pitfalls/") -Force
    Copy-Item (Join-Path $LibrarySrc "workflow/*.md") (Join-Path $KbPath "workflow/") -Force
    Copy-Item (Join-Path $LibrarySrc "tools/*.md") (Join-Path $KbPath "tools/") -Force
    Write-Host "[OK] 空库模板已安装 -> $KbPath" -ForegroundColor Green
} else {
    Write-Host "[SKIP] KbPath 已存在，保留用户内容不动" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "=== 安装完成 ===" -ForegroundColor Cyan
Write-Host "目标路径：$HooksDst"
Write-Host "下一步  ：重启 Agent 会话让新 hook/skill 生效"
if (-not $cfg.Manual) {
    Write-Host "          配置文件：$($cfg.ConfigFile)"
}
Write-Host "          覆盖默认库路径：设 AGENT_KB_PATH 环境变量"
Write-Host "          排查问题      ：设 AGENT_KB_DEBUG=1 看 stderr"
