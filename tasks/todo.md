# Todo: Phase 2 — data-center 独占适配器

> Plan：`tasks/plan.md` · Spec：`docs/spec.md`

## Task 1: 配置与选择器

- [x] `DOWNSTREAM` + `DATA_CENTER_*` in `config.py` / `.env.example`
- [x] `adapter_name` auto / explicit；缺凭证 RuntimeError
- [x] `get_adapter()` 三选一

## Task 2: 共享 HTTP + DataCenter

- [x] `app/adapters/filter_http.py`
- [x] `Data818Adapter` 薄封装
- [x] `DataCenterAdapter`（X-Api-Key；公告软降级）

## Task 3: Meta / UI / 契约

- [x] `/meta/health` 含 `data_center` + `hasApiKey`
- [x] SystemView / AppLayout 认三值
- [x] api-contract / types

## Task 4: 测试与联调文档

- [x] `tests/test_data_center_adapter.py`
- [x] 回归 `pytest -q`
- [x] `docs/data-center-integration.md`
- [x] `scripts/smoke_phase2_data_center.py`

## Checkpoint

- [x] Mock 主路径绿
- [x] DataCenter 单测：Key/JWT 分流 + 公告空
- [ ] 真联调（有凭证时人工勾 `data-center-integration.md`）
