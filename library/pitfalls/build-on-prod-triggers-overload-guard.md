---
name: build-on-prod-triggers-overload-guard
description: 别在 2 vCPU 生产机上直接 go build/go test——New API 性能护栏 CPU>90% 连续采样即对 /v1/* 返回 503，客户端表现为「重新连接」，极易误判成某个上游源（如 Loomy）故障
type: pitfall
source: APIShow / wb2api-panel 上游跟进（2026-10-28）
date: 2026-10-28
verified: 2026-10-28
topic: api-gateway
---

# 生产机编译会触发 New API 过载护栏并误伤线上

## 经验

在 2 vCPU 的生产机上跑 `go build` / `go test` / `docker compose build`，会把 CPU 打满；
New API（rc.26）默认开启系统性能护栏（`Enabled=true`、CPU/内存阈值各 90%、需连续采样），
超过阈值时直接对 `/v1/*` 请求返回 **503**，body 约 **143 字节**、GIN 耗时 **~100µs**（没进渠道选择、DB 无日志）。

客户端（ZCode）看到 503 会重试 6 次后显示「重新连接 / 等待」，**看起来像所选中转源（本例 Loomy）故障**，
实际该源完全正常（直连同一模型 200 / 3.16s，24h 49 成功）。误判代价：白查一晚上上游。

## Why

- 503 是站点级拒流，不写 `logs` 表、nginx `ustatus=503`，只有 nginx access log 有痕迹；
- 按 provider 排查会看到「只有某个 provider 失败」，但那只是该 provider 恰好被客户端选中；
- 生产机只有 2 核，Go 编译默认并行吃满两核 ⇒ 任何一次构建都会触发；
- 用户侧感知是「正常发消息也要重新连接」，与源质量无关。

## How to apply

**下次在生产机做任何编译/测试前**，二选一限制 CPU：

```bash
# 只编译（Go 容器）
docker run --rm --cpuset-cpus=0 -v /opt/wb2api-panel-a:/src -w /src golang:1.26.10-alpine go test ./...
# 整套 compose 构建（systemd-run 把整个进程树 pin 到 1 核）
systemd-run --scope -p AllowedCPUs=0 docker compose build
```

或错峰/本地构建、`docker save` 传镜像。

**怀疑 503 时按 body 大小分类**（先看 nginx，不要先看源）：

```bash
sudo grep 'status=503' /var/log/nginx/apishow-access.log | grep 'T08:3' | head
# 143~144B + GIN ~100µs  → New API 过载护栏（CPU/内存）
# 203B 左右 + 9~12ms      → No available channel（真的没有可用渠道，换查 abilities/渠道状态）
```
对照构建时间窗：`docker images --format '{{.Repository}}:{{.Tag}} {{.CreatedAt}}'`。

护栏本身可调（`performance_setting.monitor_enabled` / 阈值），但生产配置变更需站主确认；
默认策略应是「改自己的构建姿势」，而不是关护栏。
