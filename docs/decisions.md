# 技术决策

> 2026-07-30 · 由 agent 代定（用户授权）  
> 更新：前端改为 Vue 3 稳定栈（对齐 data-center818-frontEnd）

| 项 | 决定 | 理由 |
|----|------|------|
| 前端 | **Vue 3 + Vite + TypeScript + Element Plus + Pinia + Vue Router + Axios** | 与现有 818 前台同族；均为市场稳定方案 |
| 前端目录 | `web/` 独立工程 | 与后端解耦；`vite` 开发代理到 Flask `:5100` |
| 后端 | Flask + SQLAlchemy + Pydantic，分层对齐 data818 | 延续栈 |
| 本地库 | SQLite | MVP 零运维 |
| 下游 | `Data818Adapter` HTTP | 旧系统当下游 |
| 未配置下游 | `MockAdapter` | 本地可演示 |
| 默认首页 | 任务列表 + 新建 | 对齐 idea.md |
| 第二下游 | 暂缓 | 单下游先验证 |
| 完整中台 | 不做 | 见 idea.md |

## 前端栈明细

| 库 | 用途 |
|----|------|
| vue@3 | UI 框架 |
| vite@5 | 构建 |
| typescript | 类型 |
| element-plus + @element-plus/icons-vue | 组件库 |
| vue-router@4 | 路由 |
| pinia + pinia-plugin-persistedstate | 状态 / token 持久化 |
| axios | HTTP |
| sass | 样式 |

## 下游对接契约（MVP）

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
| `GET /meta/third-balances` | `GET /admin/third_management/get_third_balance` |
| `POST /auth/change-password` | 控制平面本地用户（不下发下游） |

配置：`DATA818_BASE_URL` + `DATA818_TOKEN`。

## 薄平面增量（2026-07-30）

只读价目、订单类型枚举、公告详情、剩余号导出。不做：源文件下载、充值、商品写、第二下游、完整 RBAC。
