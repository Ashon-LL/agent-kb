# 派单 #2：kb_core 增强 + 测试 + 冒烟脚本

**仓库**：apigogo/agent-kb
**分支**：feat
**NPC 角色**：CodeBuddy
**时间预算**：≤ 45 分钟
**增量推送要求**：每完成一个文件就 commit + push，至少 5 次 commit

## 背景

仓库当前 kb_core.py 是**纯字符串工厂**——session_start_reminder 里的"条数以 INDEX.md 为准"是写死的，should_trigger_user_prompt 的触发词硬编码。零测试，无法验证 hook 输出对不对。

## 交付物

### P0. kb_core.py 真干活

1. session_start_reminder(kb_path) 真读 {kb_path}/INDEX.md 统计条目数输出，不再写死
2. should_trigger_user_prompt(prompt) 支持从 AGENT_KB_TRIGGER 环境变量加载自定义触发词（分号分隔正则片段），与内置正则取并集
3. 所有函数的 kb_path 参数默认值从 DEFAULT_KB_PATH = "~/.agents/kb" 改成运行时求值（Path.home() / ".agents" / "kb"），避免硬编码字符串在非 POSIX 环境下出问题

### P1. 单元测试

	ests/test_kb_core.py（Python unittest，零第三方依赖）：
- TRIGGER_PATTERN 命中测试（记住 / 沉淀 / 晋升）
- TRIGGER_PATTERN 不命中测试（随便写点正常话）
- session_start_reminder 真库统计测试（用临时目录造一个假 INDEX.md 验证条目数正确）
- AGENT_KB_TRIGGER 环境变量生效测试

	ests/test_trae_zcode_adapter.py：
- 正常 stdin JSON → stdout 是合法 JSON + 含 hookSpecificOutput
- 空 stdin → exit 0 无 stdout
- 畸形 JSON → exit 0 无 stdout
- SessionStart 事件 → 输出含"开工钩子"
- UserPromptSubmit + 触发词 → 输出含"沉淀钩子"
- UserPromptSubmit + 无触发词 → 无输出

运行方式：python -m pytest tests/ 或 python -m unittest discover tests/。

### P2. 冒烟测试脚本

scripts/smoke_test.py：
1. 伪造 SessionStart JSON 喂给 	rae_zcode_adapter.py
2. 伪造 UserPromptSubmit（带触发词）喂给适配器
3. 伪造 UserPromptSubmit（不带触发词）喂给适配器
4. 三种场景 stdout 都是合法 JSON 且字段正确才算 pass

运行方式：python scripts/smoke_test.py，最后打印 [PASS] 3/3 或 [FAIL] x/3。

## 验收标准

- [ ] kb_core.py 真读 INDEX.md 统计条目数
- [ ] AGENT_KB_TRIGGER 环境变量生效
- [ ] tests/ 下单元测试全部 pass
- [ ] scripts/smoke_test.py 能跑通 3/3
- [ ] 至少 5 次增量 commit 推到 feat 分支
