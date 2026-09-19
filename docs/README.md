# 文档导航

项目根目录只保留三个日常入口：

- [`README.md`](../README.md)：项目定位、三分钟理解、运行、测试、部署和面试展示。
- [`CONTEXT.md`](../CONTEXT.md)：当前代码状态、架构、技术栈、关键决策和已知限制。
- [`TODO.md`](../TODO.md)：只记录尚未完成的任务，按 P0—P3 排序。

## 正式使用文档

| 主题 | 权威入口 |
|---|---|
| 数据与来源边界 | [`data/README.md`](../data/README.md) |
| API 本地运行 | [`apps/api/README.md`](../apps/api/README.md) |
| 本地交接与排障 | [`operations/local-handover-runbook.md`](operations/local-handover-runbook.md) |
| 备份恢复 | [`operations/backup-restore-runbook.md`](operations/backup-restore-runbook.md) |
| Release smoke 与回滚 | [`operations/release-smoke-rollback-runbook.md`](operations/release-smoke-rollback-runbook.md) |
| 生产就绪边界 | [`operations/production-readiness-matrix.md`](operations/production-readiness-matrix.md) |
| Windows 部署 | [`../deploy/windows/README.md`](../deploy/windows/README.md) |
| Linux 部署 | [`../deploy/linux/README.md`](../deploy/linux/README.md) |
| 面试 Demo | [`interview/three-minute-demo.md`](interview/three-minute-demo.md) |
| 面试问答 | [`interview/interview-qa.md`](interview/interview-qa.md) |

## 当前验证证据

- [`verification/latest.json`](verification/latest.json) 是当前验证日期、commit、测试结果和模型边界的唯一索引。
- [`verification/2026-09-16-t11-request-budget-and-observability.md`](verification/2026-09-16-t11-request-budget-and-observability.md) 记录最新请求预算、重试、trace 和本地回归。
- 其他带日期的 `verification/` 文件是历史证据，数字只对各自日期和基线负责。

## 设计与历史记录

- [`reviews/`](reviews/) 保存审核结论和风险清单。
- [`superpowers/specs/`](superpowers/specs/) 保存仍有参考价值的设计规格。
- [`superpowers/plans/`](superpowers/plans/) 保存历史实施计划和验收过程，不作为当前待办清单。

新增设计或验证文件时，优先使用带日期的明确名称；如果内容是当前状态，必须同步 `CONTEXT.md` 或 `TODO.md`，避免出现第二份“最新状态”。
