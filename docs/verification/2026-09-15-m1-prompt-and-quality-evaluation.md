# M1 Prompt 身份与三层评测验证记录

> 验证日期：2026-09-15
> 验证分支：`codex/interview-ready`
> 验证方式：本地固定数据、fake/offline Provider、项目测试；未调用真实模型，未读取或输出真实密钥。

## 本轮交付

- 运行时和离线 runner 共享不可变 `PromptSnapshot`，同时记录 Prompt asset hash 与实际 system message 的 effective hash。
- `apps/api/app/evals/runner.py` 支持 `--prompt`，缺少显式 Prompt 时非零退出；报告记录 Prompt、数据集、commit、脏工作树和评测模式。
- 工程协议回归扩充为 30 条，覆盖目录路由、缺信息、Provider 异常、权益分支、敏感边界和 fallback。
- 新增独立 `quality_runner.py` 与 40 条合成领域 replay 样本，按信息不足 8、引用问答 8、比较 6、多轮 6、对抗 6、域外 6 分组，并区分 `dev` / `holdout`。
- 领域质量评测检查引用归属、无依据数字、必需追问、类型契约和禁用断言；失败样本包含 case、split、失败检查和回复摘录。

## 三层验证结果

| 层级 | 命令/范围 | 结果 | 结论边界 |
|---|---|---:|---|
| 工程协议回归 | `python -m app.evals.runner --format json` | `30/30`；路由/schema/fallback 均 `100%` | 证明固定输入、路由、契约和降级行为；不是模型质量 |
| Prompt 契约 | `test_chat_services.py`、`test_eval_runner.py` | actual system message、角色顺序、Prompt 快照冻结、自定义/缺失路径均通过 | 证明组装和身份可追溯；不证明回答正确 |
| 领域质量 replay | `python -m app.evals.quality_runner --format markdown` | `40/40`；四项质量指标均 `100%`；分母均 40；禁用断言违规 0 | 证明评分器和固定 replay fixture；不代表线上模型质量 |

领域 replay 数据集 SHA-256：
`c8c3b0008d30df322d93a97d48b8db3de1b3970e2a46a53e69170248ae893fae`

## 可复现命令

```powershell
Set-Location apps/api
python -m ruff check .
python -m ruff format --check .
python -m pytest -q
python -m app.evals.runner --format markdown
python -m app.evals.quality_runner --format markdown
```

本轮实际结果：Ruff lint 通过，Ruff format 检查显示 `77 files already formatted`，API 全量测试 `232 passed`、21 个既有弃用/资源警告。Web 为 `28 files / 130 passed`，typecheck 和生产构建通过；工程评测的一次测量为 P50 `3.91 ms`、P95 `8.99 ms`。延迟只作本机相对基线，不作为生产 SLA。

## 失败路径证据

- 缺少 Prompt 的 runner CLI 实际退出码为 `2`，并输出 `Prompt asset does not exist`。
- `test_quality_runner_exposes_failures_without_hiding_the_denominator` 注入未知 citation 与无依据数字，确认报告保留分母、失败检查和失败样例，不把失败吞掉。
- 真实质量模式目前只提供显式预算门槛，带预算也会明确报告“real quality evaluation is intentionally not wired to a Provider yet”；本轮没有伪造真实模型成绩。

## 未完成门槛

- G0 仍不能封板：本机 Docker Desktop/daemon 在上一轮检查中不可用，尚未完成隔离卷启动、重启保留数据、`/health`、`/version` 和容器内 Provider stub smoke。
- G1 的 replay 部分已具备可复现证据；真实模型小样本、token/成本统计和线上质量基线未完成。进入真实评测前必须配置私有环境变量、限定 case 数、输出 token 和费用预算，密钥不得进入仓库、报告或截图。
