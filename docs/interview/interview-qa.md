# 面试问答包

每个回答都应先讲结论，再指向代码、测试或验证报告。不要把本地演示数据、
离线评测结果或模板部署说成真实招生准确率和生产 SLA。

## 1. 这个项目为什么是 Agent，而不是聊天框？

它有可选择的 Skill、匹配置信度、结构化领域工具、OpenAI-compatible Provider、
规则 fallback、多渠道适配和运营反馈闭环。`SkillRegistry` 先产生候选与原因，
`ConversationService` 选择并编排执行；模型只是其中一个可失败的增强组件。
证据：[`skills.py`](../../apps/api/app/services/skills.py)、
[`chat.py`](../../apps/api/app/services/chat.py)。

## 加分题：和直接询问 GPT/豆包相比，这个项目新增了什么价值？

底层模型可以相同，但调用方式和责任边界不同。直接询问通用模型通常得到一次泛化回答，
考生仍要自己提供完整上下文、核对年份和来源、判断建议是否满足约束；本项目把这些工作
放进了业务系统：结构化高考数据负责确定性查询，SkillRegistry 负责路由，服务端负责权益
和身份边界，LLM 负责开放问题的解释增强，模型失败则回到规则化结果。trace、固定离线评测、
会话保留/删除、微信公众号适配和运营后台，则让这条链路可以被验证和运营。

要诚实补充：这不是训练了新的基础模型，也不能承诺招生建议绝对正确；项目的面试价值在于
展示如何把通用模型约束成一个领域 LLM 应用，并对数据、成本、隐私、失败和人工介入负责。
证据：[`README 差异化定位`](../../README.md)、[`skills.py`](../../apps/api/app/services/skills.py)、
[`chat.py`](../../apps/api/app/services/chat.py)、[`access_control.py`](../../apps/api/app/services/access_control.py)、
[`tracing.py`](../../apps/api/app/services/tracing.py) 和 [`离线评测`](../verification/2026-08-25-phase3.3-3.5-evaluation.md)。

## 2. 为什么没有直接引入 LangChain、向量数据库或 Agent 编排框架？

当前核心知识是学校、专业、榜单来源和关联关系，SQL 查询更确定、更容易测量，
也不增加额外服务成本。检索 spike 的 6 个样本标签一致率为 100%，结论是
`keep_sql_first`；这不是“永远不需要向量检索”，而是要求先补充真实非结构化样本，
用证据证明新增复杂度值得承担。
证据：[`SQL Coverage Spike`](../verification/2026-08-25-phase3.7-retrieval-spike.md)。

## 3. 模型调用失败时用户会看到什么？

Provider 未配置、请求失败、余额不足和非法 JSON 会被区分；可用的目录查询和
规则化 Skill 仍能返回解释性结果。trace 会记录 `model_called`、`used_fallback` 和
`fallback_reasons`，便于知道是业务路由还是外部 Provider 出问题。
证据：[`chat.py`](../../apps/api/app/services/chat.py)、
[`llm.py`](../../apps/api/app/services/llm.py)、
[`Agent Offline Evaluation Baseline`](../verification/2026-08-25-phase3.3-3.5-evaluation.md)。

## 4. 如何验证 Agent 没有“只在演示时成功”？

使用 9 个固定离线样本覆盖目录查询、分数策略、歧义、越界问题、Provider 未配置、
请求失败、余额不足、非法 JSON 和有效结构化输出。当前报告为 9/9，通过率、路由
准确率、结构化输出成功率和 fallback 正确率均为 100%；这些指标只代表固定离线基线，
不代表线上模型质量或志愿建议准确率。
证据：[`evaluation report`](../verification/2026-08-25-phase3.3-3.5-evaluation.md)。

## 5. trace 为什么不记录完整 Prompt 和用户原文？

trace 只保留请求 ID、渠道、消息长度、候选 Skill、选择原因、Provider、耗时、
模型调用标记和 fallback 原因；session ID 只保存截断后的 SHA-256 引用，Prompt 只
记录 SHA-256 指纹。这样能解释路由和版本变化，又减少日志中的隐私与敏感内容。
证据：[`tracing.py`](../../apps/api/app/services/tracing.py)、
[`agent-trace-design.md`](../superpowers/specs/2026-08-25-agent-trace-design.md)。

## 6. 为什么需要服务端身份和权益，而不能信前端传来的 metadata？

客户端字段只能表达意图，不能成为授权事实。当前 Web/微信主体由服务端签发或
解析的 guest session 绑定，智能分析模式由服务端的 `off / gated / on` 与数据库
权益共同决定；客户端伪造 `smart_analysis` 不会扩权。
证据：[`auth.py`](../../apps/api/app/services/auth.py)、
[`access_control.py`](../../apps/api/app/services/access_control.py)、
[`trusted-user-context-design.md`](../superpowers/specs/2026-08-25-trusted-user-context-design.md)。

## 7. 公众号接入最容易出什么安全问题？

除了签名算法本身，还要处理时间窗、请求体上限、重复消息、明文/AES 两种协议和
多类型 XML。项目使用 timestamp freshness、MsgId/nonce receipt 幂等和 body limit；
重复请求会被确认但不会再次处理。AES 只在协议适配层完成，核心对话服务不依赖微信 XML。
证据：[`wechat_replay.py`](../../apps/api/app/services/wechat_replay.py)、
[`chat.py`](../../apps/api/app/routers/chat.py)、
[`wechat-replay-idempotency-design.md`](../superpowers/specs/2026-08-25-wechat-replay-idempotency-design.md)。

## 8. 如何防止图片或官网 URL 变成 SSRF？

外部 URL 只接受 HTTP(S)，拒绝凭据、非法端口、本地/内网/保留地址、危险主机名和
控制字符；重定向每一步重新校验，外部文本读取有大小边界。当前仍明确记录 DNS
rebinding、MIME/内容校验和速率限制是后续加固项，不能把现有校验描述成完整 SSRF 防护。
证据：[`url_safety.py`](../../apps/api/app/services/url_safety.py)、
[`phase4.5 verification`](../verification/2026-08-25-phase4.5-verification.md)。

## 9. 数据会保留多久？用户能删除吗？

会话默认滚动保留 30 天，媒体事件和 Agent trace 有独立保留配置；API 启动和请求
路径都能清理过期记录，并提供按服务端身份删除用户会话和媒体事件的接口。当前
删除边界不等于完整账号注销，账号认证、外部日志轮转仍是生产加固项。
证据：[`data_retention.py`](../../apps/api/app/services/data_retention.py)、
[`privacy.py`](../../apps/api/app/routers/privacy.py)、
[`privacy-data-retention-design.md`](../superpowers/specs/2026-08-25-privacy-data-retention-design.md)。

## 10. 后台为什么要做结构化错误和并发加载？

后台写操作以前难以把服务端失败反馈给用户；现在 Server Action 返回结构化成功/失败
结果，表单展示 pending 和错误状态。首页互不依赖的读取使用 `Promise.allSettled`，
一个分区失败不会让整页失效；首批内容质量表单已单独抽出，但没有一次性拆整个页面。
证据：[`actions.ts`](../../apps/web/app/(admin)/admin/actions.ts)、
[`admin-action-form.tsx`](../../apps/web/components/admin/admin-action-form.tsx)、
[`admin-operations-design.md`](../superpowers/specs/2026-08-25-admin-operations-design.md)。

## 11. 测试策略是什么？

后端用 API、服务、迁移和安全回归测试覆盖业务边界；前端用 API client、页面、表单
状态和后台交互测试；另有离线评测、检索 spike、数据资产校验和本地 HTTP smoke。
当前本地验证为 API `213 passed`、Web `129 passed`；本轮新增的离线评测为
13/13 通过。覆盖率和历史阶段结果应以带日期的验证记录为准，不应把固定样本
通过率表述为线上模型质量。
证据：[`README 测试区`](../../README.md)、[`2026-08-30 验证记录`](../verification/2026-08-30-evaluation-and-data-trust.md)。

## 12. 你会如何解释当前生产差距？

仓库已经有环境模板、CI、Docker、systemd/nginx 模板、迁移、备份恢复、发布就绪矩阵
和本地 smoke，但没有接入真实主机、HTTPS、监控告警、外部备份、GitHub Environment、
生产版本探针或自动回滚。因此下一步不是“再加一个 Agent 框架”，而是完成一次受控发布，
记录版本、执行 post-deploy smoke，再演练失败发布后的回滚。
证据：[`production-readiness-matrix.md`](../operations/production-readiness-matrix.md)、
[`backup-restore-runbook.md`](../operations/backup-restore-runbook.md)。

## 13. 高考建议的风险如何处理？

演示数据和权威招生数据严格区分；页面和文档声明示例数据不能用于真实志愿决策，
未来真实数据必须带来源 URL、年份、地区和更新时间。模型输出不能替代政策原文或
人工核验，生产接入前还需要数据来源审核和更新流程。
证据：[`data README`](../../data/README.md)、[`README 安全声明`](../../README.md)。

## 14. 如果流量和成本上升，先优化什么？

先用 trace 的路由命中、模型调用标记、耗时和 fallback 原因定位成本来源；对确定性
目录查询继续走 SQL，不把每次请求都交给模型；再按真实数据和延迟指标决定缓存、限流、
模型分层或检索升级。当前仓库没有声称已经完成线上成本优化或容量基准。

## 15. 你认为下一项最值得做的工作是什么？

完成受控生产发布和回滚演练，然后扩充真实非结构化问题评测集。只有评测显示 SQL
优先边界不足，才引入更复杂的检索组件；同时补齐账号认证、速率限制、DNS rebinding、
媒体 MIME 校验和外部日志轮转。

## 面试回答纪律

- 先区分“已在本地验证”“静态审查发现”和“需要外部确认”。
- 不把 9/9 离线样本说成线上模型准确率。
- 不把 guest session 说成完整账号认证。
- 不把 URL 校验说成已经解决 DNS rebinding。
- 不把部署模板和本地 smoke 说成生产已上线。
