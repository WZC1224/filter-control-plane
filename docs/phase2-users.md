# Phase 2：控制平面多账号 / 角色

> 状态：**已实施** · 2026-07-30  
> 依据：用户选定「多账号/角色」（spec Ask first 已授权）  
> 不做：与 data818 账号打通、完整菜单级 RBAC、审计日志

## Objective

内部多人共用控制台：管理员可开账号；运营账号可走主路径，不可管用户/不可做敏感运维操作。

## Roles

| 角色 | 能力 |
|------|------|
| `admin` | 全部页面；用户 CRUD；关单/退款/重试；系统页 |
| `operator` | 概览/任务/订单/价目/公告/账号（改自己密码）；**不可**用户管理、关单/退款/重试、系统 |

下游仍共用配置的 `DATA818_*` 服务 Token（与控制平面角色无关）。

## Success Criteria

- [x] `User` 有 `role`（`admin`\|`operator`）与 `is_active`
- [x] 种子 `ADMIN_*` 用户为 `admin`；停用账号无法登录
- [x] `GET/POST /users`、`PATCH /users/<id>` 仅 admin；不能停用/降级最后一个 admin
- [x] `POST /tasks/<id>/close|refund|retry` 仅 admin
- [x] 登录与 `/auth/me` 返回 `role`；前端按角色藏菜单与按钮（每次导航强制 `/auth/me` 刷新 role）
- [x] `GET /meta/third-balances` 仅 admin（与系统页一致）
- [x] `pytest -q` 绿；`npm run build` 绿

## API

| 方法 | 路径 | 角色 | 说明 |
|------|------|------|------|
| GET | `/users` | admin | 用户列表 |
| POST | `/users` | admin | `{username,password,role}` |
| PATCH | `/users/<id>` | admin | `{role?,isActive?,password?}` 重置密码可选 |
| GET | `/auth/me` | 登录 | `{username,role,isActive}` |
