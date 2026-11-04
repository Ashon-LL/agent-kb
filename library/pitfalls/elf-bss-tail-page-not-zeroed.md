---
name: elf-bss-tail-page-not-zeroed
description: ELF 的 p_memsz 之后那部分“看着像 .bss”的页由 ld.so 只清到文件数据页尾，后续内容是文件页残留（.symtab 等），不能当 0 用
type: pitfall
source: 2026 强网杯 babysilent（PWN，盲打）
date: 2026-10-31
verified: 2026-10-31
topic: reverse-engineering
---

## 经验

程序以 PIE 方式被 ld.so 加载时，**不要假设 `p_memsz` 之后的虚拟地址是 0**。

- 内核只对“主程序/解释器自己做映射”的段做整页清零；PT_LOAD 段由 ld.so 映射时，
  零填充只覆盖“文件数据结尾所在那一页的剩余部分”（padzero 语义），
  更靠后的页保持**文件页残留**（典型是 `.symtab` / `.strtab` / `.comment` 的内容）。
- 于是 `readelf -S` 里 `NOBITS` 之外的“空白”区域、以及段尾之后的映射页，
  运行时常有非零垃圾。要用先 dump 再下结论：
  `/proc/<pid>/mem` 读目标地址，或 gdb `x/32bx <addr>`。

实测（2026 强网杯 babysilent，pwn 二进制 RW 段 `vaddr=0x600d40 filesz=0x2d0 memsz=0x310`，
可写页 `0x601000-0x602000`）：

```text
base+0x601400: 66 6c 61 67 00 00 13 00 40 0d 60 00 ...   # 0x13 / 0x600d40 是 .symtab 里的值
```

即 `0x601050`（段 memsz 末尾，页内）之后并不是 0，而是符号表内容。

## Why

盲打 / 无输出 pwn 常用“把内存里的一个字当作长度/下标”的手法（例如把
`*(u32*)(buf+i)` 读进 size 寄存器）。如果 `buf` 之后不是 0：
长度会变成天文数字，进程卡在超大循环里、连接超时不返回，
**本地和远端表现一致，很容易被误判成利用链写错了**，浪费大量时间。

## How to apply

1. 需要某个缓冲区“后面必须是 0”时，自己在链里先写 NUL：
   例如抢到 ROP 后先 `read(0, buf, N)` 并发送 N 个 `\x00`，再 `read(3, buf, i+1)`
   读真实数据，这样窗口的高位就确定是 0。
2. 也可以只用确实落在 `memsz` 内的 .bss（通常只有几十字节）。
3. 下结论前一定先看运行时的真实内容：gdb `x/` 或 `/proc/<pid>/mem`，
   不要只依赖 `readelf -S` 的 section 视图。
