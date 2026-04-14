# Ranking Reference Admin Design

## Goal

让运营后台可以查看并维护学校、专业的 `ranking_references`，把“前台可展示榜单引用”推进到“后台可维护榜单引用”。

## Why This Next

当前公开页已经支持学校和专业的“参考榜单”模块，但榜单数据仍然只能通过修改 `data/catalog.json` 维护。这是目前最明显的运营断点：内容已经进入产品主链路，却没有后台维护入口。

## Scope

第一版只做榜单引用维护，不扩成完整内容 CMS。

支持：

- 查看学校和专业已有的榜单引用
- 新增一条榜单引用
- 编辑一条已有榜单引用
- 清空单条榜单引用的来源链接或备注

不支持：

- 批量编辑
- 删除确认弹窗
- 图片抓取
- 正文 sections 编辑
- 排名自动抓取

## Data Model

继续沿用 `catalog.json` 里现有的 `ranking_references` 结构，不新增数据库表。

每条榜单引用保持以下字段：

- `source`
- `year`
- `label`
- `scope`
- `note`
- `url`

后台写入时做最小规范化：

- `source`、`label` 必填
- `year` 必须为正整数
- `scope`、`note`、`url` 可为空
- 空字符串写回为缺省值或空字符串，保持与现有 JSON 风格一致

## API Design

继续沿用 admin 路由，不新建独立子系统。

新增：

- `GET /api/admin/ranking-references`
- `POST /api/admin/ranking-references/schools/{slug}`
- `POST /api/admin/ranking-references/majors/{slug}`

`GET` 返回两组数据：

- `schools`
- `majors`

每组元素包含：

- `slug`
- `name`
- `ranking_references`

`POST` 请求体：

- `ranking_references: list[RankingReference]`

返回更新后的单个实体：

- `slug`
- `name`
- `ranking_references`

## Service Layer

在 API service 层新增一组榜单引用读写 helper，模式与 `featured_content.py` 保持一致：

- 读取 catalog
- 通过 slug 找到学校或专业
- 更新对应实体的 `ranking_references`
- 写回 `data/catalog.json`
- 清理 catalog cache

这条链路只操作榜单引用，不接触 featured content 配置。

## Admin UI

在现有 `/admin` 页面新增一个轻量区块：

- `学校榜单引用`
- `专业榜单引用`

展示方式保持实用优先：

- 每个学校/专业一张简单表单
- 当前已有榜单逐条显示
- 每条榜单一组输入：
  - 榜单来源
  - 年份
  - 结果标签
  - 榜单范围
  - 备注
  - 来源链接

第一版不做动态增删行按钮。为了保持实现轻量，表单固定支持：

- 已有条目全部可编辑
- 额外提供 1 条空白新增行

这样运营可以：

- 编辑已有条目
- 追加一条新条目
- 把某条记录清空到“无效”状态时，提交时过滤掉空记录

## Web Data Flow

新增一个 admin 榜单 API client：

- 拉取榜单配置
- 更新学校榜单配置
- 更新专业榜单配置

admin server actions 负责：

- 从 `FormData` 解析多条榜单引用
- 过滤掉完全空白的行
- 调用对应 API client
- `revalidatePath('/admin')`
- 同时 `revalidatePath('/schools/[slug]')` 和 `revalidatePath('/majors/[slug]')` 暂不做细粒度，第一版直接 revalidate `/`

## Validation and Errors

API 校验：

- slug 不存在 -> `404`
- `source` 或 `label` 缺失 -> `422`
- `year < 1` -> `422`

Web 行为：

- action 失败时沿用当前 admin 页面风格，先静默失败返回，不引入复杂错误状态
- 列表读取失败时显示局部错误块

## Testing

API tests:

- `GET /api/admin/ranking-references` 返回学校和专业榜单引用
- 更新学校榜单引用成功
- 更新专业榜单引用成功
- 非法年份被拒绝
- 不存在 slug 被拒绝

Web tests:

- admin 页面能渲染学校榜单引用区和专业榜单引用区
- 已有榜单字段能显示
- 提交学校榜单 action 调用正确 API
- 提交专业榜单 action 调用正确 API

## Out of Scope Follow-Ups

后续如果继续这条线，最自然的增强是：

- 榜单引用删除按钮
- 榜单引用排序
- 榜单来源模板
- 榜单数据抓取辅助
