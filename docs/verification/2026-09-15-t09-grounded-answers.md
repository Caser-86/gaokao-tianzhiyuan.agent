# T09 证据驱动回答与成对评测验证记录

> 日期：2026-09-15（Asia/Shanghai）
>
> 范围：验证有限 SQL 证据注入、嵌套 citation 白名单、无证据数字声明降级，以及直接调用 vs 上下文+证据+校验的成对 replay。另执行一次最小真实 Provider smoke 验证适配器和安全降级；未记录或输出真实密钥，当前目录数据仍是 `demo` 资产。

## 本次交付

- `ConversationService` 只为消息中明确出现的学校/专业名称生成证据包，默认最多 20 条、12000 字符；客户端提交的 `evidence_items` 会被服务端生成的上下文覆盖。
- `ZhangXueFengSkill` 将受限证据包作为单独的 system context 传给 Provider，模型只能在现有嵌套结果的 `entities.evidence_refs` 中引用包内 `citation_id`。
- 服务端把受信的 `entities.evidence` 来源元数据附回结构化结果，避免接受模型自行生成的来源 URL；来源 URL 为空的 demo 内容仍不能被包装成官方依据。
- 未知 citation、非法引用数组以及没有证据却输出录取概率/分数线/位次等可见数字声明时，Provider 结果进入规则降级，并留下可观测的 debug reason。
- `quality_runner` 同时支持历史 replay fixture 的顶层 `evidence_refs` 和运行时嵌套 `entities.evidence_refs`；新增 `--mode pairwise`，以同一问题、共享预算、统一评分和 Provider 实际返回模型一致性生成逐样本对照报告。

## 真实 Provider smoke

私有环境配置检查只输出布尔状态，确认 Provider、Base URL、Key 和模型配置均存在；未读取或打印 Key。随后使用 Base URL `https://ark.cn-beijing.volces.com/api/plan/v3` 和请求模型 `ark-code-latest` 执行了两次受控调用：一次适配器连通性测试返回 18 字符且可解析为 JSON；一次完整 `ConversationService → SkillRegistry → ZhangXueFengSkill → Provider → 结构化校验/降级 → session` 链路收到模型内容，但因无证据数字声明触发 `provider_unsupported_numeric_claim`，最终安全降级为规则结果。

这次 smoke 证明了真实请求可到达 Provider，并验证了 fail-closed 保护；没有把单次调用表述成模型质量通过。当前 `OpenAICompatibleProvider` 会在内存中保留响应 envelope 的 `returned_model` 和 usage，trace 在字段存在时记录请求/返回模型；token 计费换算和真实成对评测仍未完成，且本次脱敏 smoke 摘要没有输出上游实际 returned model，因此不能把它写成真实成对评测证据。

## TDD 与回归结果

实现前先运行新增的 `test_grounded_answers.py`，结果为 `5 failed, 1 passed`；失败均对应尚未实现的证据消息、服务端证据构造、citation/数字声明校验和嵌套评测读取。实现后该文件为 `8 passed`。

API 定向与全量验证：

```powershell
Set-Location apps/api
python -m pytest tests/test_grounded_answers.py tests/test_quality_runner.py -q
# 12 passed

python -m pytest -q
# 250 passed, 7 warnings

ruff check app tests
# All checks passed!
ruff format --check app tests
# 80 files already formatted

python -m app.evals.quality_runner --format markdown
# 40/40 replay cases; four quality metrics 100%; denominator 40

python -m app.evals.quality_runner --mode pairwise --format markdown
# 1 total pair; 1 comparable; direct pass rate 0%; grounded pass rate 100%

Set-Location ../..
powershell -ExecutionPolicy Bypass -File scripts/verify-project.ps1
# Project verification finished successfully
# Web: 28 files / 131 passed; coverage 87.09% statements, 84.19% branches, 73.15% funcs
# Web typecheck and production build passed; Docker build/runtime was not part of this local run
```

仓库门禁还保留一个既有提示：当前工作区存在未跟踪的 `apps/data/`，校验器明确以根目录 `data/` 为权威源且不验证重复目录；该目录没有被本轮提交。API 运行期间的 Starlette/AnyIO、SQLite ResourceWarning 和 Web 的 Next `<img>`/ESLint plugin warning 也没有导致门禁失败。

成对 fixture 使用同一个请求别名 `ark-code-latest`，并要求两侧 Provider 实际返回同一个 `deepseek-v4-flash`；报告仍分别保存 requested alias 与 returned model，未把 alias 当成固定模型版本。该结果来自合成 recorded outputs，只验证评分器和对照报告格式，不证明 grounded 方案在线上一定更好。

## 可复现验收映射

| 验收点 | 证据 |
|---|---|
| 有界证据注入 | `test_skill_injects_bounded_evidence_and_keeps_only_known_citations`；默认配置 `GAOKAO_AGENT_EVIDENCE_MAX_ITEMS=20`、`GAOKAO_AGENT_EVIDENCE_MAX_CHARS=12000` |
| 服务端证据优先 | `test_conversation_service_builds_server_owned_evidence_context`；客户端伪造 evidence 不进入 Provider context |
| 未知 citation | `test_skill_falls_back_for_unknown_citation`；debug reason 为 `provider_invalid_citation` |
| 无证据数字声明 | `test_skill_falls_back_for_numeric_claim_without_evidence`；debug reason 为 `provider_unsupported_numeric_claim` |
| 嵌套运行时契约 | `test_quality_runner_accepts_runtime_nested_evidence_refs` 与 `test_quality_runner_rejects_unknown_nested_evidence_ref` |
| 成对评测可比性 | `test_quality_runner_compares_direct_and_grounded_outputs_with_returned_model` 与 `test_quality_runner_marks_pair_non_comparable_when_provider_models_differ` |

## 明确未完成项

- 本轮已做最小火山方舟真实 Provider smoke，但没有进行真实成对质量评测，因此没有真实返回模型、token、费用或质量结论；真实成对调用必须在私有环境变量、限定 case/token/费用预算下单独执行，密钥不得进入仓库、报告或截图。
- `comparison-cases.json` 目前是最小合成 fixture，不足以证明领域质量提升；下一步应扩充真实标注的多轮、无证据和冲突事实样本，并保留 direct/grounded 两侧原始失败原因。
- 当前 Web 仍未完成引用卡片的浏览器展示、来源 URL 点击与跨页面恢复 E2E；只有服务端结构化结果在来源 URL 存在时提供可打开元数据。
- 根目录 `data/` 仍是演示数据，不是实时招生数据库；没有来源 URL 的本地摘要不应被 UI 当作可点击官方引用。
