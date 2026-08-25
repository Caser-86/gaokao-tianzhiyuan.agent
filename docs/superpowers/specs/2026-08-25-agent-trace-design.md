# Agent Trace Schema Design

> 日期：2026-08-25
> 范围：Phase 3.1、3.6
> 状态：已实现并通过 API 服务层与离线评测回归测试

## 目标

让一次聊天请求能够解释：候选 Skill 如何被比较、最终选择了什么、是否调用了模型、请求耗时多少，以及为什么发生规则降级。

## 设计

- `ConversationService` 在请求开始生成 `request_id`，通过可注入的 `TraceSink` 发出一次结构化事件。
- 默认 sink 使用 Python logging；测试和后续接入方可以注入 callback，因此不新增数据库、APM 或运行时依赖。
- session 不记录原值，只记录其 SHA-256 前 16 位作为 `session_ref`；用户 ID、完整消息和 Prompt 不进入 trace。
- 候选项只保留 Skill ID、版本、是否匹配、置信度和有界匹配原因。
- Skill 版本来自 `SkillMetadata.version`；如果 Skill 使用本地 Prompt asset，trace 额外记录该文件内容的完整 SHA-256 `prompt_hash`，不记录路径或原文。
- Provider 由 Skill 执行结果声明；`model_called` 单独表示本次是否实际进入模型调用路径。
- trace sink 异常被隔离，不得改变聊天请求的返回结果。

## Schema v1

```json
{
  "schema_version": "agent-trace.v1",
  "request_id": "chat_<opaque-id>",
  "channel": "web",
  "session_ref": "<sha256-prefix>",
  "message_length": 24,
  "candidates": [
    {
      "skill_id": "catalog_lookup",
      "version": "v1",
      "matched": false,
      "confidence": 0.0,
      "reason": "no catalog entity matched"
    }
  ],
  "selected_skill": {
      "skill_id": "fallback",
      "version": "v1",
    "confidence": 0.0,
      "reason": "no enabled skill exceeded routing threshold"
  },
  "provider": "none",
  "model_called": false,
  "duration_ms": 1.23,
  "used_fallback": true,
  "fallback_reasons": ["no_enabled_skill_above_threshold"]
}
```

## 明确不做

- 不把 trace 返回给公开 Web/微信响应，避免把内部观测字段变成客户端契约。
- 不保存完整 Prompt、用户消息、API Key、openid 或模型原始响应。
- 不在本任务中引入 OpenTelemetry、外部 APM、消息队列或会话持久化。
- Prompt hash 只用于版本比较，不被解释为 Prompt 内容、模型质量或招生建议正确率证明。

## 验收证据

- `apps/api/tests/test_chat_services.py` 验证 Provider 成功、Provider 失败、全局 fallback、敏感字段不泄露和 sink 故障隔离。
- 同一测试文件验证 Prompt hash 出现在内部 trace、且不出现在公开 `matched_skill` 响应；`test_eval_runner.py` 验证报告同时记录 Skill version 与 Prompt hash。
- 后续持久化、保留和删除策略属于 Phase 3.2/Phase 4.6，不由本 schema 默认推导。
