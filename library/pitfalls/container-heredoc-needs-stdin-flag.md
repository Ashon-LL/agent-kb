---
name: container-heredoc-needs-stdin-flag
description: docker exec / ssh 管道里 here-doc 不转发 stdin 会零输出零报错，极易误判成"代码没执行"
type: pitfall
source: 日常沉淀 2026-09-18（here-doc 喂 docker exec/ssh 静默丢 stdin）
date: 2026-09-18
verified: 2026-09-18
topic: container, security
---

在管道命令里用 here-doc 喂容器内进程时，**`docker exec` 默认不转发标准输入**：

```bash
# 坏：零输出、零报错，看起来像"什么都没发生"
ssh host "docker exec mycontainer python - <<PY
print('hello')
PY"

# 好
ssh host "docker exec -i mycontainer python - <<PY
print('hello')
PY"
```

**症状特征**：命令正常退出（exit 0）、stderr 空、stdout 空。没有 `Error`、没有 `command not found`。第一次遇到极易往"代码有 bug / 输出被吞 / 引号被吃掉"方向排查，白烧一轮。

**同类静默丢 stdin 的位置**（都是"管道没接上"而非"命令错了"）：

- `docker exec` 缺 `-i`
- `ssh` 缺 `-T` 或不带 `stdin` 转发，远端再嵌套一层时两层都要确认
- `ssh host 'docker exec ... <<PY'` 三层嵌套：本地 bash 消费第一层 here-doc、ssh 传过去、docker 再决定是否读 stdin——**每一跳都要显式声明要 stdin**

**排查捷径**（别去读代码，先验证通路）：

```bash
ssh host "docker exec -i mycontainer cat" <<'PY'
print('stdin 通了')
PY
```

`cat` 能回显就说明 stdin 通，问题在业务代码；`cat` 也空就是管道断了。

**Why:** here-doc 失败的模式是"命令成功执行了但不产生任何输出"，这与"命令根本没跑到"在返回码上无法区分，排查方向完全相反。stdin 未接是这条静默失败里最常见也最容易被忽略的一类。

**How to apply:** 凡是"往容器/远端里塞 here-doc"的复合命令，`docker exec` 一律带 `-i`、`ssh` 一律带 `-T`，写的时候就带上，不要等零输出再回头查。遇到零输出零报错先跑一次 `cat` 探通路。
