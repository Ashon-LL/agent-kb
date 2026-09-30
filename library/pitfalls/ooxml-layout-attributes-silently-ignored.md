---
name: ooxml-layout-attributes-silently-ignored
description: Word/OOXML 四类"设了属性却不生效"的静默失效——字符单位覆盖磅值致悬挂缩进、固定行距裁掉图片与公式、长文本表列宽失衡折行、重存丢 tblW 致表格超版心
type: pitfall
source: cumcm_zcode（CUMCM 2026 A 题 Word 交付全程实测）
date: 2026-09-15
verified: 2026-09-15
---

**共同特征**：属性写进 XML 了、脚本自检全绿、Word 里却不对——**XML 计数与文本 diff 都查不出**，只能靠量测或目视。四条各附修法：

1. **`w:ind` 的 `*Chars`（字符单位）优先于磅值，且按错误基准换算**。同时写 `leftChars="200"` 与 `left="420"` 时，Word 采纳字符单位并换算成 **45pt**（期望 21pt），"首行 = left − hanging = 24pt"永远缩进一格——**把 `w:left` 改成多少都无效**。修法：`w:ind` **只写磅值** `w:left`/`w:hanging`，不写任何 `*Chars`；对既有 docx 用 Word COM 先 `CharacterUnitLeftIndent=0` 再设 `LeftIndent`/`FirstLineIndent`（顺序颠倒会被字符单位覆盖）。
2. **固定行距 `lineRule="exact"` 会裁切超高内容**：图片、含分式的**行内**公式、上下标都被截成一条（本项目积分上下限就这么丢的）。修法：图片段与公式段用 `lineRule="auto"`，含行内公式的正文段用 `atLeast`。另需给表格行 `w:cantSplit`、表头 `w:tblHeader`+`keepNext`、表题段 `keep_with_next`。
3. **列宽按内容估算在"≥2 列长文本"时失衡**：长文本列触到上限后其余列被压到下限、总宽超页，Word 再按 `tblW=100%` 等比缩回 → 表头折行、拉丁词被拦腰断开（实测 `WorkBudd/y`）。修法：在该表前加 opt-in 标记 `<!-- colwidths@N: 比例 -->`（N 为 1-based 表序号）直接采用，跳过估算；4 列长文案表还要把表头压到 4 字以内。
4. **Word 重存会丢 `w:tblW`**，只剩 `tblLayout="fixed"` → 表格右边缘超出页边距（本项目超 2.97pt/1.05mm，肉眼几乎看不出但确实越界）。修法：给 `tblW` 钉死 `type="dxa"` + 显式宽度。**量测方法**：Word COM `ExportAsFixedFormat(OutputFormat=17)` 导 PDF → 用 PyMuPDF 读表格边框矩形/文字行 x 坐标，与版心区间（A4+2.5cm 边距 = 70.87–524.41pt）比对，别靠目视。

**Why**：Word 对这些错误一律**沉默处理**（不报错、不提示），验证手段只剩"量测数字"或"逐页看图"（见 [[docx-pipeline-delivery-gotchas]]）。

**How to apply**：用 python-docx/pandoc 管线产出 docx 时，以上四项按"写完→量测→目视"三步验收；改动版式属性后必须回读 PDF 复核，不要只看 XML。
