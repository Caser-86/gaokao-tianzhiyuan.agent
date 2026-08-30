# 三分钟面试 Demo 脚本

这份脚本面向 AI Agent 工程师或 LLM 应用开发面试。目标不是逐页介绍功能，
而是用三分钟证明：项目有结构化领域数据、有可解释的 Agent 路由、有模型失败
降级、有运营闭环，并且可以被测试和安全边界约束。

## 录制前准备

只使用本地示例数据和合成配置。不要把真实模型 Key、微信凭据、管理员 token、
用户数据或生产地址放入录屏、终端、浏览器历史和截图。

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-local-stack.ps1 `
  -AdminToken '<synthetic-admin-token>' `
  -WechatOfficialAccountToken '<synthetic-wechat-token>' `
  -WechatOfficialAccountAppId '<synthetic-app-id>' `
  -WechatOfficialAccountEncodingAesKey '<43-character-synthetic-aes-key>' `
  -SmartAnalysisMode off `
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
| 0:00—0:20 | 打开首页 | “这是一个高考志愿咨询 Agent。结构化学校、专业和榜单内容先解决确定性查询，LLM 只负责需要增强的开放问题。” | [`data/`](../../data/)、首页截图 |
| 0:20—0:45 | 进入 `/chat`，提交一个学校/专业问题 | “聊天不是把所有文本直接丢给模型；请求进入统一编排服务，输出可以带结构化字段和降级原因。” | [`chat.py`](../../apps/api/app/services/chat.py)、[`skills.py`](../../apps/api/app/services/skills.py) |
| 0:45—1:10 | 说明自动路由和指定 Skill 两条入口 | “`POST /api/chat/messages` 展示自动匹配；Web 当前入口直接调用高考咨询 Skill。两者共享权益、输出和降级边界。” | [`chat.py` 路由](../../apps/api/app/routers/chat.py)、README 三分钟路径 |
| 1:10—1:35 | 展示模型未配置/离线故障场景 | “Provider 不可用时不把 500 直接交给用户；目录查询和规则化回答仍可用，trace 会记录是否调用模型以及 fallback 原因。” | [`tracing.py`](../../apps/api/app/services/tracing.py)、离线评测报告 |
| 1:35—2:00 | 打开 `/admin` | “模型增强有 `off / gated / on` 权限策略；审核、精选、榜单来源和媒体失败都能进入运营后台，失败不会静默消失。” | [`dashboard-shell.tsx`](../../apps/web/components/admin/dashboard-shell.tsx)、后台截图 |
| 2:00—2:25 | 展示公众号 smoke 或测试报告 | “公众号不是简单 webhook：有签名时间窗、body 上限、MsgId/nonce 幂等、明文/AES 和多类型消息适配。” | [`wechat_replay.py`](../../apps/api/app/services/wechat_replay.py)、Phase 5.5—5.6 报告 |
| 2:25—2:45 | 展示 trace/eval 报告 | “我们用 13 个固定离线样本验证路由、结构化输出和 fallback，而不是只展示一次成功对话。” | [`runner.py`](../../apps/api/app/evals/runner.py)、13/13 评测报告 |
| 2:45—3:00 | 回到 README 的验证区 | “当前本地基线是 API 213 个测试通过、Web 129 个用例通过；生产发布和回滚仍明确列为外部待确认项。” | [`README.md`](../../README.md)、[`2026-08-30 验证记录`](../verification/2026-08-30-evaluation-and-data-trust.md)、生产就绪矩阵 |

## 最少展示的三个问题

1. “河南 560 分如何定位专业？”——展示 Skill 选择、结构化回答和数据来源边界。
2. “如果模型挂了怎么办？”——展示规则 fallback、离线评测中的 Provider failure 样本和 trace 字段。
3. “运营如何知道哪里失败？”——展示后台媒体失败记录、结构化 Action 错误和重试入口。

## 录屏验收清单

- [ ] 前 20 秒说清业务问题和 Agent 边界。
- [ ] 至少展示一次路由、一次 fallback、一次后台运营动作。
- [ ] 至少展示一个工程证据：测试、评测报告、trace 或 smoke。
- [ ] 终端和浏览器中没有真实 secret、个人信息、生产域名或完整用户标识。
- [ ] 结尾主动说明生产发布、监控、版本探针和回滚尚未在本地之外验证。

## 当前状态

脚本、截图和本地 smoke 证据已准备完成；已用 Playwright 在本地合成配置下生成一个脱敏交互视频候选：
[`gaokao-agent-demo.webm`](../../docs/assets/gaokao-agent-demo.webm)，并提供旁挂字幕
[`gaokao-agent-demo.vtt`](../../docs/assets/gaokao-agent-demo.vtt)。候选视频包含首页、结构化
fallback 问答、样式化运营后台和 API 版本/Skill 入口四个章节，文件约 2.93 MiB，时长约 134.04 秒，
属于三分钟内 Demo。浏览器播放和关键时间点画面抽查已通过；当前仍为无音轨的静音录屏，旁白可按面试场景
后续补录；这不是生产演示，面试前仍需做最终敏感信息复核。
