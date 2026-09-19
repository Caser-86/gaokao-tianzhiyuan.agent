# T11 请求预算与可观测性验证

> 日期：2026-09-16
> 验证基线：`78071c7`（T10 完成后的基线；本报告记录其后的工作树变更）
> 分支：`codex/interview-ready`

## 结论

T11 的单进程代码边界已完成并通过 API 全量回归。聊天请求现在具备消息长度、
并发、总时限、IP/主体窗口限流和不依赖主体的 UTC 日预算；Provider 对超时、429
和 5xx 最多重试一次。Agent trace 改为会话保存成功或失败后只发一次，并以白名单
保留 token usage；Provider 没有 usage 时写入 `null`。

本次没有连接真实火山引擎、没有读取或写入真实密钥，没有进行多 worker 共享存储、
公网压测、Docker runtime 或生产日志轮转验证。因此本报告不能推出真实 token/cost、
生产 SLA 或跨进程限流结论。

## 实际命令与结果

在 `apps/api` 执行：

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_request_budget.py
# 10 passed

.\.venv\Scripts\python.exe -m pytest -q
# 261 passed, 8 warnings

.\.venv\Scripts\python.exe -m ruff check app
# passed

.\.venv\Scripts\python.exe -m ruff format --check app
# passed
```

新增回归覆盖：

- 4000 字符消息在 Pydantic 层拒绝，服务不会进入 `ConversationService`。
- 同一进程并发槽为 4；槽位满时返回 429，回调不执行。
- IP 与服务端主体组成窗口限流键；拒绝请求不调用会话服务。
- 新建匿名 session 不能通过更换身份绕过全局日预算。
- 单请求超时返回 `RequestTimeoutError`，后台工作结束后释放并发槽。
- Provider 5xx 后仅重试一次；普通 4xx 不重试；成功响应保留 usage。
- 持久化成功后 trace 才发出；持久化失败时 trace 带 `request_error:*`，仍只发一次。
- 应用启动通过 `configure_logging()` 显式开启 `app.agent_trace` 的 INFO 级别。

## 配置边界

默认值已同步到 `apps/api/.env.example`、Docker Compose、Linux/Windows 生产模板：

| 配置 | 默认值 | 说明 |
|---|---:|---|
| `GAOKAO_AGENT_CHAT_MAX_MESSAGE_CHARS` | 4000 | 单条消息字符上限 |
| `GAOKAO_AGENT_MODEL_MAX_CONCURRENCY` | 4 | 单进程并发槽 |
| `GAOKAO_AGENT_CHAT_REQUEST_TIMEOUT_SECONDS` | 30 | 单次请求总时限 |
| `GAOKAO_AGENT_CHAT_RATE_LIMIT_REQUESTS` | 20 | 窗口内 IP/主体请求数 |
| `GAOKAO_AGENT_CHAT_RATE_LIMIT_WINDOW_SECONDS` | 60 | 限流窗口 |
| `GAOKAO_AGENT_CHAT_DAILY_REQUEST_BUDGET` | 1000 | 不依赖主体的 UTC 日预算 |
| `GAOKAO_AGENT_LLM_MAX_OUTPUT_TOKENS` | 800 | 通过 OpenAI-compatible `max_tokens` 发送；Provider 兼容性仍需真实环境确认 |
| `GAOKAO_AGENT_LLM_MAX_RETRIES` | 1 | 当前配置限制为 0 或 1 |

实现是进程内标准库 guard，适合单进程本地或单 worker 验证。多 worker 部署前，
应替换为共享限流/预算存储，并额外验证代理 IP 获取、账单 token 口径和日志轮转。
