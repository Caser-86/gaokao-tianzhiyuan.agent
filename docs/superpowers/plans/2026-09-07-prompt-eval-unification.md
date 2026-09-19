# Prompt 与离线评测统一实施计划

> **For agentic workers:** Execute this plan task by task, keeping the existing product behavior and preserving unrelated workspace changes.

**目标：** 让运行时 Agent 与离线评测明确使用同一份正式 Prompt、同一套默认路径解析和同一套 SHA-256 身份计算，避免“代码看似使用了 Prompt、评测实际使用另一份 Prompt”的展示风险。

**范围：** 只调整 Prompt 资产归属、评测身份信息、评测报告和相关文档；不改变业务路由、模型调用协议、JSON 契约、数据目录或真实密钥配置。

**技术约束：** 复用现有 Python/FastAPI/pytest 结构，不引入重型依赖；使用项目根目录 `skills/zhangxuefeng/SKILL.md` 作为唯一正式 Prompt；保留 `apps/api/evals/offline-prompt.md` 作为兼容说明文件，不删除现有路径。

## 全局不变量

- `skills/zhangxuefeng/SKILL.md` 是运行时和离线评测共同解析到的默认 Prompt。
- 自定义有效 `ZHANGXUEFENG_SKILL_PATH` 仍优先于默认 Prompt。
- Provider、技能路由、JSON schema、降级和数据查询行为保持不变。
- 报告必须同时展示 Prompt 相对路径和 SHA-256；每个 case 的 hash 与报告级 hash 一致。
- `apps/data/` 不参与修改、暂存或提交。
- 不读取、写入或输出任何真实 API Key。

## Task 1：先建立失败测试与共享身份边界

**涉及文件：**
- 修改 `apps/api/tests/test_eval_runner.py`
- 视需要补充 `apps/api/tests/test_config.py`

**步骤：**

1. 新增测试：评测报告返回 `prompt.path`、64 位十六进制 `prompt.sha256`，且该 hash 等于 case trace 中的 `prompt_hash`。
2. 新增测试：空配置路径经过共享解析后得到项目正式 Prompt，而不是评测文件中的兼容说明。
3. 运行针对性 pytest，确认新断言在当前代码上失败，记录失败原因。

## Task 2：实现运行时与评测的共享 Prompt 解析及身份计算

**涉及文件：**
- 复用 `apps/api/app/config.py` 的现有默认候选解析器
- 修改 `apps/api/app/services/skills.py`
- 修改 `apps/api/app/evals/runner.py`
- 新增 `apps/api/app/services/prompt_assets.py`

**步骤：**

1. 保留现有配置优先级，提供可被运行时和评测共同调用的默认 Prompt 解析入口。
2. 抽取一个公共 Prompt 文件 SHA-256 计算函数；运行时 `describe()` 和评测报告均使用它。
3. 将离线 runner 的硬编码首候选路径改为调用共享解析入口。
4. 在评测结果顶层加入 Prompt 身份信息，并在 Markdown 报告中展示来源与 SHA-256。
5. 重新运行 Task 1 测试，确认测试通过。

## Task 3：消除第二份 Prompt 的歧义并同步文档

**涉及文件：**
- 修改 `apps/api/evals/offline-prompt.md`
- 修改 `README.md`
- 修改 `PROJECT_REVIEW.md`
- 修改 `docs/verification/2026-09-07-prompt-evaluation-unification.md`

**步骤：**

1. 将 `offline-prompt.md` 改为兼容说明，明确它不参与运行时和离线评测，正式 Prompt 位于 `skills/zhangxuefeng/SKILL.md`。
2. 在 README 和项目审查文档中补充统一 Prompt、Prompt hash、离线评测入口和面试展示价值。
3. 保存本轮实际测试、评测、静态检查和提交信息，所有数字以命令输出为准。

## Task 4：完整验证与交付

**验证命令：**

1. `apps/api/.venv/Scripts/python.exe -m pytest -q --cov=app`
2. `apps/api/.venv/Scripts/python.exe -m app.evals.runner --format markdown`
3. 对本轮修改的 Python 文件运行 Ruff；运行 `git diff --check`。
4. 扫描已跟踪差异中是否出现 API Key、Bearer Token、私钥或常见密钥格式；排除现有未跟踪 `apps/data/`。
5. 运行项目既有 `scripts/verify-project.ps1`（若其依赖环境可用）。
6. 只暂存本计划涉及文件，提交 `feat: unify prompt and offline evaluation`，推送到 `origin/codex/interview-ready`。
7. 推送后确认远端分支与本地 HEAD 一致，工作区只剩用户既有的 `apps/data/` 未跟踪目录。
