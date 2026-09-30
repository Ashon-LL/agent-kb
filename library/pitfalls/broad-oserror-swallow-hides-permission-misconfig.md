---
name: broad-oserror-swallow-hides-permission-misconfig
description: 「可选凭据/可选资源加载器把 OSError 一并吞掉」会让权限错配与「未配置」变成同一个返回值，auto 回退模式下配置错误永远无声——先查服务真实 uid 与路径链权限，再怀疑自己写的代码
type: pitfall
source: APIShow CodeArts STS 凭据改造（2026-09-28）：凭据已部署、内容有效，服务却持续回退长期钥且零日志
date: 2026-09-28
---

**经验**：任何「加载可选资源，失败就当作没有」的代码，都必须在**异常类型层面**区分「真的没有」和「有但读不到」。`except OSError: return None` 会把 `FileNotFoundError`（正常，未配置）与 `PermissionError` / `IsADirectoryError`（配置错误）合并成同一个返回值；而 `os.path.exists()` 本身就吞掉所有异常并返回 False，等于在最前面又吞了一次。在 auto/回退模式里，这类失败会被回退路径**静默吸收**，最终表现为「配置已部署、内容正确，但完全不生效，且零错误日志」——这是最难查的一类故障。

**Why**：CodeArts 中转改造，STS 临时凭据已 scp 到服务器（存在、0600、JSON 合法、未过期、离过期 100+ 分钟）。但 adapter 启动日志一直是 `签名模式切换: (none) -> longterm`，重启两次都一样，**零错误日志**。排查时先怀疑自己刚写的代码：在服务器上以 systemd 的最小环境（`env -i` + 仅注入 EnvironmentFile）直接调 `load_credentials()`，返回的却是 STS——代码、模块导入、路径解析、环境变量、过期校验、文件内容全部逐条排除，陷入僵局。

真实根因与代码无关：**服务的实际运行身份与 unit 文件声明不符**。`systemctl show -p User -p Group` 实测 `User=apishow | Group=apishow`（`/proc/<pid>/environ` 里 `USER=apishow`、`HOME=/home/apishow`），而 unit 片段里写的是 `User=root`，且片段自上年 8 月未改过。凭据目录 `0700 root:root`、凭据文件 `0600 root:root`，`apishow` 连目录遍历都做不到。

于是失败链是：`os.path.exists()` 吞异常 → `load_credential()` 的 `except (OSError, ValueError)` 再吞一次 → 上层拿到 `None` → `_cred_usable(None)` False → 刷新函数命中 `if not cred: return`（不打日志）→ auto 模式回退到 `codearts.env`（0644）里的长期钥，**继续正常工作**。每一环都「正确地」失败了，所以日志一条都没有。

**How to apply**：

1. **报「配置已部署却不生效、无报错」时，先查运行身份，别先怀疑代码**。固定顺序：`systemctl show <unit> -p User -p Group` → `/proc/<pid>/environ`（看 `USER` / `HOME`）→ `stat -c "%a %U:%G %n"` 走完整条路径链（**每一级目录都要可遍历**）→ 最后**以该 uid 身份实测 `open()`**。`su -s /bin/sh <user> -c ...` 或 `runuser -u <user> -- ...`。
2. **unit 文件内容不等于运行身份**。unit 可能被 drop-in 覆盖、被其他 unit 派生、或历史遗留。**以 `systemctl show` / `/proc/<pid>/*` 为准**，不要相信磁盘上的 `.service` 片段。
3. **目录权限是逐级生效的**：文件 0644 也没用，只要路径上有一级目录不给目标用户 `x`，就读不到。而 `0700` 目录 + `0644` 文件的组合看起来毫无恶意，实际是完全隔离。
4. **修「可选资源加载器」时，按异常类型分流**：`FileNotFoundError` → 返回 None（正常未配置）；`ValueError` / `JSONDecodeError` → 返回 None（内容损坏，可回退）；**其余 `OSError` 必须冒泡并打日志**。加一个回归测试用「路径是个目录」造 `IsADirectoryError`——跨平台、不依赖 root、不需要构造真实权限拒绝。
5. **回退路径必须留下原因**。`auto` 模式切回长期方案时，日志要写清楚为什么（凭据不可用 / 模块缺失 / 显式指定），否则回退本身就成了黑盒。切换类日志只在状态变化时打一次即可，不要每次请求都打。
6. **修部署问题时优先不放宽既有权限**。给服务一个**自己拥有的**资源目录（如 `0700 owner=<uid>`）比把全局 secrets 目录改成组可读更安全。若必须给目录权限，**只给 `x` 不给 `r`**：进程能按名打开目标文件，但列不出目录、读不到同目录其他私密文件。
7. **回退成功 ≠ 部署成功**。功能正常恰恰是这类故障最难发现的原因——验证部署时要看「用了哪条路径」的日志，而不是「功能有没有坏」。

**相邻**：权限位与 umask 不一致见 [[generated-credential-files-default-permissive]]；容器挂载属主与进程 uid 必须匹配见 [[bind-mount-owner-must-match-container-uid]]；环境里"声称的配置"必须实测核验见 [[env-claims-must-be-reverified]]；读到的日志文本不等于真实语义见 [[log-text-is-not-spec-read-emitting-code]]。
