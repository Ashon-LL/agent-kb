---
name: wsl2-stdio-mcp-bridge-for-windows-agent
description: Windows Agent 通过 wsl.exe 直连 WSL2 Kali 的 stdio MCP —— 不装 VMware、不走 SSH/IP；含特制化 ZCode 的 shared-mcp 网关（config.json 只放 HTTP、servers.json 放真实 stdio）、MSYS_NO_PATHCONV、gh tarball 下载、阿里云 PyPI、mcp<2 启动器与 168 工具验收
type: tool
source: 2026-10-27 强网杯 CTF 环境改造实测（ZCode + WSL2 Kali 2026.2）
date: 2026-10-27
verified: 2026-10-27
topic: mcp, windows, zcode
---

**经验**【作用域=Windows Agent + WSL2 Kali，本机实测 2026-10-27】：

- **VMware 是多余层**：Windows 已支持 WSL2 时，Agent 直接 `wsl.exe` 起 Linux stdio MCP，不需要 VM 导入、NAT 网段、DHCP IP 探测、SSH 密钥、端口映射。IP 会漂移，密钥要维护，sshd 还是额外攻击面。
- **桥接命令（ZCode 配置里的 args）**：
  `C:\Windows\System32\wsl.exe -d kali-linux --cd /home/kali/ctf-mcp -e /home/kali/ctf-mcp/venv/bin/python /home/kali/ctf-mcp/ctf_mcp_launch.py`
  未共享 server 的临时 stdio 定义在 `~/.zcode/cli/config.json` 的 `mcp.servers.<name>`；stdio 允许字段只有 `type/command/args/cwd/env/enabled/timeoutMs`，**未知键会让整个 server 被丢弃**。`timeoutMs` 给 120000，WSL 冷启动 + 168 工具注册需要时间。
- ★ **特制化 ZCode 的实际形态是 shared-mcp 网关**：所有共享 MCP 由 `mcp-proxy.exe` 在 `127.0.0.1:8799` 统一暴露，`config.json` 只放 `http://127.0.0.1:8799/servers/<name>/mcp`；真实 stdio 定义在 `~/.zcode/mcp-servers/shared-mcp/servers.json`。直接往 `config.json` 写 stdio 只适合临时定义/未共享 server；共享正确姿势：
  `cd ~/.zcode/mcp-servers/shared-mcp && python apply-shared-mcp.py --list|--share ctf|--enable ctf|--disable ctf|--restart|--unshare ctf`
  `--share` 会把 config 的 stdio 定义迁进 `servers.json`、把原始定义存 `state.json`、改写 config 为 HTTP、重启代理。实测 `initialize` 返回 `ctf-mcp`，`tools/list` 168 工具，base64 调用正常。
  `servers.json` 只认 `command`（stdio）；写 `url` 会被静默跳过。有状态 server 不要共享；UI 开关与代理 `enabled` 由 `ZCode-MCP-Sync` 每分钟对账；改完必须重启 ZCode。
- ⛔ **shared-mcp `--stateless` 的 named server 有冷启动竞速**：首次请求现拉上游；WSL+Python+168 工具注册约 **1.7s**，ZCode 约 **241ms** 就写 `mcp.server.failed`（`error` 为空），而 rea/tavily/bocha 这类 Windows 原生进程 244ms 内成功。判据：`zcode-*.jsonl` 里 ctf 的 `connectDurationMs≈241`、其他 server 同批 244ms 成功；curl 端点却 200。修法：重服务常驻化 —— WSL 内 systemd 跑 Streamable HTTP MCP（`StreamableHTTPSessionManager(stateless=True, json_response=True)`，绑 WSL 网卡 IP:8811，不是 0.0.0.0），Windows 侧用原生 `node.exe` stdio↔HTTP 桥（缓存 WSL IP，IP 变自动重解析）作为 `servers.json` 的 ctf command。实测桥 initialize 70ms、网关 initialize 6ms、tools/list 20ms/168 工具。不要改回直接 `wsl.exe`。
- ⛔ **Git Bash 调 `wsl.exe` 且参数含 `/home/...` 必须加 `MSYS_NO_PATHCONV=1`**：否则 MSYS 把它改写成 `C:/Program Files/Git/home/...`，报 `Wsl/ERROR_PATH_NOT_FOUND`。ZCode/Node 直接 spawn 不受影响；人工自测时不加这个前缀会误判 MCP 坏了。
- **GitHub `:443` 不通时用 `gh api repos/<owner>/<repo>/tarball > file`**：本机 `git ls-remote https://github.com/...` 超时，但 `gh` API 通。二进制重定向要在 Git Bash 里做；PowerShell 5.1 的 `>` 会写成 UTF-16 把 tar.gz 弄坏。
- **PyPI 官方源/清华源超时，阿里云可用**：`-i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com`。
- **mcp 必须钉 `<2`**：默认装 2.x 后 `'Server' object has no attribute 'list_tools'`。仓库自带 `main()` 在 1.30 下抛 `a coroutine was expected`，用独立启动器：`stdio_server()` + `app.run(read, write, app.create_initialization_options())`，`register_tools()` 后 `asyncio.run(_serve())`。实测 166 + 2 orchestrator = 168 工具；三行 JSON-RPC 自测应返回 `SGVsbG8gQ1RG`。
- **WSL 管理动作走 `wsl.exe -u root`**：Kali 的 `sudo` 要密码，Agent 没有口令；`-u root` 是原生免密入口。装 apt 包、`systemctl` 都用它。
- ⛔ **旧 0.0.0.0:5000 服务要退役**：`kali_server.service` 以 `Restart=always` 跑 Flask 命令服务，能力接近 RCE；确认新 stdio MCP 可用后 `systemctl stop/disable kali_server.service`，保留 unit 文件以便回滚。
- **技能装 Windows 侧**：ZCode 不读 WSL 的 `/home/kali/.agents/skills`；CTF skills 放 `~/.agents/skills`（跨工具共享）或 `~/.zcode/skills`。MCP 在 WSL，技能在 Windows，两边不要混。
- Python 3.13 的 `pydub` 要配 `audioop-lts`；volatility3 入口是 `~/venvs/volatility3/bin/vol`，不是 `python -m volatility3`。

**Why**：VMware 方案的复杂度（VM 生命周期、IP 漂移、SSH 密钥、端口暴露）全部是 WSL2 已经解决的问题；`wsl.exe` 的 stdin/stdout 天然就是 MCP stdio 管道，少一层就少一类故障。真正的坑集中在 Windows/Git Bash 的路径转换、GitHub/PyPI 网络和 mcp 大版本漂移，而不是 WSL 本身。

**How to apply**：Windows Agent 要调 WSL Kali 工具时，优先 `wsl.exe` stdio，不要先装 VM/配 SSH；先确认目标 ZCode 是「直接 stdio」还是「shared-mcp 网关」——本机是后者，必须走 `apply-shared-mcp.py --share`，不要把 stdio 当成最终配置；人工自测加 `MSYS_NO_PATHCONV=1`；装完用 `tools/list` 数工具、跑一个真实工具调用，再交付。相关：[[mcp-stdio-install-smoke-test]]、[[zcode-platform-verified-facts]]、[[windows-scripting-terminal-gotchas]]、[[wsl-docker-on-demand-startup]]、[[github-china-network-workarounds]]。
