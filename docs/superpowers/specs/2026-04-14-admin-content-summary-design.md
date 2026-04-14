# Admin Content Summary Design

## Goal

让运营后台可以直接编辑学校和专业的 `summary`，把最常用的正文摘要维护从 `data/catalog.json` 手工修改迁到后台。

## Why This Next

当前榜单、图片、featured 配置都已经进入后台，但学校和专业的摘要仍然只能改数据文件。这是内容运营主链路里最明显的人工断点。

## Scope

第一版只做 `summary` 编辑，不碰 `sections` 富编辑，不扩成完整 CMS。

支持：

- 查看学校和专业当前摘要
- 编辑并保存学校摘要
- 编辑并保存专业摘要

不支持：

- sections 编辑
- related schools / majors 编辑
- tags、discipline、region 等结构字段编辑
- 版本对比或草稿保存

## Data Model

继续沿用 `data/catalog.json`，不新增数据库表。

每个学校/专业实体继续使用已有的：

- `slug`
- `name`
- `summary`

后台保存时做最小规范化：

- `summary` 去掉首尾空白
- 不允许空字符串

## API Design

新增 admin 内容摘要接口：

- `GET /api/admin/content-summaries`
- `POST /api/admin/content-summaries/schools/{slug}`
- `POST /api/admin/content-summaries/majors/{slug}`

`GET` 返回：

- `schools`
- `majors`

每项包含：

- `slug`
- `name`
- `summary`

`POST` 请求体：

- `summary`

返回更新后的单个实体：

- `slug`
- `name`
- `summary`

## Service Layer

在 `apps/api/app/services/catalog.py` 中新增摘要读写 helper：

- 列出学校/专业摘要
- 按 slug 更新学校/专业摘要
- 写回 `data/catalog.json`
- 清理 catalog cache

这条链只操作 `summary`，不接触其他字段。

## Admin UI

在现有 `/admin` 页面新增两个区块：

- `学校摘要编辑`
- `专业摘要编辑`

展示方式保持轻量：

- 每个实体一个表单
- 标题显示 `name`
- 次行显示 `slug`
- 一个 `textarea` 编辑摘要
- 一个 `保存摘要` 按钮

第一版不做筛选、不做富文本、不做批量保存。

## Web Data Flow

新增一个 admin 内容摘要 API client，用于：

- 拉取学校/专业摘要
- 更新学校摘要
- 更新专业摘要

admin server actions 负责：

- 从 `FormData` 解析 `slug` 和 `summary`
- 调用对应 API client
- `revalidatePath('/admin')`
- `revalidatePath('/')`
- `revalidatePath('/schools/[slug]')` / `revalidatePath('/majors/[slug]')` 用直接 slug 路径刷新

## Validation and Errors

API 校验：

- slug 不存在 -> `404`
- `summary` 为空 -> `422`

Web 行为：

- 列表读取失败时显示局部错误块
- action 失败时维持当前 admin 页面风格，先静默返回

## Testing

API tests:

- `GET /api/admin/content-summaries` 返回学校和专业摘要
- 更新学校摘要成功
- 更新专业摘要成功
- 空摘要被拒绝
- 不存在 slug 被拒绝

Web tests:

- admin 页面能渲染学校摘要编辑区和专业摘要编辑区
- 文本域显示当前摘要
- 保存按钮存在
- action 接线正确

## Follow-Ups

这条线打通后，最自然的后续增强是：

- sections 编辑
- 内容缺失筛选
- featured 实体优先排序
- 摘要长度与质量提示
