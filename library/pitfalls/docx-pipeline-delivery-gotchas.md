---
name: docx-pipeline-delivery-gotchas
description: Word/docx 交付管线实测坑：Word 重存丢字号、附录同步红线、draw.io 0 字节导出、OOXML 子元素顺序、WinRAR 中文路径
type: pitfall
source: cumcm_zcode（CUMCM 2026 A 题交付全程）
date: 2026-09-14
---

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
- **行距/缩进/表格四类"设了不生效"的静默失效**（`exact` 裁图裁公式、`*Chars` 覆盖磅值、列宽失衡、重存丢 `tblW` 超版心）已独立成条 [[ooxml-layout-attributes-silently-ignored]]，管线交付时四条一并按它验收，勿凭本节二手摘要行事；**图的图例遮挡与"图离引用句太远"**见 [[figure-placement-and-legend-occlusion]]。
