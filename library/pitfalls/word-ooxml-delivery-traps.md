---
name: word-ooxml-delivery-traps
description: Word/docx 交付管线与 OOXML 静默失效：字号/行距/表宽、子元素顺序、draw.io 0 字节、WinRAR 中文路径
type: pitfall
source: 合并自 docx-pipeline-delivery-gotchas, ooxml-layout-attributes-silently-ignored；cumcm_zcode（CUMCM 2026 A 题交付全程）; cumcm_zcode（CUMCM 2026 A 题 Word 交付全程实测）
date: 2026-09-14
verified: 2026-09-15
topic: office, delivery
---
**经验**：Word/docx 交付管线与 OOXML 静默失效：字号/行距/表宽、子元素顺序、draw.io 0 字节、WinRAR 中文路径

> 本条由 2 条同族条目合并；原文判据、反例与实测命令保留在下面各节。

## docx-pipeline-delivery-gotchas

**经验**（管线生成 docx 交付的通用坑，任何 Word/docx 项目适用）：

- **绝不在 Word 里直接保存管线产出的 docx**：Word 重存会静默丢显式字号设定与三线表边框设置（文本 diff 查不出，段落完全一致），比对要看 `w:sz` 集合、`w:(top|bottom|insideH|insideV)` 线宽集合、`wp:extent` 图宽。要改图宽就回写主源重建。
- **附录源码与磁盘代码逐字节一致是红线**：出稿后改 code/ 或画图脚本，必须重生成附录再重建 docx。
- **draw.io CLI 导出**：cell id 取名 `map` 会返回码 0 却产出 **0 字节 PDF**——导出后必须校验文件大小；value 里的 `<sub>` 要二次转义。PNG 先出矢量 PDF 再 PyMuPDF 300dpi 转。
- **OOXML 子元素顺序硬约束**：`w:pPr`/`m:r` 乱序会被 Word 静默忽略（"设了字号却无效"）；OMML 公式字号只能写在每个 `m:r` 内部的 `w:rPr/w:sz`。
- **目视验收不可省**：只核验 XML 计数会漏图被裁、公式不居中、CJK 空格；出 docx 后转 PDF→逐页 PNG 看图。
- **WinRAR 中文路径**：`@listfile` 按系统 ANSI 码页解析，UTF-8 清单会 rc=10 但归档仍生成（极易误判）——路径直接作命令行参数传（UTF-16 无损），核验用 `Rar.exe t`+成员名逐条比对。
- **Python 字符串写 LaTeX**：`\nu`/`\times`/`\frac` 变控制字符静默破坏正文，用 `chr(92)` 拼反斜杠，插入后扫 `ord(c)<32`。
- **matplotlib**：SimHei 缺 U+2212 负号字形，对数轴改纯文本 `FuncFormatter`；大数据热图先降采样（否则矢量 PDF 上百 MB）。
- Word COM 导 PDF 偶发失败（`Visible=False` 报 AttributeError），重试一次通常即可。
- **行距/缩进/表格四类"设了不生效"的静默失效**（`exact` 裁图裁公式、`*Chars` 覆盖磅值、列宽失衡、重存丢 `tblW` 超版心）已独立成条 [[word-ooxml-delivery-traps]]，管线交付时四条一并按它验收，勿凭本节二手摘要行事；**图的图例遮挡与"图离引用句太远"**见 [[figure-geometry-and-placement]]。

## ooxml-layout-attributes-silently-ignored

**共同特征**：属性写进 XML 了、脚本自检全绿、Word 里却不对——**XML 计数与文本 diff 都查不出**，只能靠量测或目视。四条各附修法：

1. **`w:ind` 的 `*Chars`（字符单位）优先于磅值，且按错误基准换算**。同时写 `leftChars="200"` 与 `left="420"` 时，Word 采纳字符单位并换算成 **45pt**（期望 21pt），"首行 = left − hanging = 24pt"永远缩进一格——**把 `w:left` 改成多少都无效**。修法：`w:ind` **只写磅值** `w:left`/`w:hanging`，不写任何 `*Chars`；对既有 docx 用 Word COM 先 `CharacterUnitLeftIndent=0` 再设 `LeftIndent`/`FirstLineIndent`（顺序颠倒会被字符单位覆盖）。
2. **固定行距 `lineRule="exact"` 会裁切超高内容**：图片、含分式的**行内**公式、上下标都被截成一条（本项目积分上下限就这么丢的）。修法：图片段与公式段用 `lineRule="auto"`，含行内公式的正文段用 `atLeast`。另需给表格行 `w:cantSplit`、表头 `w:tblHeader`+`keepNext`、表题段 `keep_with_next`。
3. **列宽按内容估算在"≥2 列长文本"时失衡**：长文本列触到上限后其余列被压到下限、总宽超页，Word 再按 `tblW=100%` 等比缩回 → 表头折行、拉丁词被拦腰断开（实测 `WorkBudd/y`）。修法：在该表前加 opt-in 标记 `<!-- colwidths@N: 比例 -->`（N 为 1-based 表序号）直接采用，跳过估算；4 列长文案表还要把表头压到 4 字以内。
4. **Word 重存会丢 `w:tblW`**，只剩 `tblLayout="fixed"` → 表格右边缘超出页边距（本项目超 2.97pt/1.05mm，肉眼几乎看不出但确实越界）。修法：给 `tblW` 钉死 `type="dxa"` + 显式宽度。**量测方法**：Word COM `ExportAsFixedFormat(OutputFormat=17)` 导 PDF → 用 PyMuPDF 读表格边框矩形/文字行 x 坐标，与版心区间（A4+2.5cm 边距 = 70.87–524.41pt）比对，别靠目视。

**Why**：Word 对这些错误一律**沉默处理**（不报错、不提示），验证手段只剩"量测数字"或"逐页看图"（见 [[word-ooxml-delivery-traps]]）。

**How to apply**：用 python-docx/pandoc 管线产出 docx 时，以上四项按"写完→量测→目视"三步验收；改动版式属性后必须回读 PDF 复核，不要只看 XML。
