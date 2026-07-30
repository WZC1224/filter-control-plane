# 技术决策

> 本仓约定：**集中写在本文件**（表 + 分节）。不另开 `docs/decisions/ADR-NNN` 目录，避免双轨。  
> 新增重大取舍时：追加一节「决策记录」，写清 Context / Decision / Alternatives / Consequences。

## 总表

| 项 | 决定 | 理由 |
|----|------|------|
| 前端 | **Vue 3 + Vite + TypeScript + Element Plus + Pinia + Vue Router + Axios** | 与现有 818 前台同族 |
| 前端目录 | `web/` 独立工程 | 与后端解耦；Vite 代理到 Flask `:5100` |
| Element Plus 加载 | **按需**（`unplugin-vue-components` + `unplugin-auto-import`） | 全量打包主包 ~405 KB gzip；按需后主包 ~92 KB gzip |
| 图标 | 页面显式 import；**禁止** `main.ts` 全局注册全量 icons | 全量 icons 徒增 ~38 KB gzip |
| 后端 | Flask + SQLAlchemy + Pydantic，分层对齐 data818 | 延续栈 |
| 本地库 | SQLite | MVP 零运维 |
| 下游 | **独占** `DOWNSTREAM=auto\|mock\|data818\|data_center` | 禁止并行双源；auto 优先 data_center 三件套 |
| 未配置下游 | `MockAdapter` | 本地可演示 |
| 控制平面角色 | **admin / operator** | 独立账号；不映射 data818；见 `docs/phase2-users.md` |
| 鉴权存储 | JWT 存 Pinia + `localStorage` | 内部工具简单；已知 XSS 可偷 Token（见残留） |
| 角色权威 | **DB `User.role`**；每次导航 `GET /auth/me` | JWT payload 的 role 仅信息用；防本地撒谎 |
| 登录限流 | 进程内滑动窗口（默认 20 / 300s） | 无 Redis；多 worker 各自计数 |
| 生产入口 | `FLASK_ENV=production` → waitress；弱 `SECRET`/`JWT`/`ADMIN_PASSWORD` 拒启 | 见 `docs/deploy.md` |
| 完整中台 | 不做 | 见 `idea.md` |

## 前端栈明细

| 库 | 用途 |
|----|------|
| vue@3 | UI 框架 |
| vite@5 | 构建 |
| typescript | 类型 |
| element-plus（按需）+ @element-plus/icons-vue（按页） | 组件 / 图标 |
| unplugin-vue-components · unplugin-auto-import | Element Plus 按需解析 |
| vue-router@4 | 路由（页面 `import()` 拆包） |
| pinia + pinia-plugin-persistedstate | 状态 / token 持久化 |
| axios | HTTP |
| sass | 样式 |

## 下游对接契约（MVP · data818）

| 控制平面 | data818 |
|----------|---------|
| `GET /tasks` | `GET /business/taskRecord/list` |
| `POST /tasks`（multipart） | `POST /api/filter/create_task` |
| `GET /tasks/<taskNo>` | `GET /api/filter/task_query` |
| `GET /tasks/<taskNo>/download`（代理文件流，`format=csv\|txt\|xlsx\|invalid`） | `csv`→`get_csv`；`txt`→`get_valid_txt`；`xlsx`→`get_xlsx`；`invalid`→`get_invalid_txt` |
| `GET /meta/filter-types` | `GET /api/filter/type/get` |
| `GET /meta/countries` | `GET /api/filter/country_info/get` |
| `GET /meta/balance` | `GET /api/filter/get_balance` |
| `GET /meta/statistics` | `GET /business/statisticsForTable` |
| `POST /tasks/<taskNo>/close` | `POST /admin/third_management/task/close` |
| `POST /tasks/<taskNo>/refund` | `POST /admin/third_management/task/refund` |
| `POST /tasks/<taskNo>/retry` | `POST /admin/super/query/retry` |
| `GET /orders` | `GET /order/list` |
| `GET /bills` | `POST /admin/bill/list` |
| `GET /notices` | `GET /sys_msg/list` |
| `GET /notices/<id>` | `GET /sys_msg/detail` |
| `GET /meta/products` | `GET /product/list`（树扁平化） |
| `GET /meta/order-task-types` | `GET /order/taskTypeList` |
| `GET /meta/ledger-types` | data818 `LedgerType` 固定枚举（无下游 list） |
| `GET /tasks/<taskNo>/export-remaining` | `POST /business/taskRecord/exportRemainingPhone`（文件流或 `objectPath`） |
| `GET /meta/third-balances` | `GET /admin/third_management/get_third_balance`（**仅 admin**） |
| `POST /auth/change-password` | 控制平面本地用户（不下发下游） |
| `GET/POST /users` · `PATCH /users/<id>` | 控制平面用户管理（仅 admin） |

data818 配置：`DATA818_BASE_URL` + `DATA818_TOKEN`（登录 JWT）+ `DATA818_AGENT_TOKEN`（agent）。  
data_center 映射见 [`data-center-integration.md`](data-center-integration.md)。

## 薄平面增量（2026-07-30）

只读价目、订单类型枚举、公告详情、剩余号导出。不做：源文件下载、充值、商品写、并行双下游、完整菜单级 RBAC、与 data818 账号打通。

## 角色（Phase 2）

| 角色 | 能力 |
|------|------|
| `admin` | 用户管理；关单/退款/重试；系统页；`third-balances`；其余全部 |
| `operator` | 主路径（任务/订单/价目/公告/账号）；无用户管理与敏感运维 |

---

## 决策记录

### D-001 · 下游独占（非并行）

- **Status:** Accepted · 2026-07-30
- **Context:** 已有 data818；另有 data-center-backend。运营只需一个真源。并行双源带来余额/任务号冲突与运维复杂度。
- **Decision:** `DOWNSTREAM=auto|mock|data818|data_center` 独占；`auto`：data_center 三件套齐优先，否则 data818，否则 mock。显式指定缺凭证 → **启动失败**（不静默回退）。
- **Alternatives:** 并行路由按任务选源（拒：状态分裂）；启动缺凭证静默 Mock（拒：生产误跑 Mock）。
- **Consequences:** 换源改 `.env` 重启；适配器共享 `FilterHttpAdapter` 路径表，差异留在薄封装。

### D-002 · 控制平面独立账号与角色

- **Status:** Accepted · 2026-07-30
- **Context:** 多人试用；不宜共用一个 admin；不宜先打通 818 账号体系。
- **Decision:** 本地 `User.role=admin|operator` + `is_active`；关单/退款/重试/用户/系统/三方余额仅 admin。种子 `ADMIN_*`；`ensure_admin` 若同名用户非 admin 会**强制升权**（不改密码）。
- **Alternatives:** 映射 data818 账号（拒：范围膨胀）；完整菜单 RBAC（拒：MVP 过重）。
- **Consequences:** 见 `phase2-users.md`；勿把运营账号用户名设成 `ADMIN_USERNAME`。

### D-003 · 每次导航刷新 `/auth/me`

- **Status:** Accepted · 2026-07-30
- **Context:** Pinia 持久化 role；admin 降级/停用后本地仍可能显示旧角色。
- **Decision:** `router.beforeEach` 有 token 且非公开页时强制 `refreshMe()`；失败则登出。
- **Alternatives:** 仅 role 空时刷新（拒：降级后撒谎）；仅 TTL 缓存（可后续加，需证明导航卡顿）。
- **Consequences:** 多一次轻量请求/导航；正确性优先于微优化。

### D-004 · 生产托管与密钥门禁

- **Status:** Accepted · 2026-07-30
- **Context:** 一人运维、单机交付；勿公网裸 Flask debug。
- **Decision:** production → waitress；弱 `SECRET_KEY`/`JWT_SECRET`/`ADMIN_PASSWORD` 拒启；SPA 同进程托管 `web/dist`；安全头 + 可选 `CORS_ORIGINS`。
- **Alternatives:** Docker/K8s（拒：当前运维面过大）；无门禁（拒：默认密钥进生产）。
- **Consequences:** 手册见 `deploy.md`；反向代理 HTTPS 另配。

### D-005 · 登录限流（进程内）

- **Status:** Accepted · 2026-07-30
- **Context:** 登录无验证码；暴力猜密是现实面。
- **Decision:** `LOGIN_RATE_LIMIT_MAX`（默认 20）/ `LOGIN_RATE_WINDOW_SECONDS`（默认 300）；键=客户端 IP；默认**不信** `X-Forwarded-For`（`TRUST_PROXY_HEADERS=1` 才信）。用户不存在仍跑 dummy 哈希。
- **Alternatives:** Redis/共享限流（拒：零运维优先）；默认信 XFF（拒：可伪造绕过/误伤）。
- **Consequences:** 多 worker 各自计数；测试默认 `LOGIN_RATE_LIMIT_MAX=0`。

### D-006 · Element Plus 按需打包

- **Status:** Accepted · 2026-07-30
- **Context:** 全量 `app.use(ElementPlus)` + 全量 CSS + 全量 icons → 主包 405 KB gzip，超内部预算。
- **Decision:** unplugin 按需组件/样式；`el-config-provider` 中文；暗色仅保留 `dark/css-vars.css`；图标按页 import。
- **Alternatives:** 保持全量（拒：已测过大）；换组件库（拒：与 818 前台同族价值更高）。
- **Consequences:** 勿再在 `main.ts` 全量注册；新增组件靠模板/`ElMessage` 等解析器导入。

## 已知残留（有意未改）

| 项 | 说明 |
|----|------|
| JWT in `localStorage` | XSS 可偷；改 httpOnly cookie 需另开认证改造 |
| 无严格 CSP | Element Plus 内联样式成本高 |
| 限流非集群共享 | 多 waitress/多机各自窗口 |
| Dashboard 与 Layout 重复拉 balance/health | 正确优先；未测到用户侧卡顿前不耦合 |
