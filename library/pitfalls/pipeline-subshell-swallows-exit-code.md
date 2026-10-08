---
name: pipeline-subshell-swallows-exit-code
description: cmd | tee 把脚本主体跑在子 shell 里，内部 exit 1 被管道吞掉，systemd/CI 把失败报成成功
type: pitfall
source: apishow（2026-10-05 systemd oneshot 恢复脚本）
date: 2026-10-05
verified: 2026-10-05
topic: methodology
---

**经验**：需要「既落日志又保留退出码」时，把主体包进函数用 `return`，末尾统一取第一个元素的退出码：

```bash
main() {
    ...
    return 1    # 关键：return 而非 exit，才能让调用方接管
}
main 2>&1 | tee -a "$LOG"
rc=${PIPESTATUS[0]}
exit "$rc"
```

实测：`/opt/astrbot/restore_zhiqing_silence.sh` 由 systemd oneshot 调起，失败时必须让 systemd 知道（失败要保留 timer 便于排查）。原先 `main | tee` 直接跑，子 shell 里的 `exit 1` 只结束子 shell，管道返回码取 tee 的 0 ⇒ systemd 一律记 success。已用文件式演练验证：失败路径回 3、成功路径回 0。

**Why:** `A | B` 的整体退出码默认是 B 的（bash 未开 pipefail），而 A 在子 shell 里执行 ⇒ A 里 `exit N` 不传播。systemd / cron / CI 只认整条命令的退出码，失败于是被报成成功——对「到点自动恢复」这类脚本尤其致命：它失败后没人会再去看第二眼。

**How to apply:** 主体包函数 + `return`，末尾 `rc=${PIPESTATUS[0]}; exit "$rc"`；`set -o pipefail` 只解决「管道整体取非零」，不解决 exit 在子 shell 的问题，两者互补不替代。⛔ 不要用「日志里有 FAIL 字样」代替退出码——调度器不读日志。

相关：[[verify-with-real-pipeline-and-readonly-probes]]、[[automation-artifacts-lie-existence-and-freshness]]。
