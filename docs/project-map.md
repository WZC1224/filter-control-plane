# Project Map: filter-control-plane

> 会话切换时只加载与当前任务相关的一节，勿整仓灌入。

## 产品定位

运营统一入口：下任务 → 看进度 → 取结果。控制平面独立账号；下游 HTTP 适配 `data818` / `data_center`（`DOWNSTREAM` 独占）。

## Backend（`app/`）

| 区域 | 路径 | 说明 |
|------|------|------|
| 启动 | `main.py` · `app/__init__.py` | `:5100`；有 `web/dist` 则托管 SPA；安全头 |
| 配置 | `config.py` | `settings`；生产弱密钥拒启；登录限流 / CORS |
| 认证 | `app/api/auth.py` · `app/service/auth.py` · `app/exts/` | JWT；`admin_required`；登录限流 |
| 用户 | `app/api/auth.py`（`/users`） | admin CRUD；见 phase2-users |
| 任务 API | `app/api/tasks.py` · `app/service/task.py` | 列表/创建/详情/下载流 |
| 元数据 | `app/api/meta.py` | health / filter-types / countries；third-balances=admin |
| 适配器 | `app/adapters/` | `FilterHttpAdapter`；Mock；data818；data_center（X-Api-Key） |
| 响应 | `app/utils/response.py` | 与 818 习惯兼容的 envelope |

**模式：** api 不直连下游；下载成功非 JSON；`DOWNSTREAM` 独占。

## Frontend（`web/src/`）

| 区域 | 路径 | 说明 |
|------|------|------|
| 入口 | `main.ts` · `App.vue` · `router/` | 按需 Element Plus；导航强制 `/auth/me` |
| 状态 | `stores/user.ts` | token 持久化（localStorage） |
| HTTP | `api/http.ts` | `request` + `downloadBlob` |
| 布局 | `layouts/AppLayout.vue` | 侧栏导航 |
| 页面 | `LoginView` · `DashboardView` · `Task*` · `Orders` · `Bills` · `Products` · `Notices*` · `Users` · `Account` · `System` | 主路径 UI |
| 构建 | `vite.config.ts` | unplugin Element Plus 解析；代理含 `/users` |

**模式：** Element Plus **按需**（勿全量 `app.use`）；blob 下载不弹 JSON 详情。

## Tests（`tests/`）

| 文件 | 覆盖 |
|------|------|
| `test_auth.py` | 登录成败 |
| `test_users.py` | 角色 / 用户管理 |
| `test_login_rate_limit.py` | 登录 429 / XFF 策略 |
| `test_production_guards.py` | 生产弱密钥拒启 |
| `test_tasks.py` | 列表/创建/下载流/鉴权/format |
| `test_data818_download.py` | resultUrl 拉取、业务错误、filename* 解码 |
| `test_data_center_adapter.py` | X-Api-Key/JWT 分流、公告软降级、adapter_name |
| `conftest.py` | 临时 SQLite + 强制 Mock；默认关登录限流 |

命令：`pytest -q`

## Docs

| 文档 | 何时读 |
|------|--------|
| `docs/spec.md` | 改范围 / 验收 |
| `docs/decisions.md` | 改栈、下游独占、角色、限流、打包（含 D-001…） |
| `docs/phase2-users.md` | 多账号 / 角色 |
| `docs/deploy.md` · `docs/pilot.md` | 部署 / 运营试用 |
| `docs/data818-integration.md` | data818 真下游联调 |
| `docs/data-center-integration.md` | data-center 真下游联调 |
| `tasks/todo.md` | 执行中的任务切片 |
