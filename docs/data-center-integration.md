# data-center-backend 联调检查清单

> 与 data818 **独占**切换（`DOWNSTREAM`）。无有效 Key/JWT 时本清单为阻塞项；Mock 不影响本地验收。

## 环境

- [ ] `.env` 填写（从 `.env.example` 复制，**不要**把密钥写进 example）：
  - `DOWNSTREAM=data_center`（或 `auto` 且仅配齐 data-center 三件套）
  - `DATA_CENTER_BASE_URL`：API 根，例 `https://filter.168studio.com` 或 `http://host:9999`
  - `DATA_CENTER_API_KEY`：开放筛选 `X-Api-Key`
  - `DATA_CENTER_TOKEN`：登录 JWT（`Authorization`）
- [ ] 重启后 `GET /meta/health` 的 `adapter` 为 `data_center`，`hasApiKey=true`

### 鉴权对照

| 前缀 | Header | env |
|------|--------|-----|
| `/api/filter*` | `X-Api-Key` | `DATA_CENTER_API_KEY` |
| 业务面（列表/订单/账单/关退等） | `Authorization: Bearer …` | `DATA_CENTER_TOKEN` |

与 data818 差异：818 用 agent JWT；data-center 用 API Key。**无** `/sys_msg/*` 公告。

## 冒烟

```bash
python -m scripts.smoke_phase2_data_center
python -m scripts.smoke_phase2_data_center --create --yes   # 扣费建单，慎用
```

- [ ] 余额 / 筛选类型 / 国家 / 任务列表
- [ ] 建任务路径可读错误（如 min_count）
- [ ] 已完成任务代理下载
- [ ] 公告列表为空（预期）；详情返回可读 404

## 常见错误

| 现象 | 可能原因 |
|------|----------|
| `adapter` 仍为 data818 | `DOWNSTREAM` 未切，或 DATA818 仍配齐且 auto 被显式盖住 |
| `RuntimeError` 缺凭证 | 显式 `DOWNSTREAM=data_center` 但三件套不全 |
| filter 401 | API Key 无效 / Redis `api_keys:active` 未激活 |
| 列表 401/403 | JWT 过期或无 ApiPath ACL |
| 公告 404 | 预期：data-center 无 sys_msg |
