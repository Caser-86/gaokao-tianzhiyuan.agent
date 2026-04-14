# Admin Related Content Design

## Goal

让后台直接维护学校的 `related_majors` 和专业的 `related_schools`，把相关推荐也收进现有内容运营链。

## Scope

- 新增 admin API，用于读取和更新相关推荐配置
- 在 admin 页面新增学校/专业相关推荐编辑区块
- 继续使用 slug 列表做关系编辑，不改 public detail 的展示结构

## Recommended Approach

采用和摘要、正文、榜单一致的最小后台编辑模式：

- API 返回所有学校和专业的当前关系配置
- 后台按实体逐条编辑
- 学校维护 `related_majors`
- 专业维护 `related_schools`
- 输入方式使用多行 slug 文本框，一行一个 slug

这样实现最快，也和现有后台表单风格一致，不会额外引入复杂选择器或拖拽交互。

## API Design

新增 admin 路由：

- `GET /api/admin/related-content`
- `POST /api/admin/related-content/schools/{slug}`
- `POST /api/admin/related-content/majors/{slug}`

响应结构：

- `schools[]`
  - `slug`
  - `name`
  - `related_majors`
- `majors[]`
  - `slug`
  - `name`
  - `related_schools`

更新请求结构：

- 学校：
  - `related_majors: string[]`
- 专业：
  - `related_schools: string[]`

校验规则：

- slug 必须存在于 catalog
- 关系项中的每个 slug 也必须存在于对应实体集合
- 允许空数组，表示当前不展示相关推荐
- 不允许空字符串项

## Web Admin Design

在 admin 页面新增两个区块：

- `学校相关推荐`
- `专业相关推荐`

每个实体显示：

- 名称
- slug
- 多行文本框
- 保存按钮

交互规则：

- 一行一个 slug
- 空行会被忽略
- 保存后刷新 `/admin`、首页和对应详情页

## Error Handling

- API 校验失败返回 `422`
- 目标 slug 不存在返回 `404`
- 后台页面加载失败时显示页面级错误块：
  - `相关推荐加载失败，请稍后重试`
- action 调用失败时继续沿用现有“静默返回 + revalidate on success”模式

## Testing

API：

- 列表接口返回学校和专业的相关推荐配置
- 更新学校相关推荐成功
- 更新专业相关推荐时，非法 related slug 返回 `422`

Web：

- admin API client 能读取和更新相关推荐
- admin 页面能渲染 `学校相关推荐` 和 `专业相关推荐`
- 表单能显示已有 slug 列表

## Out of Scope

- 前台相关推荐 UI 改版
- 多选器/搜索式关系选择
- 排序权重
- 自动推荐关系生成
