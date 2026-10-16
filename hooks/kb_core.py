# -*- coding: utf-8 -*-
"""agent-kb Hook 核心逻辑（平台无关）。

被各平台适配器（ZCode hooks.json 等）import 后调用。

⚠️ **本文件是消息文本与触发词的唯一真相源**。适配器（kb_hooks.py）只负责
   把这里的返回值塞进平台协议，**不得自己存一份文案或正则副本**——
   2026-10-02 之前 ZCode 就因为入口里存了文案副本而与本文件分叉。
   `kb_validate.py --check-triggers` 会核对适配器与 config.json 是否仍与本文件一致。

设计原则：
- 核心逻辑只做一件事：根据事件类型，把一段提醒文本输出给适配器
- 任何异常静默放行（exit 0 无输出），绝不阻塞 Agent 会话
- 触发词自过滤：UserPromptSubmit 在平台 matcher 不生效时，用正则补位
- 路径在运行时求值（Path.home()），不硬编码 "~" 字符串，非 POSIX 环境同样可用

参考：hook 注入链路拆三段 —— ① 平台回调点（hook_event_name）② 执行载体（command 进程）③ 平台消费的数据结构（stdout JSON 字段）
"""
import os
import re
import sys
from pathlib import Path

# 触发词环境变量：分号分隔的正则片段，与内置触发词取并集
TRIGGER_ENV_VAR = "AGENT_KB_TRIGGER"

# 内置触发词：命中其一即注入沉淀规程。
# 与 SKILL.md 的 description（语义层）互补：这里机械匹配保确定性，description 兜词表外口语。
# 2026-10-12 扩词：按「用户真实口语」补入（原 6 词覆盖不足，27 句实测仅 3 句命中）。
#   词表已归一为单真相源（config.json 的 matcher 由用户删除），改这一处即全机生效。
#   误触发有自愈条款兜底（注入文本含「若用户并非要求沉淀，忽略本提醒」）。
TRIGGER_PATTERN = re.compile(
    # —— 原 6 词 ——
    r"记住|沉淀|晋升|以后别|下次别|全局经验"
    # —— 沉淀意图口语 ——
    r"|值得记|记一下|记下来|记下这个|存起来|存进|写进知识库|进知识库|收进|收录"
    r"|引以为戒|长点记性|长记性|涨记性|做个笔记|记个笔记|备忘|留个档|留档"
    # —— 教训 / 复盘意图 ——
    r"|总结一下教训|总结教训|吸取教训|复盘|这个坑|踩的坑|踩过坑|最佳实践"
    # —— 纠错 / 防复发意图 ——
    r"|别再犯|不要再犯|别重犯|别再踩|下次注意|以后注意|以后这样做|以后就这么做|学到"
    r"|记录一下|记一笔"
    # —— 2026-10-16 全量历史消息扫描（4029 条真用户消息）实证新增 ——
    #   数据：去重 1208 条上旧词表命中 21、新词命中 32（+52%），新增覆盖逐条核实
    #   全为真沉淀意图，误报抽查为零。
    #   ① 纳入/记入系列（用户最高频的表达；限定组合避免「纳入号」误报）
    r"|纳入.{0,8}?(kb|KB|知识库|记忆)"
    r"|记入|订正记忆|更新记忆|修正记忆|修正kb|修正KB|补充记忆"
    #   ② 值得记/记录的变体
    r"|值得一记|记录下来|经验记录"
    #   ③ 教训泛化（实测零误报：只在「/kb 给予教训」「把难题域这轮的教训」出现）
    r"|给予教训|教训"
    #   ⑤ 需求/约束声明（用户 2026-10-16 指定；33+4 条历史实证全为需求声明语境：
    #      「我希望在不改变脚本路径的情况下优化」「我不希望…一条都收不到」）
    r"|我希望|不希望"
    #   ④ kb 状态确认疑问句（「修正kb了吗」「纳入开kb并更新了吗」）
    r"|(kb|KB|知识库|团队记忆).{0,10}?(了吗|了没)"
)

# 索引文件名
INDEX_FILENAME = "INDEX.md"

# 索引条目行形状：- [标题](相对路径) —— 一句话钩子
_INDEX_ENTRY_RE = re.compile(r"^\s*[-*]\s+\[[^\]]*\]\([^)]+\)")


def default_kb_path() -> Path:
    """运行时求值默认库路径，避免把 "~" 写死成字符串。

    优先读 AGENT_KB_PATH 环境变量，其次 Path.home() / ".agents" / "kb"。
    """
    env = os.environ.get("AGENT_KB_PATH", "").strip()
    if env:
        return Path(env).expanduser()
    return Path.home() / ".agents" / "kb"


def resolve_kb_path(kb_path=None) -> Path:
    """把调用方传入的 kb_path（str / Path / None）统一成 Path。"""
    if kb_path is None:
        return default_kb_path()
    return Path(str(kb_path)).expanduser()


def _fence_mark(stripped):
    """取一行代码围栏的开栏标记（连续反引号/波浪线串），非围栏行返回 None。

    取**完整前导串**而非固定 3 字符：```` 包 ``` 的嵌套里，内层 ``` 不应关闭外层。
    """
    if stripped.startswith("`"):
        return "`" * (len(stripped) - len(stripped.lstrip("`")))
    if stripped.startswith("~"):
        return "~" * (len(stripped) - len(stripped.lstrip("~")))
    return None


def index_entry_lines(text):
    """产出 INDEX.md 文本中的有效条目行（跳过代码围栏内的示例行）。

    这是「什么是条目行」的唯一实现：count_index_entries 与 kb_validate 的
    索引路径提取都必须走这里，避免两处围栏状态机各自漂移。
    旧版只认 ``` 且逐行翻转，``` ` ```` 嵌套会被内层提前闭合、~~~ 围栏完全
    不识别（2026-10-04 实测的漏数/多数形状）。
    """
    fence = None  # 当前围栏标记（` 或 ~ 的重复串）；None = 不在围栏内
    for line in text.splitlines():
        stripped = line.strip()
        mark = _fence_mark(stripped)
        if fence is None:
            if mark:
                fence = mark
            elif _INDEX_ENTRY_RE.match(line):
                yield line
        elif mark == fence:
            fence = None


def count_index_entries(kb_path=None) -> int:
    """统计 {kb_path}/INDEX.md 里的条目行数。

    索引缺失 / 不可读 / 无条目时返回 0 —— 永不抛异常，hook 不阻塞会话。
    只数条目行（`- [标题](路径)`），不数标题、说明、代码块内的示例。
    """
    index = resolve_kb_path(kb_path) / INDEX_FILENAME
    try:
        text = index.read_text(encoding="utf-8")
    except Exception:
        return 0
    return sum(1 for _ in index_entry_lines(text))


def get_trigger_pattern() -> re.Pattern:
    """内置触发词 + AGENT_KB_TRIGGER 环境变量（分号分隔的正则片段）取并集。

    逐片段校验：非法片段跳过并向 stderr 告警，同批合法片段照常生效——
    旧版整体 try/except 会在任一片段写坏时静默回退内置词表，把合法扩词一并吞掉，
    用户以为扩了词实际等于没扩（2026-10-04 实测确认过该行为）。
    """
    fragments = []
    env = os.environ.get(TRIGGER_ENV_VAR, "")
    for frag in env.split(";"):
        frag = frag.strip()
        if not frag:
            continue
        try:
            re.compile(frag)
        except re.error as exc:
            print(
                f"[agent-kb] 忽略 {TRIGGER_ENV_VAR} 中的非法正则片段 {frag!r}: {exc}"
                f"（同批其余片段仍生效）",
                file=sys.stderr,
            )
            continue
        fragments.append(frag)

    if not fragments:
        return TRIGGER_PATTERN

    try:
        return re.compile(TRIGGER_PATTERN.pattern + "|" + "|".join(fragments))
    except re.error:
        # 环境变量里的正则是坏的 —— 退回内置，别把 hook 拖挂
        return TRIGGER_PATTERN


def stop_reminder() -> str:
    """Stop 事件注入：会话收尾的沉淀提醒（用户 2026-10-04 注册 Stop 钩子）。

    开工有开工提醒、触发词有沉淀规程，唯独「收尾」没有任何提示——任务做完最容易
    忘记把新教训回流。这里补上最后一道：不判断该不该沉淀，只提醒一遍。
    """
    return (
        f"【kb 收尾钩子】本次会话若有**跨项目可复用**的教训/经验（踩坑与修法、"
        f"最佳实践），按 kb 技能规程沉淀进 {default_kb_path()}；"
        f"写入后必须见 kb_validate [PASS]。项目专属状态留项目 memory，不必入库。"
    )


def session_start_reminder(kb_path=None) -> str:
    """SessionStart 时注入的开工提醒。

    真读 {kb_path}/INDEX.md 统计条目数；库不存在时提示尚未初始化。
    """
    resolved = resolve_kb_path(kb_path)
    count = count_index_entries(resolved)
    # 就绪与否由 count 决定，但**不把数字印进注入文本**：那个数字随增删漂移，
    # 且 2026-10-02 之前两份拷贝正是因它不一致才分叉。需要条数随时查
    # count_index_entries()，kb_validate.py 就在用。
    # 显示真实路径：resolved 已是 resolve_kb_path() 的结果，直接印它。
    # 旧版写 `resolved == default_kb_path()` 判断——但 default_kb_path() 自己就读
    # AGENT_KB_PATH，两边恒等 ⇒ env 覆盖时文案仍印字面 "~/.agents/kb/"，
    # 用户以为在真库操作、实际读写的却是 env 指向的库（2026-10-04 分析已标记，
    # 本次 CI 红点正是它：env 覆盖后真实路径必须可见）。
    shown = f"{resolved}/"
    if count:
        head = f"全局经验库 {shown} 就绪。"
    else:
        head = f"全局经验库 {shown} 尚无条目（未找到可读的 INDEX.md）。"
    return (
        f"【kb 开工钩子】{head}"
        "动手前按任务关键词跑 `python ~/.agents/kb/kb_search.py <关键词>`"
        "（全文检索，症状词/口语也能命中；比扫 INDEX 快），命中读条目全文再干。"
    )


def user_prompt_reminder() -> str:
    """UserPromptSubmit 命中触发词时注入的沉淀规程。"""
    return (
        "【kb 沉淀钩子】用户本条消息疑似要求沉淀经验。执行："
        "1) 先 `python ~/.agents/kb/kb_search.py --similar 「本次内容关键词」` 查重（同族条目优先扩充现有文件而非新建）；若本条消息涉及既有主题，顺手 kb_search 该主题看有无同类既有教训；"
        "2) 按 kb 技能规程落盘（frontmatter: name/description/type/source/date/verified/topic；正文: 经验/Why/How to apply）；"
        "3) 更新 INDEX.md 并核对索引行数=实际文件数；"
        "4) ⛔ 跑校验器 `python ~/.agents/kb/kb_validate.py`，看到 [PASS] 才算完"
        "（报 [FAIL] 按它列的行逐条修，不要绕过、不要改校验器迁就条目）；"
        "5) 回报条目路径与索引行。若用户并非要求沉淀，忽略本提醒正常干活。"
    )


def should_trigger_user_prompt(prompt: "str | None") -> bool:
    """自过滤：当平台 matcher 不生效时，用正则判断是否注入沉淀规程。

    正则 = 内置触发词 ∪ AGENT_KB_TRIGGER 环境变量片段。
    """
    if prompt is None:
        return True  # 拿不到 prompt 就默认注入一次（保险）
    return bool(get_trigger_pattern().search(prompt))
