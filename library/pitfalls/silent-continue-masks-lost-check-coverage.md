---
name: silent-continue-masks-lost-check-coverage
description: 校验器用 config.get() 取不到键就 continue，改名后该校验被静默跳过而非报错——门禁仍全绿，漏检无声；跨名字引用的校验必须容忍命名后缀或显式登记，并有一条测试专门断言"改名的代价是仍能定位"
source: APIShow CodeArts 五渠道合并（2026-09-28，config adapter 键 codearts → codearts__ch177，compare_adapter_maps 静默跳过）
date: 2026-09-28
verified: 2026-09-28
topic: ci
type: pitfall

---

# 校验器 `continue` 掉缺项 = 门禁全绿地漏检

**经验**：校验循环里 `if adapter is None: continue` 这种写法，把「配置里确实没有这个适配器（合理）」和「键改名了所以我查不到（事故）」合并成同一个分支。改名之后该校验**整个被跳过**，门禁依旧全绿，而且不会有任何一条"找不到 X"的报错。

这是与「错误码静默」「权限错配伪装成未配置」同族的第三类：**失败路径本身没有信号**。

## 本案实测

`validate_model_config.py` 里：

```python
ADAPTER_SOURCE_CANDIDATES = {
    "codearts": [ROOT / "scripts" / "adapters" / "codearts_adapter.py"],
    ...
}
...
adapter = config.get("adapters", {}).get(adapter_name)
if adapter is None:
    continue
```

渠道合并后配置键从 `"codearts"` 变成 `"codearts__ch177"`（合并命名约定 `<来源>__<渠道后缀>`）。于是：

- `compare_adapter_maps()` 对 CodeArts **一行都不查**，返回 `[]`；
- 门禁 `validate OK`、ruff 全绿、unittest 全绿；
- 唯一的暴露方式是**测试自己 KeyError 了**（测试写的是 `config["adapters"]["codearts"]`，改键后抛 `KeyError: 'codearts'`）——即门禁漏检先被测试撞上，不是被门禁发现。

## 修法（已落地）

精确名优先、退化到前缀匹配，把「查不到」从静默变成可定位：

```python
def _find_adapter(config, source_key):
    adapters = config.get("adapters", {})
    if source_key in adapters:
        return adapters[source_key]
    for name, adapter in adapters.items():
        if isinstance(adapter, dict) and name.startswith(source_key + "__"):
            return adapter
    return None
```

代价为零，收益是：以后再把配置键改名，校验**仍然生效**，而不是无声降级。

配套测试断言要跟着改到真实键上（否则测的是 KeyError 而不是校验逻辑），并且保留一个「注入错误配置 → 必须报错」的用例——这条用例是门禁没漏检的唯一证据。

## How to apply

1. **审计自己的校验器时，先找 `is None: continue` / `if not X: continue` 类分支**，逐个问：这个 `continue` 是把「合理缺项」和「意外失联」分开了吗？
2. **跨命名空间引用配置键的校验（源码↔配置、服务↔端点、路由↔上游），一律做名称容错或显式登记**，不要让精确匹配静默失配。
3. **改键名之后主动跑一遍所有以该键为锚的校验/测试**，别等它们 KeyError。
4. **给每条关键校验配一个"注入错误配置必须报错"的用例**——它才是「门禁真在查」的证据。门禁绿只证明没查出错，不证明查过。
5. 判断「门禁可信」时要看它覆盖了什么，而不是它输出了什么。`OK` 和「我跳过了它」在输出上是同一个字符串。

**相邻教训**：静默失败的另外两族见 [[broad-oserror-swallow-hides-permission-misconfig]]（`except OSError: return None` 把「不存在」和「没权限」合并）、[[automation-artifacts-lie-existence-and-freshness]]（自动化产物存在性/新鲜度不可信）；错误码静默型见 [[newapi-rc26-channel-crud-shapes]]（`success=false` 但 HTTP 200）。
