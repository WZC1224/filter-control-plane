# 部署手册（单机 · 一人运维）

> 目标：把控制台跑在一台机器上，可回滚、可探活。  
> 不做：Docker/K8s、多副本、蓝绿自动化（需要时另开）。

## 假设

- 一台 Windows 或 Linux 主机
- Python 3.11+ · Node 20+（仅构建前端）
- 同进程托管 API + `web/dist`（默认端口 `5100`）
- 下游 `data818` 或 `data_center` 凭证已备好（或先 Mock 演示）

## 发布步骤

```bash
cd filter-control-plane
python -m venv .venv
# Windows: .\.venv\Scripts\activate
# Linux:   source .venv/bin/activate
pip install -r requirements.txt

cd web && npm ci && npm run build && cd ..

copy .env.example .env   # 或 cp
# 编辑 .env：见下方「生产必填」

# 冒烟
pytest -q
curl -s http://127.0.0.1:5100/meta/health   # 启动后

# 启动（FLASK_ENV=production 时走 waitress）
python main.py
```

探活成功形如：`success: true`，`adapter` 为 `data818` / `data_center` / `mock`。

## 生产必填（`.env`）

| 变量 | 要求 |
|------|------|
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | 强随机，**禁止** example 默认值 |
| `JWT_SECRET` | 强随机，与 SECRET 不同 |
| `ADMIN_PASSWORD` | 强密码，**禁止** `admin123` |
| `DATABASE_URL` | 例 `sqlite:////data/fcp.db`（绝对路径更稳） |
| `DOWNSTREAM` | `data818` 或 `data_center`（勿生产裸 `mock` 对真实用户） |
| 下游凭证 | data818 双 Token / data_center 三件套 |

可选：`HOST` `PORT` `CORS_ORIGINS` `APP_VERSION`。

弱密钥 / 弱管理员密码 → **进程直接拒绝启动**。

## 前置检查清单

- [ ] `pytest -q` 绿
- [ ] `cd web && npm run build` 绿，`web/dist` 存在
- [ ] `.env` 生产必填已填；`.env` **未**进 git
- [ ] `GET /meta/health` adapter 符合预期
- [ ] 登录 admin → 开一个 `operator` 试用账号（见 [`pilot.md`](pilot.md)）
- [ ] 反向代理（若有）把 HTTPS 转到 `:5100`；静态也走 Flask 即可
- [ ] 备份 `fcp.db`（或对应数据库文件）

## 回滚

1. 停进程（Ctrl+C / 服务管理器停掉）
2. 检出上一 git tag/commit：`git checkout <good-sha>`
3. 恢复该版本对应的 `web/dist`（重新 `npm run build` 或还原备份目录）
4. 若 DB 迁移有破坏性变更：恢复发布前 `fcp.db` 备份
5. 启动：`python main.py`
6. 再打 `/meta/health` + 登录冒烟

建议每次发布前：`copy fcp.db fcp.db.bak-YYYYMMDD`

## 运维提示

- 开发：`FLASK_ENV=development` → Flask debug（**勿对公网**）
- 生产：waitress · 无自动重载
- SPA 路由：未知前端路径回 `index.html`；`/auth` `/tasks` 等 API 前缀不吞
- 安全头：`X-Content-Type-Options` `X-Frame-Options` `Referrer-Policy`
- 试用通过后再扩大账号（[`pilot.md`](pilot.md)）

## 明确不做（本手册）

多机集群 · 自动证书 · 集中日志 SaaS · CI 自动发布。需要时单开任务。
