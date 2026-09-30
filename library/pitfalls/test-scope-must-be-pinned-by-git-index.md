---
name: test-scope-must-be-pinned-by-index-not-walk
description: 测试的「扫描范围/环境前提/宽松断言」三者任一不当，都会产出看环境脸色的假红单或假绿单；范围钉在 git 索引、前提显式屏蔽、断言要能被变异验证
type: pitfall
source: MH-Agent-Open（2026-09-18：ps1 BOM 测试被 .venv311/node_modules 打红；openclaw 解析测试被本机实装件打红且宽松断言让变异漏网）
date: 2026-09-18
verified: 2026-09-18
topic: git, ci
---

**经验**：凡是「仓库里每份 X 都必须满足约定 Y」的测试（BOM/EOL/编码/文件头/命名），
**扫描范围必须来自版本控制索引**（`git ls-files "*.ps1"`），不能用磁盘遍历。

**为什么**：磁盘遍历会把 `.gitignore` 排除的东西一并扫进来 —— 虚拟环境、`node_modules`、
工具自动生成的脚本。这些东西**本仓既无约定也无控制权**，它们的格式由上游决定。
后果不是一个 bug，而是一条**看环境脸色的假红单**：

| 环境 | 结果 |
|---|---|
| 干净 CI | 绿（没有 .venv/node_modules） |
| 开发者本机（装过依赖） | 红 |

⇒ 开发者学会「这条红是正常的、忽略它」，然后**真正的违规也从这条漏过去**。
这比没有测试更糟：它把注意力训练没了。

**实测案例**（MH-Agent-Open 2026-09-18）：`test_ps1_scripts_are_bom_crlf` 用
`_ROOT.rglob("*.ps1")` 扫描，报 4 条违规，**全部**来自 gitignored 目录：

```
.analysis/.venv311/Scripts/activate.ps1         缺 BOM + 无 CRLF
.analysis/cnb-docs/cnb-skill/install.ps1        无 CRLF
backend/tools/docx-cn-engine/node_modules/.bin/fxparser.ps1   缺 BOM
```

前两条是 pip 装的第三方包，第三条是 npm 装的。仓库自己写的 `.ps1` 全都合规。

**正确写法**

```python
def _contract_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "*.ps1"],
                         cwd=_ROOT, capture_output=True, text=True)
    return [Path(p) for p in out.stdout.splitlines() if p.strip()]
```

⛔ **别用目录名黑名单**（排除 `.venv`/`node_modules`/`__pycache__`…）：黑名单永远会漏 ——
换个 venv 目录名、多一个 node_modules、出现 `dist/`、`build/`、`.tox/`、`target/` 就复发。
而且语义上本来就该按「是否入库」划界：gitignored 文件不随仓库分发，不受仓库约定管辖。

**⛔ 必须另加一条元断言（关键）**：范围本身也会被后来者无意改回去（「用 rglob 简单点」），
而**范围退化不会让任何正常用例变红** —— 直到某人本机装了虚拟环境才炸，中间可能有几个月
完全静默。用一条测试把范围钉死：

```python
def test_contract_scope_is_tracked_only():
    files = _contract_files()
    assert files
    polluted = [str(p) for p in files
                if any(part in {".venv", "venv", "node_modules", "__pycache__"}
                       for part in p.parts)]
    assert not polluted
    authoritative = {Path(p) for p in subprocess.run(
        ["git", "ls-files", "*.ps1"], cwd=_ROOT,
        capture_output=True, text=True).stdout.splitlines() if p.strip()}
    assert {Path(p) for p in files} == authoritative
```

**配套坑**：
- 比等号时**两侧都转 `Path`**：Windows 上 `Path("a/b")` 的 `str()` 是 `a\b`，直接字符串比必假红；
  `git ls-files` 又永远输出 `/` 分隔符 ⇒ 拿它的字符串和 `Path` 比是同样的坑。
- 这类「范围/判据本身」的断言要**做变异验证**才算数：把实现改回 `rglob` 跑一次，
  必须变红；恢复后必须全绿。否则你不知道这条元断言是否空跑。

**How to apply**：写任何全仓库扫描型断言前先问一句「这个范围包含我无权约定的东西吗」。
范围取 git 索引，范围本身再钉一条元断言，并对元断言做变异验证。
相关：[[oneoff-script-file-edit-rules]]、[[automation-artifacts-lie-existence-and-freshness]]。

---

## 同一家族的两个兄弟错法（2026-09-18 同日第二例）

上面那例是**扫描范围**错。同日又撞到两条**同一家族、不同错法**的，一并记下——

### 错法 B：「环境前提」写死在测试里，但环境会变

```python
def test_openclaw_bin_resolver_returns_bare_name_when_absent(monkeypatch):
    """全解析失败 → 裸名。"""
    monkeypatch.setattr(se.shutil, "which", lambda n: None)        # 屏蔽 PATH
    monkeypatch.setattr(se, "_openclaw_npm_global_candidates", lambda: [])  # 屏蔽全局 npm
    got = se.resolve_openclaw_bin({})
    assert got in ("openclaw", "openclaw.cmd", "openclaw.exe") or got.endswith("openclaw")
```

被测函数 `resolve_openclaw_bin` 有 **4 段**解析顺序，测试只屏蔽了第 3、4 段，
漏了第 2 段「**安装区 runtime**」——它从 `ROOT_DIR.parent` 推安装根、直接扫
`runtime/node/node_modules/openclaw/openclaw.mjs`，**不经过 `which`**。

⇒ 开发机装过 openclaw（runtime 里有实装件）→ 返回该绝对路径 → **必红**；
干净 CI 没装 → **必绿**。又是假红单。

⛔ **修法不是放宽断言去迁就环境**（那样「全失败返回裸名」这条契约就再也测不到了），
而是**把被测函数真正用到的入口全部屏蔽**。这里最干净的形态是改根：

```python
fake_backend = tmp_path / "install" / "backend"
fake_backend.mkdir(parents=True)
monkeypatch.setattr(se, "ROOT_DIR", fake_backend)   # install_root 下什么都没有
```

—— 与生产走同一条代码路径，只换根。**比逐个 stub 内部候选更稳**（增加第 5 段解析时不会又漏）。

### 错法 C：断言里的 `or` 分支是**假网眼**（最隐蔽）

上面那条的断言尾巴 `or got.endswith("openclaw")` 看着是「宽容一点」，实际是
**把要守的契约整个放掉了**：

| 实现返回值 | `in (裸名)` | `endswith("openclaw")` | 结果 |
|---|---|---|---|
| `"openclaw"` | ✅ | ✅ | 过（正确） |
| `"/bogus/absolute/path/openclaw"` | ❌ | ✅ | **过（错误！）** |

而被测函数的 docstring 写的恰恰是「**不要**返回一个不存在的绝对路径」——
即这个 `or` 分支把唯一要防的错法防漏了。

⛔ **只有做变异验证才会发现**：把实现改成返回假绝对路径跑一次 —— 原本「45 passed」
纹丝不动，才发现断言是空的。改成严格比裸名后，变异立刻被捕获。

**How to apply（三条一起用）**：
1. 范围类断言 → 取版本控制索引，别走磁盘。
2. 前提类断言 → 屏蔽**被测函数真实用到的全部入口**，最稳的形式是 monkeypatch 根路径；
   排查方法 = 打开被测函数，把它 `return` 前的每一段解析路径逐条对照测试的 stub 清单。
3. **任何断言都要能通过变异验证**：故意改坏实现，断言必须变红。改不红就是假网眼。
   尤其警惕 `or` / `any()` / `in (多个候选)` 这类**放宽型写法**——它们天然掩盖变异。


关联 [[silent-continue-masks-lost-check-coverage]]。
