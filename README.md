# filter-control-plane

内部筛选控制台：运营任务工作台 + 薄控制平面（`data818` / `data-center` 独占下游）。

- 意图：[`docs/idea.md`](docs/idea.md)
- 决策：[`docs/decisions.md`](docs/decisions.md)
- 规格：[`docs/spec.md`](docs/spec.md)
- 地图：[`docs/project-map.md`](docs/project-map.md)
- Agent：[`AGENTS.md`](AGENTS.md)
- 计划：[`tasks/plan.md`](tasks/plan.md)
- 联调：[`docs/data818-integration.md`](docs/data818-integration.md) · [`docs/data-center-integration.md`](docs/data-center-integration.md)
- API 合同：[`docs/api-contract.md`](docs/api-contract.md)

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 `web/` | Vue 3 · Vite · TypeScript · Element Plus · Pinia · Vue Router · Axios |
| 后端 | Flask · SQLAlchemy · Pydantic · httpx |

账号模型：**控制平面独立账号**（默认 `admin` / `admin123`）。  
下游独占切换：`DOWNSTREAM=auto|mock|data818|data_center`。  
- data818：`DATA818_TOKEN` + `DATA818_AGENT_TOKEN`  
- data-center：`DATA_CENTER_API_KEY` + `DATA_CENTER_TOKEN`  

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

## 生产构建

```bash
cd web && npm run build
python main.py   # 托管 web/dist，端口 5100
```

## 控制台能力（薄平面）

- 登录 / 改密（本地账号）· 明暗主题 · 侧栏折叠记忆
- 任务：列表筛选（类型/国家/状态，URL 可分享）· 新建（价目单价预览）· 详情轮询 · 多格式下载 · 关单/退款/重试 · 导出剩余号
- 只读：订单 · 账单 · 价目 · 公告详情 · 概览统计 · 三方余额（需 admin Token）

## MVP API（节选）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/login` | 登录 |
| POST | `/auth/change-password` | 改密 |
| GET | `/tasks` | 任务列表 |
| POST | `/tasks` | 新建（multipart） |
| GET | `/tasks/<taskNo>` | 详情 |
| GET | `/tasks/<taskNo>/download` | 文件流 |
| GET | `/tasks/<taskNo>/export-remaining` | 剩余号文件流或 `{objectPath}` |
| POST | `/tasks/<taskNo>/close\|refund\|retry` | 运维 |
| GET | `/orders` · `/bills` · `/notices` · `/notices/<id>` | 只读业务 |
| GET | `/meta/health` · `/filter-types` · `/countries` · `/balance` | 元数据 |
| GET | `/meta/products` · `/order-task-types` · `/ledger-types` · `/statistics` · `/third-balances` | 扩展元数据 |

完整字段见 [`docs/api-contract.md`](docs/api-contract.md)；下游映射见 [`docs/decisions.md`](docs/decisions.md)。

## 明确不做

充值 · 商品写 · 完整 RBAC · 第二下游 · 重写筛号引擎（见 `docs/spec.md` Boundaries）。
