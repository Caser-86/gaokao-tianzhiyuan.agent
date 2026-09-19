# Prompt 与离线评测统一验证记录

> 验证日期：2026-09-07
> 验证基线：`02f4fd3` + 当前工作树中的本轮改动
> 验证方式：本地命令、固定离线样本、项目既有验证脚本；未调用真实模型，未读取或输出真实密钥。

## 本轮目标

确认运行时 Agent 和离线评测使用同一份正式 Prompt，并让评测报告公开声明 Prompt 来源与 SHA-256 身份，避免维护两份容易漂移的 Prompt。

## 实现结果

- 正式 Prompt：[`skills/zhangxuefeng/SKILL.md`](../../skills/zhangxuefeng/SKILL.md)。
- 运行时默认路径：复用 `app.config.resolve_zhangxuefeng_skill_path` 的默认候选解析；有效的自定义配置路径仍优先。
- 离线 runner：通过同一解析入口选择默认 Prompt，不再硬编码候选列表首项。
- Prompt hash：运行时 `SkillMetadata.prompt_hash` 与评测报告共用 `app.services.prompt_assets.hash_prompt_file`。
- 兼容文件：[`apps/api/evals/offline-prompt.md`](../../apps/api/evals/offline-prompt.md) 仅说明历史路径兼容，不会被运行时或评测加载。
- 评测报告：新增 `prompt.path` 和 `prompt.sha256`，Markdown 报告增加 Prompt Identity 表格。

## 验证命令与结果

### 针对性测试

```powershell
Set-Location apps/api
.\.venv\Scripts\python.exe -m pytest -q tests/test_eval_runner.py tests/test_config.py
```

结果：`19 passed`。

### API 全量测试与覆盖率

```powershell
.\.venv\Scripts\python.exe -m pytest -q --cov=app
```

结果：`216 passed`，总覆盖率 `85%`。输出中有既有的 SQLite `ResourceWarning`、Starlette/httpx 弃用提示和 FastAPI 422 弃用提示，但没有测试失败。

### 离线评测

```powershell
.\.venv\Scripts\python.exe -m app.evals.runner --format markdown
```

结果：`13/13` 通过；路由、schema、fallback 均为 `100%`。本次报告声明：

```text
Prompt source: skills/zhangxuefeng/SKILL.md
Prompt SHA-256: 51ead705957105c3e09ea3fdc98cca8bace6d58b99be2202a73fac05929d0178
```

该结果来自固定 case 和本地 Provider stub，不代表线上模型质量、招生建议准确率或生产延迟。

### 项目级验证

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify-project.ps1
```

结果：脚本成功结束，包含以下通过项：

- JSON 数据资产校验：`2 schools, 4 majors`；
- API：`216 passed`；
- Web：`28` 个测试文件、`130 passed`；
- Web 覆盖率：语句/分支/函数/行分别为 `87.03% / 84.17% / 73.15% / 87.03%`；
- Web typecheck 和 Next.js 生产构建通过。

构建输出包含既有的 `<img>` 性能提示和 Next.js ESLint 配置提示；它们未阻断构建，也不是本轮 Prompt 改动引入的失败。

### 静态与差异检查

```powershell
.\.venv\Scripts\python.exe -m ruff check app/config.py app/evals/runner.py app/services/skills.py app/services/prompt_assets.py tests/test_eval_runner.py tests/test_config.py
git diff --check
```

结果：Ruff `All checks passed!`，`git diff --check` 通过。提交前还会再次确认只暂存本轮文件，排除既有未跟踪的 `apps/data/`。

## 边界与安全说明

- 离线评测不会访问火山引擎、OpenAI 或其他真实模型服务。
- 本轮没有修改 `.env`、API Key、模型配置或真实数据；未提交任何密钥。
- 评测 hash 证明的是 Prompt 资产身份一致，不等于模型输出质量证明。
- 根目录 `data/` 仍是演示数据，不是官方招生数据库；真实志愿决策仍需复核权威来源。

