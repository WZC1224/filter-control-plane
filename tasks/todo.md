# Todo: filter-control-plane

> Plan：`tasks/plan.md` · Spec：`docs/spec.md`  
> 状态：**待审阅** — 回复「批准 plan」后按 Task 1→5 Implement  
> Definition of Done（每项任务）：验收条件满足 + Verification 勾完 + 不引入 Never 范围

---

## Task 1: 扩展下游下载契约为文件载荷

**Description:** 把 `DownstreamAdapter.get_download` 从「返回 JSON 占位」改为返回统一文件载荷（bytes + content_type + filename）。Mock 给可预测小文件；Data818 按 format 请求下游并填同一结构；业务错误继续 `_Exception`。

**Acceptance criteria:**
- [ ] 契约签名与载荷字段在 `base.py`（或同级 dataclass）写清
- [ ] Mock：给定 taskNo 返回非空 content
- [ ] Data818：按 `format` 选下游 path；HTTP/业务失败转 `_Exception`
- [ ] list/create/query 接口行为不变

**Verification:**
- [ ] Tests pass: （本任务可先手工）`get_adapter().get_download('MOCK-1001')` 在 Flask shell/短脚本中 content 非空；完整断言见 Task 4
- [ ] Build succeeds: 后端可 `create_app()` 无 import 错误
- [ ] Manual check: 无

**Dependencies:** None  

**Files likely touched:**
- `app/adapters/base.py`
- `app/adapters/mock.py`
- `app/adapters/data818.py`

**Estimated scope:** S（1–3 files）

---

## Task 2: API 代理文件流

**Description:** `TaskService` + `GET /tasks/<taskNo>/download` 成功时返回 Flask 文件 Response（`Content-Disposition: attachment`）；可选 query `format`（默认 csv）。失败仍 JSON Fail。

**Acceptance criteria:**
- [ ] 成功响应体不是 `{success, result}` envelope
- [ ] 带合理 `Content-Type` 与 filename
- [ ] 未登录 / 下游错误仍为 JSON 业务错误

**Verification:**
- [ ] Tests pass: 将在 Task 4 固化；本任务用 test_client 或 curl 抽查一次
- [ ] Manual check: Mock 登录后 download，body 含 Mock 文件内容

**Dependencies:** Task 1  

**Files likely touched:**
- `app/service/task.py`
- `app/api/tasks.py`

**Estimated scope:** S（1–2 files）

---

### Checkpoint: After Tasks 1–2（Foundation）

- [ ] Mock download 为文件流
- [ ] 主路径 list/create 未坏
- [ ] 人确认默认 `format=csv`（或改为 txt）后再进 Task 3

---

## Task 3: 前端 blob 触发下载

**Description:** 任务页「下载」改为带 Token 的 blob 请求并触发浏览器保存；「详情」仍展示 JSON。若响应实为 JSON 错误，解析后 ElMessage。

**Acceptance criteria:**
- [ ] 下载不再打开详情 Dialog
- [ ] 能保存文件（优先 Content-Disposition 文件名）
- [ ] 错误有提示

**Verification:**
- [ ] Build succeeds: `cd web && npm run build`
- [ ] Manual check: Mock 下点击下载得到文件

**Dependencies:** Task 2  

**Files likely touched:**
- `web/src/api/task.ts`
- `web/src/api/http.ts`（或专用 `downloadBlob`）
- `web/src/views/TasksView.vue`

**Estimated scope:** M（3 files）

---

## Task 4: pytest 基础套件

**Description:** 引入 pytest + conftest（test app、临时 SQLite、Mock 适配器）。覆盖登录失败/成功、任务列表、建任务、下载为文件流。

**Acceptance criteria:**
- [ ] `pytest -q` 一条命令可跑且全绿
- [ ] 至少含 auth + tasks（含 download）用例
- [ ] `requirements.txt` / README 写明命令

**Verification:**
- [ ] Tests pass: `pytest -q`
- [ ] Manual check: 无

**Dependencies:** Task 2  

**Files likely touched:**
- `tests/conftest.py`
- `tests/test_auth.py`
- `tests/test_tasks.py`
- `requirements.txt`
- `README.md`（仅测试命令一行，细文档放 Task 5 亦可）

**Estimated scope:** M（≤5 files；禁止顺手大重构）

---

### Checkpoint: After Tasks 3–4（Core）

- [ ] `pytest -q` 绿
- [ ] `npm run build` 绿
- [ ] 浏览器：下载文件 + 详情 JSON 分离

---

## Task 5: 文档与 data818 联调附录

**Description:** 同步 README、decisions、spec 状态句；新建联调检查清单（环境变量、权限、format、常见错误）；标明无 token 时联调 Success Criteria 阻塞。

**Acceptance criteria:**
- [ ] 下载=代理流、独立账号、pytest 命令在 README 可见
- [ ] decisions 契约表与代码一致
- [ ] `docs/data818-integration.md` 可勾选

**Verification:**
- [ ] Manual check: 文档与实现交叉阅读无矛盾

**Dependencies:** Task 3、Task 4  

**Files likely touched:**
- `README.md`
- `docs/decisions.md`
- `docs/spec.md`
- `docs/data818-integration.md`

**Estimated scope:** S（文档）

---

### Checkpoint: Complete

- [ ] Plan Overview 目标达成
- [ ] Spec 中非联调 Success Criteria 可勾选
- [ ] Ready for human review

---

## 进度总览

- [x] Task 1
- [x] Task 2
- [x] Checkpoint Foundation
- [x] Task 3
- [x] Task 4
- [x] Checkpoint Core
- [x] Task 5
- [x] Checkpoint Complete

**状态：** Task 1–5 已实现并通过 `pytest -q`（7 passed）与 `npm run build`。未自动 git commit。
