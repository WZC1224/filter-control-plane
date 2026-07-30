# Implementation Plan: Phase 2 — 独占 data-center 下游

> Spec：`docs/spec.md`  
> 状态：**执行中** · 2026-07-30  
> 不做：双下游并行、任务主库、账号映射、E2E、改下游源码

## Overview

在控制平面增加 `DataCenterAdapter`（路径同构、鉴权为 `X-Api-Key` + JWT），用 `DOWNSTREAM` 在 `mock | data818 | data_center` 三选一（独占）。

## Architecture

- 共享基类 `app/adapters/filter_http.py`；子类只覆写 `_headers_for`（及公告降级）。
- `get_adapter()` 按 `settings.adapter_name` 选一；显式下游缺凭证抛错。

## Tasks

1. 配置 `DOWNSTREAM` + `DATA_CENTER_*` + 选择逻辑
2. `FilterHttpAdapter` + `DataCenterAdapter` + Data818 迁入
3. health / SystemView / api-contract
4. pytest + 联调清单 + smoke 脚本
5. 文档同步

## Out of Scope

- UI 切换双源、并行路由、完整 RBAC
