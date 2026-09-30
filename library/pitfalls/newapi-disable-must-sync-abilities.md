---
name: newapi-disable-must-sync-abilities
description: New API 的 abilities 表是唯一路由事实源，docker restart 不会重算它；禁用渠道、改 channels.group 都必须手工重建 abilities，且 INSERT 时占位符顺序极易错位导致整批渠道静默不可路由
type: pitfall
source: APIShow/New API（2026-09-17 扩充条目：改 channels.group 同样要手工重建 abilities）
date: 2026-09-17

---

# New API：abilities 是路由唯一事实源，restart 不重算它

## 现象

admin API 关闭（`PasswordLoginEnabled=false`）时渠道状态只能 SQL 直写 + `docker restart` 刷缓存。但 **restart 不会重算 `abilities` 表**——改完 `channels.status=0` 后，`abilities` 里该渠道的行仍是 `enabled=1`。

New API 以 `abilities.enabled` 为主筛：行还在，路由器就会先选中这个 channel_id，取到 channel 发现 `status≠1` 再跳过。等价于**没禁干净**，还可能白耗一跳或走进不同的错误分支。

## 本库惯例

渠道非启用 → abilities 标记也置 0。实测印证：手动禁用的渠道其 abilities 行全为 `enabled=0`。

## ⚠️ status 码语义随版本变过，动手前先核当前版本（2026-09-26 修正）

本条最初按旧语义写「0=手动禁用、2=自动禁用」——**那是错的**。rc.26 实测语义（`common/constants.go`，upstream main 同值）：

| 值 | 含义 | API 可管理 |
|---|---|---|
| `0` | Unknown（源码注释：don't use 0, 0 is the default value!） | ❌ 拒绝 |
| `1` | Enabled | ✅ |
| `2` | **ManuallyDisabled（手动禁用，可逆）** | ✅ |
| `3` | AutoDisabled | ❌ 拒绝 |

`POST /api/channel/{id}/status` 的校验是 `isManageableChannelStatus` = 只收 `1`/`2`；传 `0` 返回 HTTP 200 但 `{"message":"Invalid parameters","success":false}`，**一个字段都没改**。「0=手动禁用」这个直觉会让禁用操作静默落空，所以动手前必须确认成功标志，不能只看 HTTP 码。

核对方法：查部署版本的 `constants.go`，或看库里已被前端手动禁用的渠道是什么值。2026-09-26 实测：5 个渠道 API 置 `status=2` 全 `success=true`，回读 `status=2` + `abilities.enabled=0`，且**前台 `/api/channel/` 立刻读到新值**——该接口会调 `InitChannelCache()`，**禁用不用重启**（与上文「admin API 关闭时才需 restart」区分）。

## How to apply

标准动作三步：

```sql
UPDATE channels SET status=2 WHERE id IN (...);   -- 2=手动禁用（rc.26）；0 是 Unknown，别写
UPDATE abilities SET enabled=0 WHERE channel_id IN (...);
```

然后 `docker restart apishow-new-api`，回读时查三态交叉汇总：

```sql
SELECT ch.status, ab.enabled, COUNT(*) FROM abilities ab
JOIN channels ch ON ch.id=ab.channel_id
GROUP BY ch.status, ab.enabled;
```

结果应只出现 `(1,1)`（启用）、`(2,0)`（手动禁用）、`(3,0)`（自动禁用），历史库可能还留着旧语义的 `(0,0)` 行。出现 `(2,1)`、`(3,1)` 或 `(0,1)` 就是漏了第二步。

**只置标记，不删行**：禁用后复活只需 `status=1 + enabled=1`。只有**删除**渠道才 `DELETE FROM abilities WHERE channel_id IN (...)`——残留行会让已删的 channel_id 留在候选集里。禁用与删除在这一步方向相反，别混用。

## 改 `channels.group` 时同样要手工重建 abilities

`channels.group` 只是数据来源，路由器只查 `abilities`（`WHERE group=? AND model=? AND enabled=1`，按 `priority DESC, weight DESC`）。改 group 后不重建 abilities，就是"改了配置但一条路都没通"。

照上游 `model/ability.go` 的 `UpdateAbilities` 语义重建：先 `DELETE FROM abilities WHERE channel_id=?`，再逐行 INSERT（`OnConflict DoNothing`），字段值取：

- `Enabled = (channels.status == 1)`
- `Priority = channels.priority`
- `Weight = channels.weight`
- **`Tag = channels.tag`** —— 取自 channels 表，**不从兄弟行继承**（旧数据里 channels.tag 与 ability.tag 可能不一致，重建后按上游约定以 channels 为准；tag 不参与路由）

`group` 是 SQL 保留字，**列名列里必须引号化**，否则 INSERT/SELECT 直接语法错误。

## INSERT 占位符与列顺序错位会静默产出不可路由行

本表事故：`INSERT INTO abilities (group,model,channel_id,enabled,priority,weight,tag) VALUES (?,?,?,?,1,?,?)` —— 字面量 `1` 占的是 priority 槽位，于是第 4 个占位符（渠道 priority）落进了 `enabled`。结果 16 行全写成 `enabled=4/5/2/0`、`priority=1`。

**症状极隐蔽**：行数、group、model 看起来都对。但路由过滤条件是 `enabled = 1`（SQLite `numeric` 列），`4/5/2/0` 被静默全部丢弃，等于这些渠道整条路不通。

排查曾一度怀疑上游有列顺序 bug，拉源码才证实：`Ability` struct 字段顺序与表列顺序完全一致（`Group, Model, ChannelId, Enabled, Priority, Weight, Tag`），bug 在自己写的 SQL。**教训：别把"行数对"当验收。**

验收三步，缺一不可：

1. 逐行回读 `(group, model, channel_id, enabled, priority, weight)`，确认 `enabled` 全为 1、`priority`/`weight` 等于渠道值；
2. 没动过的渠道行逐字节未变；
3. 按 `(group, model)` 汇总出路由视图，确认每个期望模型在该组至少 1 条 enabled 渠道。

## 相关

- [[newapi-base-url-never-carry-v1]]（同一批 New API 反直觉行为）
- [[newapi-multikey-size-must-track-key-count]]（同样是"两处状态必须一致，改一处不生效"）
