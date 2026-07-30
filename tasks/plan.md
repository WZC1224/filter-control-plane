# Implementation Plan: filter-control-plane（下载代理 + 测试门禁）

> Spec：`docs/spec.md`（已批准）  
> 状态：**已执行**（incremental Task 1–5 · 2026-07-30）  
> 本轮不做：第二下游、任务主库、账号映射、E2E

## Overview

在已有 Flask 控制平面 + Vue3 任务台骨架上，把「取结果」做成**控制平面代理文件流**（前端 blob 下载），并用 **pytest（Mock）** 锁住 auth/任务/下载主路径；文档与联调清单收尾。独立账号与 `DATA818_TOKEN` 服务凭证模型不变。

## Architecture Decisions

- **下载响应分叉：** 成功 → 原始文件 `Response`（`Content-Disposition`）；失败 → 现有 JSON envelope（`Fail` / `_Exception`）。避免前端用同一套 `success` 解析器解文件。
- **适配器返回值：** `get_download` 改为结构化载荷（`content: bytes`、`content_type`、`filename`），由 API 层组装 Flask Response；不在 adapter 里依赖 Flask。
- **下游映射：** 默认 `format=csv` → data818 `/api/filter/get_csv`；若实测为 JSON 包装则适配器解包或改走 `get_valid_txt`（`format=txt`）。MVP 支持 `csv|txt`（xlsx 可选，Ask first 若工作量大）。
- **大文件：** data818 侧优先 `httpx` 读完整 body（MVP）；若单文件常 >50MB 再改为 `stream_with_context`（本轮不强制）。
- **前端鉴权下载：** `axios` + `responseType: 'blob'` + object URL；不用裸 `<a href>`（无法带 Bearer）。
- **测试优先于真联调：** 无 token 不阻塞；联调清单单独文档，人工勾选。

## Dependency Graph

```
FileDownload 载荷契约 (adapters/base)
    │
    ├── MockAdapter 假文件
    ├── Data818Adapter HTTP 拉文件
    │
    └── TaskService.download → api/tasks 文件 Response
            │
            ├── 前端 blob 下载 UI
            └── pytest（auth / tasks / download）
                    │
                    └── 文档 + data818 联调清单
```

## Task List

### Phase 1: Foundation（下载契约 + API）

- [ ] Task 1: 扩展下游下载契约为文件载荷（S）
- [ ] Task 2: API 代理文件流（S）

### Checkpoint: Foundation

- [ ] Mock 下 `GET /tasks/<id>/download` 返回非 JSON 文件体 + `Content-Disposition`
- [ ] list / create / query 无回归（手工或即将补的测试）
- [ ] 与人确认：默认 format 与下游路径无异议后再做前端

### Phase 2: Core Features（前端闭环 + 测试）

- [ ] Task 3: 前端 blob 触发下载（M）
- [ ] Task 4: pytest 基础套件（M）

### Checkpoint: Core Features

- [ ] `pytest -q` 全绿
- [ ] `cd web && npm run build` 通过
- [ ] 浏览器 Mock：登录 → 列表 → 下载得到文件；详情仍弹 JSON

### Phase 3: Polish

- [ ] Task 5: 文档与 data818 联调附录（S）

### Checkpoint: Complete

- [ ] `docs/spec.md` Success Criteria 中「下载 / 账号 / Mock 全流程 / 文档」可勾选（联调项有 token 再勾）
- [ ] README 命令与行为一致
- [ ] Ready for review

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| data818 `get_csv` 实为 JSON 而非文件流 | High | 适配器按 Content-Type / body 形状分支；`format=txt` 走 `get_valid_txt` |
| 业务错误 JSON 被当成 blob | Med | 前端：若 `content-type` 含 json 则解析 message 后 ElMessage |
| Task 4 文件数顶格（~5） | Low | 严格只加 tests + pytest 依赖 + README 一行；不顺手重构 |
| 无 DATA818_TOKEN | Low | 联调不进完成门禁；清单标明阻塞 |

## Open Questions

- [ ] 默认下载格式：`csv` 还是 `txt`？（Plan 默认 **csv**，可在批准时改口）
- [ ] xlsx 是否进本轮？（默认 **否**，Ask first）

## Out of Scope

- data-center-backend 第二适配器  
- 控制平面自建任务主数据  
- 与 data818 用户/余额打通  
- Playwright / E2E  

## Parallelization

| 可并行 | 必须串行 |
|--------|----------|
| Task 5 初稿文档 ↔ Task 4 后半 | Task 1 → 2 → 3 |
| — | Task 2 → Task 4（download 断言依赖 API） |
