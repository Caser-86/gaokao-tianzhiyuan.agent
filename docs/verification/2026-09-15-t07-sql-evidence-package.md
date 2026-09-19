# T07 有限 SQL 证据包验证记录

> 日期：2026-09-15（Asia/Shanghai）
>
> 范围：只验证 M2 T07 的 demo 数据证据包，不代表真实招生数据质量、模型质量或生产 SLA。

## 本次交付

- 新增 `apps/api/app/services/evidence.py`，从现有 SQLModel 目录表构建有上限的 `EvidenceItem` 列表。
- 支持学校/专业实体、精确 slug 或名称、关键词、地区和精确年份过滤。
- `max_items` 与 `max_chars` 由服务端校验；超出字符预算的完整条目跳过，不截断句子。
- 来源字段只接受可引用的 HTTP(S) URL；无效 URL 不会作为链接输出。
- provenance 过期时返回空的可用证据列表；年份请求不会静默回退到旧年份。
- `data/README.md` 记录 SQL 证据边界，明确当前全部内容仍为 `demo`。

## 可复现命令与结果

在 `apps/api` 目录执行：

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_evidence.py
# 4 passed

.\.venv\Scripts\python.exe -m pytest -q ..\..\scripts\tests\test_verify_data_assets.py
# 5 passed

.\.venv\Scripts\python.exe -m ruff check .
# All checks passed!
```

随后执行根目录 `scripts/verify-project.ps1`：数据资产校验通过（2 所学校、4 个专业），API Ruff lint/format 通过，API 全量测试 `236 passed`，Web 测试 `28 files / 130 passed`，typecheck 和 Next.js 生产构建通过。构建过程保留既有的 Next.js `<img>` 性能提示、Node.js action deprecation 提示以及测试依赖的弃用/资源警告；没有失败项。本记录中的来源 URL 是演示 fixture 的占位链接，验证器不会把它们升级为官方来源。

## 明确未完成项

- 尚未维护真实业务输入所需的别名表，也没有用 demo fixture 推导线上 entity miss/召回率。
- 尚未接入真实招生数据；来源许可、更新责任人和可发布年限仍需外部确认。
- 该证据包当前是 T09 的输入基础，尚未将证据注入模型回答或完成同模型成对评测。
