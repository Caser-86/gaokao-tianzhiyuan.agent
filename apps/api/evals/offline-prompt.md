# 离线评测 Prompt 兼容说明

离线评测和运行时 Agent 统一使用项目正式 Prompt：
[`skills/zhangxuefeng/SKILL.md`](../../../skills/zhangxuefeng/SKILL.md)。

本文件保留用于兼容已有路径和历史文档，不是 Prompt 资产，不会被运行时或
`app.evals.runner` 加载。评测报告会记录正式 Prompt 的相对路径、资产 SHA-256
和 effective system message SHA-256，用于确认评测与运行时使用的是同一份内容。
