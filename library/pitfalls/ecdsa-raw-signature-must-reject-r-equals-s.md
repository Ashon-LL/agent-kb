---
name: ecdsa-raw-signature-must-reject-r-equals-s
description: 纯标准库 ECDSA 签名循环只判 r==0/s==0 会漏掉 r==s，撞上时直接返回数学上无效的签名（公钥验签 InvalidSignature），且 while 循环不会重来——等于静默产出一次认证失败
type: pitfall
source: APIShow（2026-10-02 codearts_sts.py P-256 偶发验签失败）
date: 2026-10-02
verified: 2026-10-02
topic: security
---

# ECDSA 手写签名：r==0 / s==0 / r==s 三个都要拒

## 症状：单测偶发红，重跑就绿

```
tests/test_codearts_sts.py::TestPurePythonP256::
  test_keypair_and_signature_cross_check_with_cryptography
E   cryptography.exceptions.InvalidSignature
```

单跑 5 次全过、全量跑偶发红。**不要当 flaky 放过**——它每次复发都是真在产出坏签名。

## 根因：nonce 重试条件漏了第三种退化

```python
while True:
    k = ...nonce...
    r = point[0] % N
    if r == 0:            # ✅
        continue
    s = pow(k, -1, N) * (z + r * d) % N
    if s == 0:            # ✅
        continue
    return r.to_bytes(32,"big") + s.to_bytes(32,"big")   # ❌ r==s 时直接返回坏签名
```

ECDSA 要求 `r ≠ 0`、`s ≠ 0`、**`r ≠ s`**。第三种退化概率极低（≈2⁻²⁵⁶），
但一旦撞上：循环条件不覆盖 → 直接 return → 验签必失败。
生产含义是一次**静默的认证失败**（签名发出去了，对端拒了，日志里看不出是本地 bug）。

## How to apply

- 手写 ECDSA 循环，重试条件写成 `if s == 0 or r == s: continue`。
- 参考实现（Go `crypto/ecdsa`、Python `cryptography`）都会显式跳 `r == s`，别只抄一半。
- 压力验证比单测更早暴露：连签 300 次、逐次公钥验签，比跑 5 遍单测可信。
- **加固项（本条未做）**：`s` 低 S 归一化（`if s > N//2: s = N - s`）防签名 malleable；
  JOSE 场景一般不强制，但同一消息能出两个有效签名本身不是好性质。

关联 [[redaction-must-key-on-field-not-value]]、[[dont-handroll-spec-encoders-use-libraries-plus-fallback]]。
