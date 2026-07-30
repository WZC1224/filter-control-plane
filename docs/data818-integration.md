# data818 联调检查清单

> 无有效 `DATA818_TOKEN` 时本清单为**阻塞项**；Mock 模式不影响本地验收。

## 环境

- [ ] `.env` 中填写：
  - `DATA818_BASE_URL`（无尾斜杠，例 `https://xxx`）
  - `DATA818_TOKEN`（Bearer 可带可不带前缀；服务会自动补 `Bearer `）
- [ ] 重启 `python main.py` 后 `GET /meta/health` 的 `adapter` 为 `data818`

## 所需下游权限（ApiPath + 角色）

Token 对应用户需能访问：

| 控制平面 | data818 |
|----------|---------|
| 列表 | `GET /business/taskRecord/list` |
| 建任务 | `POST /api/filter/create_task` |
| 详情 | `GET /api/filter/task_query` |
| 下载 csv | `GET /api/filter/get_csv`（常返回 JSON + `resultUrl`，控制平面再拉文件） |
| 下载 txt/xlsx/invalid | `get_valid_txt` / `get_xlsx` / `get_invalid_txt` |
| 元数据 | `GET /api/filter/type/get`、`GET /api/filter/country_info/get`、`GET /api/filter/get_balance` |
| 统计 | `GET /business/statisticsForTable` |
| 关单/退款/重试 | admin/super 路径（见 decisions） |
| 订单 | `GET /order/list`、`GET /order/taskTypeList` |
| 账单 | `POST /admin/bill/list` |
| 公告 | `GET /sys_msg/list`、`GET /sys_msg/detail` |
| 价目 | `GET /product/list` |
| 剩余号 | `POST /business/taskRecord/exportRemainingPhone`（常返 OSS `object_path`，控制台可复制） |
| 三方余额 | `GET /admin/third_management/get_third_balance` |

## 冒烟步骤

- [ ] 登录控制平面（独立账号）
- [ ] 筛选类型 / 国家下拉有数据
- [ ] 任务列表有该服务账号可见任务
- [ ] 对已完成任务点下载，浏览器得到文件
- [ ] 对未完成任务点下载，看到业务错误提示（非空白文件）
- [ ] 价目页有扁平产品行；订单类型下拉有值
- [ ] 公告列表可进详情
- [ ] 完成任务「导出剩余号」：Mock 得文件；真下游多为 OSS 路径弹窗可复制

## 常见错误

| 现象 | 可能原因 |
|------|----------|
| `adapter` 仍为 mock | URL/Token 未配齐或未重启 |
| 401 / 权限 | Token 过期或角色无上述 path |
| 201 暂无数据 | 任务未完成或无有效量 |
| 502 无可用下载地址 | `get_csv` 未返回 `resultUrl`；可改 `format=txt` 试 `get_valid_txt` |
| 剩余号仅路径无可下载文件 | 下游只给 OSS `object_path`（预期）；去 OSS/818 侧取 |
| 建任务失败 | 余额不足 / 国家不支持 / 文件校验失败（见下游 message） |
| 关单/退款/三方余额失败 | Token 缺 admin ACL |
