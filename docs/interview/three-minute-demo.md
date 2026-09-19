# 三分钟面试 Demo 脚本

这份脚本面向 AI Agent 工程师或 LLM 应用开发面试。目标不是逐页介绍功能，
而是用三分钟证明：项目有结构化领域数据、有可解释的 Agent 路由、有模型失败
降级、有运营闭环，并且可以被测试和安全边界约束。

## 录制前准备

只使用本地示例数据和合成配置。T10 的引用展示使用本地合成 OpenAI-compatible Provider，
请求中的模型标签可以写成 `ark-code-latest`，但不能把它说成真实火山模型质量结论。
不要把真实模型 Key、微信凭据、管理员 token、用户数据或生产地址放入录屏、终端、
浏览器历史和截图。

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local-stack.ps1 `
  -AdminToken '<synthetic-admin-token>' `
  -WechatOfficialAccountToken '<synthetic-wechat-token>' `
  -WechatOfficialAccountAppId '<synthetic-app-id>' `
  -WechatOfficialAccountEncodingAesKey '<43-character-synthetic-aes-key>' `
  -SmartAnalysisMode on `
  -DatabasePath '.tmp/interview-demo.db' `
  -StateFilePath '.tmp/interview-demo.state.json'
```

打开 `http://127.0.0.1:3000`、`/chat` 和 `/admin`。录制完成后运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop-local-stack.ps1 `
  -StateFilePath '.tmp/interview-demo.state.json'
```

如需一次性验证公众号明文/AES、多类型消息和本地健康链路，可使用现有的
`start-local-stack.ps1 -RunSmoke`；它不会连接真实模型或生产接口。

## 时间线与台词

| 时间 | 操作 | 建议台词 | 证据落点 |
|---|---|---|---|
| 0:00—0:20 | 打开首页并进入一条详情 | “这是一个高考志愿咨询 Agent。结构化学校、专业和榜单内容先解决确定性查询，详情页明确标注当前是演示数据，LLM 只负责需要增强的开放问题。” | [`data/`](../../data/)、[`data-provenance-notice.tsx`](../../apps/web/components/public/data-provenance-notice.tsx) |
| 0:20—0:45 | 进入 `/chat`，提交“东南大学怎么样” | “聊天不是把所有文本直接丢给模型；请求进入统一编排服务，输出可以带结构化字段、证据 ID 和降级原因。” | [`chat.py`](../../apps/api/app/services/chat.py)、[`skills.py`](../../apps/api/app/services/skills.py) |
| 0:45—1:05 | 展开“证据与引用” | “目录证据由服务端筛选，来源元数据由服务端回填；有 HTTP(S) 来源才能打开链接，没有 URL 的演示资料会显示边界提示。” | [`evidence.py`](../../apps/api/app/services/evidence.py)、[`evidence-list.tsx`](../../apps/web/components/public/evidence-list.tsx) |
| 1:05—1:25 | 同一 session 追问并重新打开 `session_id` | “服务端只把当前主体最近最多 6 轮、12000 字符的完整 turn 交给 Skill；客户端不能伪造历史，刷新后仍能恢复四条会话消息。” | [`chat_sessions.py`](../../apps/api/app/services/chat_sessions.py)、[`chat-workspace.tsx`](../../apps/web/components/public/chat-workspace.tsx) |
| 1:25—1:45 | 停止合成 Provider，再提问 | “Provider 不可用时不把 500 直接交给用户；页面仍显示规则降级结果，响应 debug 和 trace 会记录 `provider_request_failed`。” | [`tracing.py`](../../apps/api/app/services/tracing.py)、[`T10 验证记录`](../verification/2026-09-15-t10-browser-demo.md) |
| 1:45—2:05 | 打开 `/admin` 并保存一次学校摘要 | “模型增强有 `off / gated / on` 权限策略；内容摘要、精选、榜单来源和媒体失败都能进入运营后台，保存结果可见。” | [`dashboard-shell.tsx`](../../apps/web/components/admin/dashboard-shell.tsx)、后台截图 |
| 2:05—2:30 | 展示 trace/eval 报告 | “我们用 30 个固定工程样本验证路由、结构化输出和 fallback，再用 40 条独立 replay 检查引用、无依据数字和追问覆盖；另有 1 条同问题同预算的 direct vs grounded 成对样本，逐项展示失败原因，而不是只展示一次成功对话。” | [`runner.py`](../../apps/api/app/evals/runner.py)、[`quality_runner.py`](../../apps/api/app/evals/quality_runner.py)、T09 评测报告 |
| 2:30—3:00 | 回到 README 的验证区 | “当前本地基线是 API 261 个测试通过、Web 132 个用例通过；T10 浏览器验收和 T11 请求预算回归已通过，但真实模型成对质量、多 worker 预算、Docker runtime 和生产发布仍明确列为待确认项。” | [`latest.json`](../verification/latest.json)、[`T10 验证记录`](../verification/2026-09-15-t10-browser-demo.md)、[`T11 验证记录`](../verification/2026-09-16-t11-request-budget-and-observability.md)、生产就绪矩阵 |

## 最少展示的三个问题

1. “河南 560 分如何定位专业？”——展示 Skill 选择、结构化回答和数据来源边界。
2. “如果模型挂了怎么办？”——展示规则 fallback、离线评测中的 Provider failure 样本和 trace 字段。
3. “运营如何知道哪里失败？”——展示后台媒体失败记录、结构化 Action 错误和重试入口。

## 本轮已实际验收

- [x] 前 20 秒说清业务问题和 Agent 边界。
- [x] 展示一次目录证据、一次两轮会话、一次 fallback 和一次后台运营动作。
- [x] 展示测试、评测报告、trace 字段和唯一验证索引。
- [x] 终端和浏览器中没有真实 secret、个人信息、生产域名或完整用户标识。
- [x] 结尾主动说明真实模型、生产发布、监控、版本探针和回滚尚未在本地之外验证。

## 当前状态

脚本、截图和本地 smoke 证据已准备完成；已用 Playwright 在本地合成配置下生成一个脱敏交互视频候选：
[`t10-demo.webm`](../../docs/assets/t10-demo.webm)，并保留此前的通用候选
[`gaokao-agent-demo.webm`](../../docs/assets/gaokao-agent-demo.webm)及旁挂字幕
[`gaokao-agent-demo.vtt`](../../docs/assets/gaokao-agent-demo.vtt)。候选视频包含首页、目录详情、证据引用卡、两轮问答和运营后台保存动作；当前仍为无音轨的静音录屏，旁白可按面试场景
后续补录；这不是生产演示，面试前仍需做最终敏感信息复核。
最新事实以 [`latest.json`](../verification/latest.json) 为准；浏览器场景见 [`2026-09-15 T10 验证记录`](../verification/2026-09-15-t10-browser-demo.md)，请求预算与最终 trace 见 [`2026-09-16 T11 验证记录`](../verification/2026-09-16-t11-request-budget-and-observability.md)，T09 的证据注入、citation 校验和成对评测记录见 [`2026-09-15 T09 验证记录`](../verification/2026-09-15-t09-grounded-answers.md)。
