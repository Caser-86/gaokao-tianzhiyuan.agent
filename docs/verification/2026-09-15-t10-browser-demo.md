# T10 三分钟 Demo 与浏览器验收记录

> 验证日期：2026-09-15<br>
> 验证分支：`codex/interview-ready`<br>
> 验证模式：本地合成配置 + 本地合成 OpenAI-compatible Provider<br>
> 唯一索引：[`latest.json`](latest.json)

## 结论

T10 的面试展示链路已在本机真实浏览器中跑通：主页目录 → 学校详情 → 第一轮带目录证据的回答 → 第二轮追问 → 用 `session_id` 恢复历史 → Provider 断开后的规则降级 → 后台保存摘要。引用卡片只渲染服务端返回的 `entities.evidence`，有 HTTP(S) 来源才显示“打开来源”，演示资料没有 URL 时明确显示边界提示。

本轮 Provider 是本地合成服务，返回模型标签为 `ark-code-latest`，用于验证 OpenAI-compatible 协议和前端展示；没有调用火山引擎、没有使用真实 API Key，也不能据此宣称真实模型质量或招生准确率。

## 自动化回归

| 检查 | 结果 | 说明 |
|---|---:|---|
| API pytest | `250 passed` | 8 个依赖库/框架弃用警告，无失败 |
| Web Vitest | `28 files / 132 passed` | 包含证据引用卡片测试 |
| Web typecheck | 通过 | `tsc --noEmit -p tsconfig.typecheck.json` |
| Web lint | 通过 | 0 errors，3 个既有 `<img>` 性能 warning |
| Web production build | 通过 | 保留既有图片和 Next ESLint 插件 warning |

## 浏览器路径

使用 Playwright CLI 在 `127.0.0.1` 回环地址上验证，数据库从项目 `data/` 演示资产播种，端口和凭据均为临时合成值。

1. 主页成功加载学校/专业目录卡片，并进入 `/schools/southeast-university`。
2. 详情页显示学校模块、榜单链接以及 `演示数据` 来源声明。
3. 第一轮提问“东南大学怎么样”返回 HTTP 200，页面显示 `证据与引用`，服务端证据包展示 11 条证据，其中有来源 URL 的榜单记录显示“打开来源”，无 URL 的演示记录显示“暂无可打开来源”。
4. 第二轮提问“它适合什么专业？”复用同一会话；页面可见两轮 user/assistant 共 4 条历史消息。
5. 重新打开带 `session_id` 的 `/chat` 地址后，页面恢复上述 4 条历史消息。报告和截图不记录完整 session ID。
6. 停止本地合成 Provider 后再次提问，API 仍返回 HTTP 200，响应 debug 显示 `used_fallback=true`、`provider_request_failed`，页面显示“当前使用规则降级结果”。
7. 后台学校摘要保存按钮完成一次真实提交，页面显示“学校摘要已保存”。写入的是本地临时 SQLite，不影响仓库跟踪数据。

## 证据资产

- 证据卡片截图：[`t10-chat-evidence-card.png`](../assets/t10-chat-evidence-card.png)
- 脱敏视频候选：[`t10-demo.webm`](../assets/t10-demo.webm)
- 本次完整 Playwright 输出：`output/playwright/`（本地忽略目录，不作为 GitHub 运行时资产）

## 边界与后续

- 当前浏览器验收证明的是本地 API/Web 连接、会话持久化、服务端证据元数据和降级 UI；不证明线上网络、真实 Provider 质量、真实 token/cost、生产 SLA 或权威招生数据准确率。
- `npm run build` 与 Next 开发服务器不能同时复用正在运行的 `.next` 目录；本轮发现该环境耦合后停止并重启开发服务器，重启后的浏览器验收通过。
- 下一阶段继续做受控真实模型成对评测、请求预算/trace 完整性、Docker runtime 与生产发布/回滚演练。
