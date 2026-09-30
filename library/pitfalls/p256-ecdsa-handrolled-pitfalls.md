---
name: p256-ecdsa-handrolled-pitfalls
description: 纯标准库手写 P-256 ECDSA/DPoP JWS 的四个坑——曲线是 a=-3 不是 a=0（点加倍会「静默正确」地落到曲线外）、JOSE ES256 签名是裸 r‖s 非 DER、cryptography 的 SECP256R1() 不暴露曲线参数、JWS 紧凑序列化必须用 separators=(",",":")
type: pitfall
source: APIShow CodeArts STS 凭据体系改造（2026-09-28，为对齐 gitee deepseek-harness-codearts 的 DPoP 签名手写 P-256，零第三方依赖）
date: 2026-09-28
verified: 2026-09-28
---

**经验**：需要在无第三方依赖的环境（生产服务器只装标准库）里手写 ECDSA 签名时，有四个坑会让代码「看起来对、验签必错」：

1. **P-256 曲线方程是 `y² = x³ − 3x + b`，即 `a = −3`，不是教科书常见的 `y² = x³ + b`。**
   初版写 `a = 0` 时，点加倍斜率 `(3x² + a) / (2y)` 仍然「能算」，只是算出来的点不在曲线上——`n*G` 永远不是无穷远点，`verify()` 也永远过不了，但代码不会抛任何错。
   **定位手段**：先断言 `G` 本身满足曲线方程（`y² ≡ x³ + a*x + b`），再用 `cryptography` 反解真实参数交叉验证：
   取 `d = N-1` 则 `P = (Gx, -Gy mod p)`；由 `b' = y² − x³` 反解出真实 `b`，再核对 `b − 3² ≡ 已知 b`，即可断定 `a = ±3`。
   曲线参数常量见 RFC 5480 / SEC 2 Appendix 3.2.6.1，`a = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC`。

2. **JOSE 的 ES256 签名是裸 `r ‖ s`（32+32 字节大端拼接），不是 DER 编码。**
   与 `cryptography` 交叉验证时必须先 `DER → r‖s` 转换，否则签名「长度对、内容错」。反过来验证 JOSE 签名时用 `ec.ECDSA.from_der()` 会直接失败。

3. **`cryptography` 的 `ec.SECP256R1()` 不暴露曲线参数。**
   只有 `.group_order` / `.key_size` / `.name`；**没有** `.b` / `.a` / `.field_size` / `.order` / `.generator`，也没有 `EllipticCurvePrivateNumbers.from_private_value`。
   要从私钥取公钥用 `ec.derive_private_key(d, ec.SECP256R1())`，曲线参数请硬编码常量或从 RFC 抄，别指望 API 给你。

4. **JWS 紧凑序列化的 JSON 必须用 `separators=(",", ":")` 且无空格**，否则 base64url 之后的签名输入和标准库/参考实现逐字节不同，签名全部作废。同理 `iat` 必须是整数字符串秒（不是浮点），`jti` 是随机 hex。

**交叉验证的三条正确性判据**（不依赖任何记忆里的测试向量）：
   - `G` 满足曲线方程；
   - `n * G` 等于无穷远点（点群阶为素数）；
   - 取一批随机标量（含 `1, 2, 3, 2**32, 2**128, n−1, n//3` 等边界）与 `cryptography` 逐点比对。
   这三条同时成立就可以相信自己的实现，**不要凭记忆硬编码 SEC 2 附录 D 的测试向量**——记错的概率比写错代码还高（本轮就记错过一个 `nGx`）。

**How to apply**：手写椭圆曲线前先把 `a`、`b`、`G`、`n` 四个常量写死并从 RFC 核对；用上面三条判据验证而不是抄测试向量；签名格式先确认目标是 DER 还是裸拼接（JOSE/DPoP = 裸，传统 X.509/CMS = DER）；`cryptography` 只用来做交叉验证的基准，不从它身上取曲线参数。DPoP 头的 `htm`/`htu`/`iat`/`jti` 四个声明一个都不能少，`jwk` 直接内联公钥（`kty/crv/x/y`，不含 `d`）。

关联：`pitfalls/dont-handroll-spec-encoders-use-libraries-plus-fallback.md`（同一族：手写规范编码器要留交叉验证基准）。
