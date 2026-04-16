# Media Analysis Failure Reason Design

## Goal

让运营在 `/admin` 的媒体分析记录卡片里直接看到“为什么这次媒体分析失败了”，尤其是手动重试失败时，不必再展开 JSON 或查日志。

## Scope

本次只做“失败原因落库并在管理端展示”的最小闭环，不改公众号用户侧回复文案，不新增独立详情页，不做数据库字段迁移。

## Current State

- 媒体分析结果目前只有 `pending / success` 两种状态。
- OpenAI 兼容适配器遇到网络异常、HTTP 错误、空响应或结构异常时，会统一退回 `pending`。
- 管理端虽然能看到媒体分析记录和重试关系，但无法直接区分“暂未接入”与“真的失败”，也看不到失败原因。
- `MediaAnalysisEvent.status` 本身是字符串，`context` 也是 JSON，可承载额外失败信息。

## Options

### Option 1: 只在前端根据现有字段猜测失败原因

- 优点：不改后端结构，改动最小。
- 缺点：无法区分真实失败与待接入，信息不可靠，运营看到的仍然是猜测。

### Option 2: 新增数据库专用失败字段

- 优点：结构最清晰，后续统计最方便。
- 缺点：需要模型变更和迁移，当前这一步会明显变大，不符合快速闭环目标。

### Option 3: 后端引入 `failed + failure_reason`，先落到 `context`

- 优点：不需要迁移；失败原因来自真实 provider 路径；管理端可立即展示。
- 缺点：失败原因暂时存放在 `context`，后续如果要做报表再抽字段。

## Recommendation

选择 Option 3。

这是最适合当前阶段的做法：保留现有表结构和运营页面，只补足“真实失败原因”的采集与展示链路，低风险、收益直接。

## Design

### Backend result model

- 扩展 `MediaAnalysisResult`：
  - `status` 支持 `failed`
  - 新增 `failure_reason: str | None`

### Failure classification

- 保持 `pending` 的场景：
  - 当前媒体类型不支持
  - 缺少 `PicUrl`
  - provider 未配置或仍走 reserved pending provider
- 归类为 `failed` 的场景：
  - 上游 HTTP 失败
  - 网络请求异常
  - 上游返回为空
  - 上游返回结构无法产出 `summary` 或 `rendered_reply`

### Persistence

- 不新增数据库列。
- 在写入 `MediaAnalysisEvent` 时，如果 `result.failure_reason` 存在，则追加到事件 `context.failure_reason`。
- 这条规则同时适用于：
  - 公众号媒体分析事件落库
  - 管理端手动重试事件落库

### Admin UI

- 在现有媒体分析卡片中，如果 `context.failure_reason` 存在，则显示：
  - `失败原因：<reason>`
- 保留上一轮已完成的“原始记录 / 手动重试记录 / 最新重试状态”文案。
- 不新增筛选项，不改单卡布局层级。

### User-facing behavior

- 公众号用户侧回复逻辑保持不变：
  - 只有 `success` 才使用 provider 的 `rendered_reply` 或 `summary`
  - `failed` 仍然走现有 `WECHAT_OFFICIAL_ACCOUNT_MEDIA_ANALYSIS_PENDING_REPLY`

## Testing

- API service test:
  - OpenAI 兼容适配器在上游 HTTP 失败时返回 `status="failed"` 与可读 `failure_reason`
- Chat router test:
  - 失败事件会落库为 `failed`
  - `context.failure_reason` 被持久化
  - 用户回复仍然走原有 pending reply
- Admin retry test:
  - 管理端重试失败时会生成新的 `failed` 事件，并写入失败原因
- Admin dashboard test:
  - 卡片显示 `失败原因：...`

## Out of Scope

- 失败原因国际化
- 独立失败日志页面
- 数据库层 `failure_reason` 专用列
- 自动重试策略
