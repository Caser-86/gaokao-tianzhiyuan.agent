# 隐私与数据保留设计

**状态：** Implemented and verified

## 目标

把当前已经存在的会话、公众号媒体事件、重放 receipt 和 Agent trace 数据分成明确的收集、脱敏、保留、清理与用户删除规则。保持 SQLite、FastAPI、SQLModel 边界，不引入队列、外部审计平台或新的运行时依赖。

## 数据盘点与策略

| 数据 | 当前用途 | 收集内容 | 默认保留 | 删除/清理 |
|---|---|---|---:|---|
| `ChatSession` / `ChatMessage` | 会话恢复与按用户删除 | 用户消息、结构化 assistant 输出、channel、request/session 引用 | 30 天滚动 | 写路径、API 启动时清理过期记录；用户可删除全部个人数据 |
| `MediaAnalysisEvent` | 媒体分析审计、失败重试和后台排障 | Provider 状态、摘要、提取字段、微信回调上下文；不保存二进制图片 | 30 天滚动 | 创建/查询路径和 API 启动时清理；用户删除接口一并删除 |
| `WeChatMessageReceipt` | 防止短时间重复回调 | `MsgId`/nonce 去重键与接收时间 | 公众号 timestamp 窗口（默认 300 秒） | claim 前与 API 启动时清理；不作为长期用户档案 |
| Agent trace | 解释 Skill、Provider、fallback 和耗时 | 脱敏后的 schema、长度、哈希/指纹和错误类别；不记录消息原文、Prompt 原文、密钥或 openid | 外部日志系统建议 7 天 | 应用只写结构化 logger；生产由 journald/容器日志轮转策略删除 |

## 身份与脱敏边界

- 会话和媒体事件按服务端解析的主体删除；客户端提交的 `user_id`/`openid` 不作为生产授权边界。
- trace 继续只允许 `AgentTraceRecorder` 产生的白名单字段；session 只保留短哈希，消息只保留长度，不把原文送入默认 trace logger。
- 微信媒体只记录用于当前审计/重试的 URL 和回调元数据，不下载或保存图片二进制；媒体事件受 30 天上限约束。
- 数据删除返回删除计数，不返回已删除的消息、URL、媒体上下文或 trace 内容。

## API

新增 `DELETE /api/privacy/me`：要求已有 HTTP-only guest session cookie 或 Bearer session token，删除当前主体的全部会话/消息和媒体事件。接口不撤销 HMAC token；账号注册、撤销和多设备管理留给后续阶段。

## 启动清理与可配置项

- `GAOKAO_AGENT_CHAT_SESSION_RETENTION_DAYS`：默认 `30`。
- `GAOKAO_AGENT_MEDIA_ANALYSIS_RETENTION_DAYS`：默认 `30`。
- `GAOKAO_AGENT_AGENT_TRACE_RETENTION_DAYS`：默认 `7`，用于运维日志轮转约定；应用不把 trace 写入数据库。
- 启动时对三类 SQLite 持久化数据执行一次清理；写/查询路径继续执行局部清理，避免无定时任务部署长期堆积。

## 非目标

- 不实现账号级 token 撤销、数据导出、跨库擦除、备份介质擦除或完整日志平台管理。
- 不把媒体 URL 改造成不可重试的摘要，避免删除现有后台重试功能；通过保留期和用户删除接口控制生命周期。
