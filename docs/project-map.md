# Project Map: filter-control-plane

> 会话切换时只加载与当前任务相关的一节，勿整仓灌入。

## 产品定位

运营统一入口：下任务 → 看进度 → 取结果。控制平面独立账号；下游 HTTP 适配 `data818`。

## Backend（`app/`）

| 区域 | 路径 | 说明 |
|------|------|------|
| 启动 | `main.py` · `app/__init__.py` | `:5100`；有 `web/dist` 则托管 SPA |
| 配置 | `config.py` | `settings`；`DATA818_*` 空则 Mock |
| 认证 | `app/api/auth.py` · `app/service/auth.py` · `app/exts/` | JWT；默认 admin |
| 任务 API | `app/api/tasks.py` · `app/service/task.py` | 列表/创建/详情/下载流 |
| 元数据 | `app/api/meta.py` | health / filter-types / countries |
| 适配器 | `app/adapters/` | `FilePayload`；Mock；data818（csv 可跟 resultUrl） |
| 响应 | `app/utils/response.py` | 与 818 习惯兼容的 envelope |

**模式：** api 不直连下游；下载成功非 JSON。

## Frontend（`web/src/`）

| 区域 | 路径 | 说明 |
|------|------|------|
| 入口 | `main.ts` · `App.vue` · `router/` | 登录守卫 |
| 状态 | `stores/user.ts` | token 持久化 |
| HTTP | `api/http.ts` | `request` + `downloadBlob` |
| 布局 | `layouts/AppLayout.vue` | 侧栏导航 |
| 页面 | `LoginView` · `DashboardView` · `TaskListView` · `TaskCreateView` · `TaskDetailView` · `AccountView` · `SystemView` | 主路径 UI |

**模式：** Element Plus；blob 下载不弹 JSON 详情。

## Tests（`tests/`）

| 文件 | 覆盖 |
|------|------|
| `test_auth.py` | 登录成败 |
| `test_tasks.py` | 列表/创建/下载流/鉴权/format |
| `test_data818_download.py` | resultUrl 拉取、业务错误、filename* 解码 |
| `conftest.py` | 临时 SQLite + 强制 Mock |

命令：`pytest -q`

## Docs

| 文档 | 何时读 |
|------|--------|
| `docs/spec.md` | 改范围 / 验收 |
| `docs/decisions.md` | 改栈或下游契约 |
| `docs/data818-integration.md` | 真下游联调 |
| `tasks/todo.md` | 执行中的任务切片 |
