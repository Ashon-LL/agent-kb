---
name: alibaba-src-assets-waf-block-probing
description: 阿里系SRC资产（盒马/千问等）有WAF，路径枚举式探测会被block_deny页拦截并留痕，必须极度轻量
type: pitfall
source: SRC挖洞项目（2026-09-21 盒马 portal.hemaos.com 探测实战）
date: 2026-09-21
---

**经验**：对阿里系 SRC 范围资产（盒马 hemaos.com、千问 qianwen.com、阿里云等）做暴露面探测时——

1. **路径枚举（/.git/HEAD、/swagger-ui.html、/actuator、/.env、/druid 等）会触发阿里 WAF**，返回 `waf_block_deny` 拦截页（特征：响应含 `gateway-diagnostic` JSON、`block_phase: pre-inspection`、跳转 dev.g.alicdn.com/sd/punish/）。拦截页 HTTP 状态可能是 200，**别把 WAF 页当"接口存在"**——必须看响应体特征。
2. 探测要**极度轻量**：单主机经典路径 ≤10 个、串行、加正常 UA；批量路径字典 = 扫描器行为，既违反 SRC 测试规范（荣耀等明令禁止，阿里协议同样约束）又会招致 WAF 封禁/IP 拉黑，后续正常业务请求也可能被拦。
3. 被 WAF 拦过之后**该主机暂停探测一段时间**，改从其他面突破（已登录功能、JS 扒接口、业务逻辑）。
4. 判断"接口是否真实存在"的三步：看响应体是否 JSON/HTML 业务内容 → 跟 302 的 Location → 与已知正常页面对照。WAF 页、SPA 兜底页（任何路径 200 返回同一 HTML 壳）、登录跳转页是三种最常见的假阳性。

**Why**：实战中对 portal.hemaos.com 批量探测 11 个路径，全部撞 WAF（block_deny），不仅零收获，还在对方 WAF 留下记录；而同样的轻量接口请求（如已确认的 /api/v1 正常业务接口）并未被拦——说明 WAF 对"探测器特征路径"敏感、对正常 API 路径宽容。SRC 挖洞的合规底线（不用扫描器）本身就是最好的反封禁策略。
