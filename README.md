# filter-control-plane

内部筛选控制台：运营任务工作台 + 薄控制平面（`data818` 等为下游）。

- 意图：[`docs/idea.md`](docs/idea.md)
- 决策：[`docs/decisions.md`](docs/decisions.md)
- 规格：[`docs/spec.md`](docs/spec.md)
- 地图：[`docs/project-map.md`](docs/project-map.md)
- Agent：[`AGENTS.md`](AGENTS.md)
- 计划：[`tasks/plan.md`](tasks/plan.md)
- 联调：[`docs/data818-integration.md`](docs/data818-integration.md)
- 试用：[`docs/pilot.md`](docs/pilot.md)
- 部署：[`docs/deploy.md`](docs/deploy.md)
- 用户角色：[`docs/phase2-users.md`](docs/phase2-users.md)
- API 合同：[`docs/api-contract.md`](docs/api-contract.md)

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 `web/` | Vue 3 · Vite · TypeScript · Element Plus（**按需**）· Pinia · Vue Router · Axios |
| 后端 | Flask · SQLAlchemy · Pydantic · httpx · waitress（生产） |

账号模型：**控制平面独立账号**（默认 `admin` / `admin123`，角色 `admin`）。支持多用户：`admin` / `operator`，见 [`docs/phase2-users.md`](docs/phase2-users.md)。下游需双 Token：`DATA818_TOKEN`（登录 JWT）+ `DATA818_AGENT_TOKEN`（agent），见 [`docs/data818-integration.md`](docs/data818-integration.md)。

下载：**控制平面代理文件流**（`Content-Disposition` 附件）；前端 blob 保存。Query `format=csv|txt|xlsx|invalid`（默认 `csv`）。

## 开发启动

```bash
# 后端
cd filter-control-plane
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python main.py
```

```bash
# 前端
cd web
npm install
npm run dev
```

打开 http://127.0.0.1:5173 。未配置 `DATA818_*` 时使用 **MockAdapter**。生产也可只开 `:5100`（托管 `web/dist`）。

## 测试与构建

```bash
# 后端（Mock）
pytest -q

# 前端
cd web && npm run build
```

## 生产构建与启动

见完整手册 [`docs/deploy.md`](docs/deploy.md)。摘要：

```bash
cd web && npm run build && cd ..
# .env 设 FLASK_ENV=production + 强 SECRET_KEY / JWT_SECRET / ADMIN_PASSWORD
python main.py   # waitress 托管 API + web/dist，默认 :5100
```

探活：`GET /meta/health`。
## 控制台能力（薄平面）

- 登录 / 改密（本地账号）· 明暗主题 · 侧栏折叠记忆 · 登录限流（同 IP）
- 任务：列表筛选（类型/国家/状态，URL 可分享）· 新建（价目单价预览）· 详情轮询 · 多格式下载 · 关单/退款/重试（admin）· 导出剩余号
- 只读：订单 · 账单 · 价目 · 公告详情 · 概览统计 · 三方余额（admin）
- 用户：`admin` 管理 `admin`/`operator`（见 phase2-users）

## MVP API（节选）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/login` | 登录（限流；超限 429） |
| GET | `/auth/me` | 当前用户（导航强制刷新） |
| POST | `/auth/change-password` | 改密 |
| GET/POST | `/users` · `PATCH /users/<id>` | 用户管理（admin） |
| GET | `/tasks` | 任务列表 |
| POST | `/tasks` | 新建（multipart） |
| GET | `/tasks/<taskNo>` | 详情 |
| GET | `/tasks/<taskNo>/download` | 文件流 |
| GET | `/tasks/<taskNo>/export-remaining` | 剩余号文件流或 `{objectPath}` |
| POST | `/tasks/<taskNo>/close\|refund\|retry` | 运维（admin） |
| GET | `/orders` · `/bills` · `/notices` · `/notices/<id>` | 只读业务 |
| GET | `/meta/health` · `/filter-types` · `/countries` · `/balance` | 元数据 |
| GET | `/meta/products` · `/order-task-types` · `/ledger-types` · `/statistics` | 扩展元数据 |
| GET | `/meta/third-balances` | 三方余额（admin） |

完整字段见 [`docs/api-contract.md`](docs/api-contract.md)；下游映射见 [`docs/decisions.md`](docs/decisions.md)。

## 明确不做

充值 · 商品写 · 完整菜单级 RBAC · 重写筛号引擎（见 `docs/spec.md` Boundaries）。
下游仅 **data818**（或 Mock），已剥离 data-center。
