# Chat Session Persistence Design

> 日期：2026-08-25
> 范围：Phase 3.2
> 状态：已实现并通过 API/Web 回归测试

## 目标

让 Web 聊天能够在同一个 `session_id` 下继续多轮对话，并提供按用户读取和删除历史消息的最小接口。当前身份仍来自请求参数，可信身份迁移属于 Phase 4，不在本任务中假装解决。

## 最小数据模型

- `ChatSession`：保存随机/客户端传入的 session ID、当前用户标识、渠道、创建/更新时间和过期时间。
- `ChatMessage`：保存 `user` / `assistant` 角色、请求 ID、内容类型和内容；结构化 assistant 内容以 JSON 文本存储，便于恢复原始输出。
- trace 不写入会话表，避免把调用观测与用户消息生命周期耦合。

## 生命周期与隐私边界

- 默认保留期为 30 天；每次写入刷新 `expires_at`，写路径清理已过期会话。
- 用户可以按自己的 `user_id + session_id` 删除会话及其消息。
- 查询、续写和删除均同时匹配 `session_id` 与 `user_id`；不向错误用户区分“会话不存在”和“无权访问”，统一返回 404。
- 当前阶段必须存储用户消息才能恢复上下文，因此该数据属于敏感业务数据；生产部署前仍需替换客户端 user ID 为可信认证上下文，并补充后台/定时清理策略。
- 不保存请求 metadata、完整 Prompt、API Key 或 trace 原文。

## API 形态

- 聊天响应新增 `session_id`，客户端后续请求原样带回。
- `GET /api/chat/sessions/{session_id}/messages?user_id=...` 返回脱敏后的会话消息列表。
- `DELETE /api/chat/sessions/{session_id}?user_id=...` 删除该用户拥有的会话。

## 明确不做

- 不实现长期记忆、语义摘要、向量检索或跨用户画像。
- 不把历史消息自动拼入模型 Prompt；本阶段先保证可持久化和可恢复，Prompt 上下文策略另立评测任务。
- 不把当前客户端提交的 `user_id` 描述为可信身份。
