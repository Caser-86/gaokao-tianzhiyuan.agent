# T08 受控多轮上下文验证记录

> 日期：2026-09-15（Asia/Shanghai）
>
> 范围：验证服务端会话上下文、用户隔离、上下文预算、改口规则和 Web 当前轮展示；不代表真实模型质量、浏览器 E2E 或生产 SLA。

## 本次交付

- `ChatSessionStore` 从服务端已授权 session 读取完整的 user/assistant turn，默认最多最近 6 轮、总计 12000 字符，两个上限可由配置覆盖且必须为正数。
- 首次使用尚未落库的 session 返回空上下文；已存在 session 仍按用户归属校验，过期会话清理后不会继续注入历史。
- 结构化 assistant 消息只提取 `rendered_reply`，再回退到 `summary`/`analysis`，不把数据库 JSON envelope 直接传给 Provider。
- 请求中的客户端 `conversation_history` 不覆盖服务端读取结果；Skill 只接受 `user`/`assistant` 角色，历史助手消息不会升级为 system message。
- 正式 Prompt 增加多轮改口规则：用户后续对省份、年份、分数、位次、选科或目标的明确更正优先。
- Web 请求成功后把当前 user/assistant exchange 追加到可见历史，并继续复用返回的 `session_id`。

## TDD 与回归结果

实现前先运行新增测试，观察到 API 定向测试 `50 passed, 4 failed`、Web 聊天工作区 `8 passed, 1 failed`；失败分别对应缺少上下文配置/读取/Provider 注入和前端历史追加。

实现后执行：

```powershell
Set-Location apps/api
.\.venv\Scripts\python.exe -m pytest -q tests/test_config.py tests/test_chat_sessions.py tests/test_chat_services.py
# 55 passed, 1 warning

.\.venv\Scripts\ruff.exe check app\config.py app\services\chat.py app\services\chat_sessions.py app\services\skills.py tests\test_config.py tests\test_chat_sessions.py tests\test_chat_services.py
# All checks passed!

.\.venv\Scripts\ruff.exe format --check app\config.py app\services\chat.py app\services\chat_sessions.py app\services\skills.py tests\test_config.py tests\test_chat_sessions.py tests\test_chat_services.py
# 7 files already formatted

Set-Location ..\web
node ./node_modules/vitest/vitest.mjs run tests/chat-workspace.test.tsx
# 1 file, 9 passed
```

随后执行完整本地门禁，当前基线记录为 API `241 passed`、Web `28 files / 131 passed`；数据资产、typecheck、Next.js 生产构建和 Docker build 的结果以本次门禁终端输出为准。既有 Starlette/AnyIO 弃用提示、Next `<img>` 提示和 GitHub Actions Node deprecation 不作为本次功能失败。

## 可复现验收映射

| 验收点 | 证据 |
|---|---|
| 最近 6 轮 | `test_chat_session_store_builds_recent_model_context_with_turn_and_char_limits` |
| 12000 字符可配置与超长裁剪 | `test_chat_context_limits_are_configurable_and_must_be_positive`、`test_chat_session_store_trims_old_turns_when_character_budget_is_reached` |
| 不同用户不能读取上下文 | `test_chat_session_store_does_not_leak_context_across_users`、既有会话 HTTP 隔离测试 |
| 服务端历史覆盖客户端伪造 | `test_conversation_service_passes_saved_history_as_non_system_messages` |
| 改口优先的 Prompt 约束 | 正式 `skills/zhangxuefeng/SKILL.md` 信息规则第 6 条；服务测试使用“更正：河南580分”作为第二轮输入 |
| Web 当前 exchange 可见且 session 可续写 | `apps/web/tests/chat-workspace.test.tsx` 的 `appends the submitted exchange...` 与既有 session 复用测试 |

## 明确未完成项

- 当前 Provider 测试使用 fake/spy，不证明 `ark-code-latest` 或其他真实模型对改口、多轮信息召回的质量；真实调用必须在私有环境变量、限定 case/token/费用预算下单独记录。
- 当前 Web 证据是 Vitest 组件测试，不等于真实浏览器跨页面恢复、刷新、重复提交和移动端体验；这些留给 T10 浏览器 E2E。
- 证据注入、citation 校验和“上下文 + 证据”对照评测仍属于 T09。
