# Spec: filter-control-plane（内部筛选控制台）

> 状态：**已批准（Phase 2 · data-center 独占适配器）** · Plan/Tasks 执行中 · 2026-07-30  
> 依据：`docs/idea.md` + `docs/decisions.md`  
> 联调清单：`docs/data818-integration.md` · `docs/data-center-integration.md`

## Objective

为公司内部**业务/运营**提供统一入口，完成筛选主路径：

**下任务 → 看进度 → 取结果**

控制平面负责登录、任务编排入口与状态汇总展示；`data818`（及远期其他系统）通过适配器作为下游，**不重写**筛号引擎，不另造第三套筛选中心。

### 用户故事

1. 作为运营，我登录控制台后能看到任务列表与状态，而不必打开 data818 / data-center 两套后台。
2. 作为运营，我能上传 `.txt`、选择筛选类型与国家并提交任务。
3. 作为运营，我能查看任务详情，并获取结果下载信息/链接。
4. 作为开发，未配置下游时可用 Mock 本地演示同一套 API/UI。

### Success Criteria（可验收）

- [x] 本地：未配 `DATA818_*` 时，Mock 模式下登录 → 列表 → 建任务 → 详情全流程可走通
- [x] 联调：配置有效 `DATA818_BASE_URL` + `DATA818_TOKEN` 后，列表/建任务/查询/下载能打到真实 data818 且错误信息可读（见 `docs/data818-integration.md`；`scripts/smoke_phase1.py` 只读 4/4 PASS，建单路径已验，真实下载待首个已完成单）
- [x] **Phase 2**：独占 `data_center` 适配器（`X-Api-Key` + JWT）；`DOWNSTREAM` 三选一；公告软降级；pytest 覆盖鉴权分流（真联调见 `docs/data-center-integration.md`）
- [x] **下载**：`GET /tasks/<taskNo>/download` 由控制平面**代理文件流**；前端 blob 下载；Mock 可下载假文件
- [x] 账号：控制平面**独立账号**；下游用配置的服务 Token
- [x] 前端为 Vue 3 + Element Plus，开发态代理后端，生产态 `web/dist` 可由 Flask 托管
- [x] 后端分层清晰；下游切换只改适配器
- [x] 文档与实现一致（含 pytest 命令）
- [x] **明确不做**项未被实现（见 Boundaries · Never）
- [x] `pytest -q` 覆盖 auth + tasks（含文件流下载）

## Tech Stack

| 层 | 技术 | 版本锚点（与 package/requirements 对齐） |
|----|------|------------------------------------------|
| 后端 | Python · Flask · Flask-SQLAlchemy · Pydantic v2 · python-jose · httpx | 见 `requirements.txt` |
| 前端 | Vue 3 · Vite 5 · TypeScript · Element Plus · Pinia · Vue Router · Axios · Sass | 见 `web/package.json` |
| 本地库 | SQLite（控制平面用户） | `DATABASE_URL` |
| 下游 | HTTP → data818 | 可选；缺省 Mock |

## Commands

```bash
# 后端
cd filter-control-plane
python -m venv .venv
.\.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env            # 按需填写 DATA818_*
python main.py                    # http://127.0.0.1:5100

# 前端开发
cd web
npm install
npm run dev                       # http://127.0.0.1:5173 ，代理 /auth /tasks /meta → :5100

# 前端生产构建（产物 web/dist，Flask 托管）
npm run build
npm run preview

# 后端冒烟（示例）
.\.venv\Scripts\python -c "from app import create_app; c=create_app().test_client(); print(c.get('/meta/health').get_json())"
```

## Project Structure

```
filter-control-plane/
├── docs/
│   ├── idea.md              # 已确认意图
│   ├── decisions.md         # 技术决策
│   └── spec.md              # 本规格（真源）
├── app/
│   ├── api/                 # 路由：薄控制器
│   ├── schema/              # Pydantic 入参
│   ├── service/             # 业务编排
│   ├── adapters/            # 下游：base / mock / data818
│   ├── models/              # 控制平面 ORM（用户）
│   ├── exts/                # db / jwt / auth_guard
│   └── utils/               # Success / Fail / _Exception
├── web/                     # Vue 3 前端工程
│   └── src/
│       ├── api/             # Axios 封装与接口
│       ├── stores/          # Pinia
│       ├── router/
│       ├── views/           # LoginView / TasksView
│       └── types/
├── config.py
├── main.py
├── requirements.txt
├── tasks/                   # Phase 2/3 产出（plan.md / todo.md），审阅后创建
└── README.md
```

测试目录约定（待 Phase 2 落地）：

```
tests/                       # pytest：适配器契约、auth、tasks API
web/ 内组件测试暂不强制；优先 API + 构建通过
```

## Code Style

### 后端（对齐 data818 分层习惯）

```python
# api：只做解析 → Service → Success/Fail
@bp.route('', methods=['GET'])
@login_required
def list_tasks():
    data = TaskListSchema(**request.args.to_dict())
    return Success(result=TaskService.list_tasks(data))

# service：编排；下游只经 adapter
# adapter：统一 DownstreamAdapter 契约；禁止在 api 层直接 httpx
```

- 业务错误：`raise _Exception(code, message)`，HTTP 统一 200 + body.code
- 配置：只读 `from config import settings`
- 命名：模块/蓝图 `url_prefix` 与文件名对应；适配器方法英文 snake_case

### 前端

```ts
// api 层返回已解包的 result；错误由 http 拦截器 ElMessage
export function listTasksApi(params?: Record<string, string | number | undefined>) {
  return request<TaskListResult>({ url: '/tasks', method: 'get', params })
}
```

- 视图：`<script setup lang="ts">` + Element Plus
- 路径别名：`@/` → `src/`
- Token：Pinia persist（`fcp-user`），请求头 `Authorization: Bearer …`

## Testing Strategy

| 层级 | 框架/方式 | 覆盖 |
|------|-----------|------|
| 后端单元/接口 | pytest + Flask test_client（待加） | auth 登录失败/成功；tasks CRUD 在 Mock 下；adapter `_unwrap` 错误码 |
| 适配器 | pytest + httpx mock（待加） | data818 路径与参数映射正确 |
| 前端 | `npm run build`（vue-tsc + vite）为门禁；E2E 暂缓 |
| 手工 | Mock 全流程；有 token 时对 data818 冒烟 |

**覆盖期望（MVP）：** 后端关键路径有测试即可，不设强百分比；合并/交付前必须 `npm run build` + Mock API 冒烟通过。

## Boundaries

### Always

- 改下游对接先改 `adapters/` 与 `docs/decisions.md` 契约表
- 用户可见主路径变更同步更新本 spec 的 Success Criteria
- 提交前：Mock 冒烟 +（若改了前端）`npm run build`
- 密钥只进 `.env`，不进仓库

### Ask first

- 增加第二个下游（~~data-center-backend~~ → **已批准独占 env 切换**；并行/按任务分流仍 Ask first）
- 换库（SQLite → MySQL）、引入 Redis/Mongo
- 新增 npm/pip 大依赖或换 UI 库
- 控制平面自建「任务主库」替代纯代理
- 权限模型升级（多角色/菜单/与 data818 账号打通）
- **双下游并行**或 UI 切换源（非独占）

### Never

- 重写筛号引擎或把 data818 业务逻辑复制进本仓库
- 实现完整数据中台（数仓/血缘/自助 SQL）
- Day1 迁移商品/充值/复杂菜单
- 对外 ToB 售卖形态
- 提交 `.env`、真实 `DATA818_TOKEN`、生产密码

## API 契约（控制平面对外）

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| POST | `/auth/login` | 否 | `{username,password}` → `{token,username}` |
| GET | `/auth/me` | 是 | 当前用户 |
| GET | `/tasks` | 是 | 分页列表（query: pageNo, pageSize, taskType, …） |
| POST | `/tasks` | 是 | multipart: file, filterType, countryCode, describe |
| GET | `/tasks/<taskNo>` | 是 | 详情 |
| GET | `/tasks/<taskNo>/download` | 是 | **代理文件流**；`format=csv\|txt`（默认 csv）。完整合同见 `docs/api-contract.md` |
| GET | `/meta/health` | 否 | `{service, version, adapter, mock, time}` |
| GET | `/meta/filter-types` | 是 | 筛选类型 |
| GET | `/meta/countries` | 是 | 国家 |

响应 envelope：`{ code, success, message, result, timestamp }`（与 818 前端习惯兼容）。

## 当前实现状态（相对本 spec）

| 项 | 状态 |
|----|------|
| 意图 / 决策 / spec | 已有 |
| Flask MVP + Mock/data818/data_center 适配器 | 已有；下载为 `FilePayload` 文件流；`DOWNSTREAM` 独占 |
| Vue3 登录 + 任务页 + blob 下载 | 已有；build 通过 |
| pytest | **已有**（`pytest -q`） |
| 真实 data818 联调验证 | 只读冒烟已过（清单已写） |
| 真实 data-center 联调 | **待 Key/JWT**（清单已写） |
| Phase 2 plan · tasks | 独占 data-center；见 `tasks/plan.md` |

## Open Questions

| 问题 | 结论（2026-07-30） |
|------|-------------------|
| 下载体验 | **控制平面代理文件流** |
| 账号模型 | **独立账号**；下游用服务凭证 |
| 联调 vs 测试优先 | **先 Mock + pytest，有凭证再联调** |
| 第二下游 data-center | **独占 env 切换已接**；并行分流仍暂缓 |

---

**下一门禁：** 有 `DATA_CENTER_*` 时跑 `scripts/smoke_phase2_data_center.py` 勾联调清单。
