---
name: research-slide-deck-image-only-pages
description: 行业协会/发布会网页正文只有标题而关键数字在图片或PDF附件里；用联系表+OCR+逐页看图核数，并把原文直给值与派生值分开
type: pitfall
source: 10years-humanity EP07 G2 汽车数据核查
date: 2026-11-15
verified: 2026-11-15
topic: verification
---

## 经验

做数据调研时，若 HTML 正文只有标题、没有数字，不要据网页抽取工具的空正文判定「页面无数据」。先检查页面源码中的图片、附件 PDF、iframe 或图片列表；把发布页图片按顺序下载并合成联系表，定位候选页，再用 OCR + 逐页 Read 核读。对 PDF 同时跑 `pdftotext -layout` 与 PyMuPDF 逐页文本；中文发布会图片可能 OCR 缺字，关键数字要回到原图肉眼确认。

数据包里把「原文直给值」和「由其他数字算出的派生值」分开：每条观测写 `value/year/source_id/url/basis`，派生值另写 `expression/formula/inputs` 并自动重算。若不同月份发布会的同一历史数字有修订，采用最新年度发布会终值，在冲突表记录旧值和采用理由。

## Why

EP07 汽车 G2 核查时，中汽协 2025 年 12 月发布页 HTML 正文只有标题，42 个关键页全是图片；仅用网页抽取会漏掉 2730.2 万国内销量、1342.7 万传统燃料国内销量、1387.5 万新能源国内销量、50.8% 国内渗透率、261.5/448.3 万出口拆分、69.5% 中国品牌份额。把图片合成 PDF 后 OCR 曾因远程连接失败，最后靠联系表定位 p25–p29 并逐张 Read 静态页确认。若不区分直给与派生，会把 `2730.2-1342.7=1387.5` 误写成媒体推算值。

## How to apply

遇到「页面标题正确但正文没数字」的统计发布页：①查图片/附件链接并下载快照；②生成低分辨率联系表定位页段；③用 OCR 做检索、用原图逐页目检关键数字；④把直给值、派生值、冲突值分别落盘；⑤审计脚本必须重算全部公式并检查 source_id/URL 一致性。相关：[[dark-field-keyframes-thin-line-flow-false-empty]]。
