# -*- coding: utf-8 -*-
"""安装脚本测试：install.sh / install.ps1 覆盖全部平台且产出可解析配置。

零第三方依赖。install.sh 必测；install.ps1 仅在 pwsh 可用时测（跳过 Windows-only）。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SH = REPO_ROOT / "scripts" / "install.sh"
INSTALL_PS1 = REPO_ROOT / "scripts" / "install.ps1"

PLATFORMS = [
    "trae", "zcode", "codex", "claude", "hermes", "pi",
    "opencode", "openclaw", "workbuddy", "kimi", "qoder",
]

# 平台 -> 期望的 (hooks 目录相对 $HOME, 配置相对 $HOME)
EXPECTED = {
    "trae":      (".trae-cn/hooks/agent-kb",      ".trae-cn/hooks.json"),
    "zcode":     (".zcode/hooks/agent-kb",        ".zcode/hooks.json"),
    "codex":     (".codex/hooks/agent-kb",        ".codex/hooks.json"),
    "claude":    (".claude/hooks/agent-kb",       ".claude/settings.json"),
    "qoder":     (".qoder/hooks/agent-kb",        ".qoder/settings.json"),
    "workbuddy": (".codebuddy/hooks/agent-kb",    ".codebuddy/settings.json"),
    "hermes":    (".hermes/hooks/agent-kb",       ".hermes/hooks.json"),
    "pi":        (".pi/hooks/agent-kb",           ".pi/hooks.json"),
    "kimi":      (".kimi-code/hooks/agent-kb",    None),
    "opencode":  (".config/opencode/hook-bridge/agent-kb", None),
    "openclaw":  (".openclaw/hooks/agent-kb",     None),
}

ADAPTER_FILE = {
    "trae": "trae_zcode_adapter.py", "zcode": "trae_zcode_adapter.py",
    "codex": "codex_adapter.py", "claude": "claude_adapter.py",
    "qoder": "qoder_adapter.py", "workbuddy": "workbuddy_adapter.py",
    "hermes": "hermes_adapter.py", "pi": "pi_adapter.py",
    "kimi": "kimi_adapter.py", "opencode": "opencode_adapter.py",
    "openclaw": "openclaw_adapter.py",
}


def _has_pwsh() -> bool:
    return shutil.which("pwsh") is not None


class InstallerTestBase:
    # 子类填：命令行前缀 + 平台参数标志 + 库路径标志
    script_cmd: list[str] = []
    platform_flag: str = "-p"
    kbpath_flag: str = "-k"
    force_flag: str = "-f"

    def _run(self, platform, home, *extra):
        env = dict(os.environ)
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
        cmd = [*self.script_cmd, self.platform_flag, platform]
        cmd += [*extra]
        return subprocess.run(
            cmd, capture_output=True, env=env, timeout=120, cwd=str(REPO_ROOT),
        )

    def test_all_platforms_install(self):
        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                with tempfile.TemporaryDirectory() as home:
                    r = self._run(platform, home)
                    self.assertEqual(
                        r.returncode, 0,
                        f"{platform} failed: {r.stderr.decode('utf-8', 'replace')}",
                    )
                    hooks_dir, cfg_rel = EXPECTED[platform]
                    hooks_path = Path(home) / hooks_dir
                    self.assertTrue(hooks_path.is_dir(), f"{platform}: missing {hooks_path}")
                    self.assertTrue((hooks_path / "kb_core.py").is_file())
                    self.assertTrue((hooks_path / "adapter_base.py").is_file())
                    self.assertTrue((hooks_path / ADAPTER_FILE[platform]).is_file())

    def test_generated_config_is_valid_json_without_placeholders(self):
        for platform in PLATFORMS:
            cfg_rel = EXPECTED[platform][1]
            if cfg_rel is None:
                continue  # 手工注册型，无自动配置
            with self.subTest(platform=platform):
                with tempfile.TemporaryDirectory() as home:
                    self.assertEqual(self._run(platform, home).returncode, 0)
                    cfg = Path(home) / cfg_rel
                    self.assertTrue(cfg.is_file(), f"{platform}: missing {cfg}")
                    text = cfg.read_text(encoding="utf-8")
                    self.assertNotIn("PYTHON_EXECUTABLE", text)
                    self.assertNotIn("HOOKS_DIR", text)
                    self.assertNotIn("_comment", text)
                    data = json.loads(text)
                    self.assertIn("hooks", data)
                    self.assertIn("SessionStart", data["hooks"])
                    self.assertIn("UserPromptSubmit", data["hooks"])

    def test_merge_preserves_unrelated_settings(self):
        for platform in ("claude", "qoder", "workbuddy"):
            with self.subTest(platform=platform):
                with tempfile.TemporaryDirectory() as home:
                    cfg_rel = EXPECTED[platform][1]
                    cfg = Path(home) / cfg_rel
                    cfg.parent.mkdir(parents=True, exist_ok=True)
                    cfg.write_text(
                        json.dumps({"theme": "dark", "permissions": {"allow": ["Bash"]}}),
                        encoding="utf-8",
                    )
                    r = self._run(platform, home, "-f")
                    self.assertEqual(r.returncode, 0)
                    data = json.loads(cfg.read_text(encoding="utf-8"))
                    self.assertEqual(data.get("theme"), "dark")
                    self.assertIn("permissions", data)
                    self.assertIn("hooks", data)

    def test_unknown_platform_fails(self):
        with tempfile.TemporaryDirectory() as home:
            r = self._run("not-a-platform", home)
            self.assertNotEqual(r.returncode, 0)


class TestInstallSh(InstallerTestBase, unittest.TestCase):
    script_cmd = ["bash", str(INSTALL_SH)]

    def test_list_covers_every_platform(self):
        r = subprocess.run(
            ["bash", str(INSTALL_SH), "-l"],
            capture_output=True, timeout=60, cwd=str(REPO_ROOT),
        )
        out = r.stdout.decode("utf-8")
        for p in PLATFORMS:
            self.assertIn(p, out)

    def test_strict_mode_and_shebang(self):
        text = INSTALL_SH.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("#!/usr/bin/env bash"))
        self.assertIn("set -euo pipefail", text)


@unittest.skipUnless(_has_pwsh(), "pwsh 不可用，跳过 install.ps1 测试")
class TestInstallPs1(unittest.TestCase):
    SCRIPT = ["pwsh", "-NoProfile", "-File", str(INSTALL_PS1)]

    def test_ps1_and_sh_list_outputs_match(self):
        sh = subprocess.run(["bash", str(INSTALL_SH), "-l"],
                            capture_output=True, timeout=60, cwd=str(REPO_ROOT))
        ps = subprocess.run([*self.SCRIPT, "-List"],
                            capture_output=True, timeout=120, cwd=str(REPO_ROOT))
        self.assertEqual(
            [l.rstrip() for l in sh.stdout.decode("utf-8").splitlines()],
            [l.rstrip() for l in ps.stdout.decode("utf-8").splitlines()],
        )

    def test_ps1_installs_all_platforms(self):
        for platform in PLATFORMS:
            with self.subTest(platform=platform):
                with tempfile.TemporaryDirectory() as home:
                    env = dict(os.environ)
                    env["HOME"] = home
                    env["USERPROFILE"] = home
                    r = subprocess.run(
                        [*self.SCRIPT, "-Platform", platform],
                        capture_output=True, env=env, timeout=180,
                        cwd=str(REPO_ROOT),
                    )
                    self.assertEqual(
                        r.returncode, 0,
                        f"{platform}: {r.stderr.decode('utf-8', 'replace')}",
                    )
                    hooks_path = Path(home) / EXPECTED[platform][0]
                    self.assertTrue((hooks_path / ADAPTER_FILE[platform]).is_file())


if __name__ == "__main__":
    unittest.main()
