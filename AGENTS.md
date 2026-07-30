# AGENTS.md — filter-control-plane

面向 Agent 的会话入口。详细规范见 Cursor rule：`.cursor/rules/filter-control-plane.mdc`（glob: `filter-control-plane/**`）。

## Brain dump（开新会话可粘贴）

```
PROJECT: filter-control-plane — 内部筛选控制台（运营工作台 + 薄控制平面）
STACK: Flask/Pydantic/SQLite + Vue3/Vite/Element Plus；下游 data818/data_center 经 adapters（独占 DOWNSTREAM）
DOCS: docs/spec.md · docs/decisions.md · docs/project-map.md
COMMANDS: pytest -q | python main.py | cd web && npm run dev | npm run build
CONSTRAINTS: 不重写筛号引擎；独立账号；下载=代理文件流；Ask before 双下游并行/换库/任务主库
TESTS: tests/ 必须先红后绿改行为；提交前 pytest -q
```

## 按任务加载

| 任务类型 | 先读 |
|----------|------|
| 改 API / 下载 | `docs/project-map.md` Backend + `app/api/tasks.py` + `app/adapters/` + `tests/test_tasks.py` |
| 改下游对接 | `docs/decisions.md` + `app/adapters/filter_http.py` + `data818.py` / `data_center.py` + 对应 integration.md |
| 改前端 | `web/src/layouts/AppLayout.vue` · `web/src/views/*` + `web/src/api/` · Element Plus |
| 改范围 | `docs/spec.md` Boundaries，先更新 spec 再改代码 |
