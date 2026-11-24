---
name: multikey-pool-is-multi-account-rotation-is-the-point
description: 多 key 池通常等于多个账户；429 换号/轮换是「单 key 易被限、聚合保连续」的设计目的，不是负优化或自我放大；分析限流前必须先确认 key 的账户归属与配额维度
type: pitfall
source: APIShow 商汤源 2026-10-30 实测复盘（15 个 key = 15 个账户；站主纠正）
date: 2026-10-30
verified: 2026-10-30
topic: api-gateway
---

# 多 key 池 = 多账户：429 换号是设计目的，别把它当「放大」

## 症状

看到「15 把 key 全部 429」「每次失败在 relay 里试了 5 个 key」，于是下结论：
「所有 key 共享额度，换号无效」「重试 5 次把用量放大 5 倍，是负优化」。

## 根因

1. **多 key 池通常是多账户**：每个 key 对应独立账户、独立配额。聚合多条 key 的目的
   就是「单 key 容易被限/停，多账户轮换保持连续」。429 → 换 key = 换账户，是**设计目的**。
2. **不要把「重试 N 次」叫放大**：请求是在 N 个不同账户间分摊；只有当这些账户同时
   被限时才失败。把它写成「同一账户重复打 5 次」会把结论带反。
3. **共享额度的判断需要证据**：仅凭「连续 6 个 key 都 429」不能证明共享——突发窗口里
   多个账户各自被限同样会出现这个现象。

## 正确判据（分析限流前先做）

- 确认 key 与账户的归属关系（keys.json/accounts.json 是否一 key 一账户、有无独立配额字段）。
- 做对照实验：**同 key 连打** vs **轮换 key**，比成功率和恢复时间；不要只测轮换。
- 观察 429 的错误码与文案是否区分「账户×模型 / 端点 / 平台」维度。
- 把「重试次数」表述为「尝试了几个账户」，而不是「同一目标打了几次」。

## 结论模板

多账户池的 429 处置优先级：换账户 → 冷却该账户 → 全部受限才返回 429。
失败率高的真正杠杆通常是「增加可用账户」或「降低单请求 token」，而不是取消轮换。

## 相关

[[upstream-queue-blind-wait-backfires]]、[[upstream-queue-error-must-be-429-not-hard-403]]

## 运维口径（2026-10-30 站主令）

- 商汤这类「多账户限额池」的 429/限流是**常态**，不是故障：监控/告警不应把它当异常追。
- 告警只对**非 429**（401/5xx/超时/解析失败）计数；429 单独做观测列（本项目
  `scripts/ops/channel_health_alert.py` 已按此改：单密钥非 429 错误 ≥50 才告警）。
- 优化方向是「使用逻辑」（多账户分摊、降低单请求 token、排队/重试节奏），不是「消灭错误」。

## ⭐ 轮换触发条件必须覆盖「额度耗尽」，不能只判 429（2026-11-07 实测）

**多账户池的价值一半在限流、一半在额度**。余额/配额耗尽是**永久性**不可用——只判 429 的换 key 逻辑会让整个池子在「第一把烧干」的那一刻集体失效，后面的 key 明明有钱却永远轮不到。

**实例（AstrBot v4.28.2 `provider/sources/openai_source.py::_handle_api_error`）**：

```python
if "429" in str(e):          # ← 只有限流换 key
    ...
    chosen_key = random.choice(available_api_keys)
```

13 把 DeepSeek key（余额 $1.77~$7.81）配好了，默认只用 `api_keys[0]`；第一把耗尽时上游返 **402 `Insufficient Balance`**，此分支不命中 ⇒ 直接抛给上层回退，其余 12 把永不启用。

**正解**：换 key 判据按「这把 key 还能不能用」定义，而不是按 HTTP 状态码枚举：

```python
_err_lower = str(e).lower()
if ("429" in str(e) or "402" in str(e)
        or "insufficient balance" in _err_lower
        or "insufficient_quota" in _err_lower
        or "quota exceeded" in _err_lower
        or "余额不足" in str(e)):
    available_api_keys.remove(chosen_key)
    chosen_key = random.choice(available_api_keys)   # 空了才 raise，交给下一档
```

**取舍：轮换顺序 = 余额从高到低**。因为 `api_keys[0]` 恒为首选，把余额最大的放第一位能延长首档寿命；顺序反了会频繁触发轮换（每次多一次失败请求的延迟）。

**验证方式（不用真烧完一把 key）**：直接对补丁后的方法做单测，喂 `Exception("Error code: 402 - Insufficient Balance")` 与假 key 列表，断言返回的 `chosen_key` 变了、`available_api_keys` 少了当前那把；再喂「只剩一把」断言抛异常（应交给 provider 级回退）。这比等真耗尽快且可复现。

**持久化陷阱**：容器里改源码，`docker compose up -d` 重建即丢。稳妥做法是**启动时应用**——把补丁脚本放宿主机目录 bind-mount 进容器（如 `./patches:/patches:ro`），compose `command` 改成 `sh -c "python /patches/apply_boot_patches.py || true; exec python main.py"`。脚本必须**幂等 + 软失败**：已打过就跳过，锚点消失（镜像升级）只打印 ERROR 不阻塞启动。

## ⭐ 策略复杂化后：从源码补丁升级为独立 sidecar 服务（2026-11-08 实操）

启动补丁适合**小而固定**的行为修正（几行条件）。一旦 key 策略长成「余额排序 + dead 标记持久化 + 热加载 + 管理观测」（几十行逻辑、要独立重启/独立配置/独立日志），继续 patch 厂商源码有三个结构性短板：

1. **镜像升级静默回滚**（软失败只打 ERROR，策略退回默认行为，极易漏看）；
2. **无独立观测**：key 池状态（哪把死了、余额多少）只能翻 bot 日志；
3. **生命周期耦合**：bot 重启会牵连 key 状态。

正解：升级成 **OpenAI 兼容 sidecar**（relay 模式）。bot 配置指 `http://keyrouter:8000` + 一把 dummy key，真实 key 只在 sidecar 的 0600 配置文件里。收益：镜像升级不碰策略、`/admin/state` 一眼看池、`/admin/reload`+`/admin/undead` 管热加载与充值复活、sidecar 可独立重启。「全死 → 402」语义保留，bot 的 provider 级 fallback 链（二档/三档）不受影响。

**踩坑备忘**：

- Go 纯构建（`CGO_ENABLED=0`）在 alpine 基（无 tzdata 包）下**不读 `/etc/localtime`**，时间退化 UTC；软链也不救（目标不存在）。必须 `-tags timetzdata` 构建（内嵌 IANA 时区库）+ `TZ=Asia/Shanghai` env——Go 不读 TZ env 的前提是该 tag 提供了数据。
- **换运行中的二进制**：被 `:ro` bind mount 占用的文件直接 scp 覆盖会 ETXTBSY，先 `docker stop` 再传。
- **不烧真 key 的换 key 活体验证**：注入一把假 key 且余额顶格 → 重启 sidecar（状态进进程内存）→ 请求先打假 key → 上游 401 → 断言标 dead 并切真 key。⚠ **改磁盘状态文件对运行进程无效**（状态在内存、文件只写）——「第一次就成功」的测试很可能是假阳性（假 key 沉底根本没被选中）。
