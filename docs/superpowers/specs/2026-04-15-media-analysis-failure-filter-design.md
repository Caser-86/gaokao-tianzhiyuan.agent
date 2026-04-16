# Media Analysis Failure Filter Design

## Goal

让运营在 `/admin` 的媒体分析区域里更快聚焦失败记录，能直接看到当前列表中的失败数量，并一键切换到“只看失败”。

## Scope

本次只做管理台页面层增强：

- 复用现有 `/api/admin/media-analysis-events?status=...` 过滤能力
- 在媒体分析区域增加当前列表概览
- 增加“只看失败记录 / 查看全部媒体记录”快捷入口
- 保留现有用户 ID、自动路由筛选和其他 admin 页面上下文

不做：

- 新增后端统计接口
- 新增数据库字段
- 修改媒体分析事件返回结构

## Current State

- 后端已支持按 `status / user_id / auto_routed_to_chat` 过滤媒体分析记录。
- `/admin` 已有媒体分析筛选表单，但缺少失败聚焦入口。
- 运营要看失败项时，需要手动展开状态下拉并提交。

## Options

### Option 1: 只保留现有表单

- 优点：零改动
- 缺点：失败排障路径仍然慢，用户需要手动操作两步以上

### Option 2: 新增后端统计接口

- 优点：能展示全量失败统计
- 缺点：引入新接口和测试，超出当前最小闭环

### Option 3: 前端基于当前列表做失败概览和快捷筛选

- 优点：改动小、见效快、复用已有过滤参数
- 缺点：数量仅代表当前已加载列表，不是全库统计

## Recommendation

选择 Option 3。

对当前阶段最合适：不扩后端、不碰数据模型，只把已有过滤能力包装成更顺手的运营入口。

## Design

### Admin page data flow

- 继续由 `app/(admin)/admin/page.tsx` 解析 `media_analysis_status`
- 基于现有 `buildAdminHrefBase()` 生成两个快捷链接：
  - `showFailedMediaAnalysisOnlyHref`
  - `showAllMediaAnalysisStatusesHref`
- 链接需要保留：
  - `preview_date`
  - 当前图片/榜单/摘要/正文/相关内容等 admin 上下文参数
  - `media_analysis_user_id`
  - `media_analysis_auto_routed`

### Dashboard presentation

- 在“最近媒体分析记录”标题下增加当前列表概览文案
- 概览展示当前窗口内：
  - 总数
  - `failed` 数量
  - `pending` 数量
- 当当前状态不是 `failed` 且存在失败项时，展示“只看失败记录（n）”
- 当当前状态是 `failed` 时，展示“查看全部媒体记录”
- 保留原有“清除媒体筛选”链接，用于一次性清空媒体相关筛选

### Behavior details

- 概览基于当前 `mediaAnalysisEvents` 计算，不新增接口请求
- 若媒体列表为空或加载失败，则不显示概览和快捷链接
- 若当前列表中失败数为 0，则不显示“只看失败记录”入口

## Testing

- `apps/web/tests/admin-dashboard.test.tsx`
  - 验证媒体分析区域显示失败概览
  - 验证“只看失败记录 / 查看全部媒体记录”入口展示逻辑
- `apps/web/tests/admin-page.test.tsx`
  - 验证失败快捷链接保留现有筛选参数
  - 验证 `media_analysis_status=failed` 时页面走失败过滤并展示返回全部入口

## Out of Scope

- 全库媒体失败统计
- 失败趋势图表
- 多状态组合筛选器
