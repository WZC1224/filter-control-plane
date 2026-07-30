# API Contract: filter-control-plane

> 合同优先。实现跟本文；改破坏性字段先 Ask。  
> 对齐：data818 前端习惯（HTTP 200 + body.code）· 控制平面自有命名（camelCase）。

## 1. Envelope（JSON 端点）

除 **下载成功** 外，一律：

```json
{
  "code": 200,
  "success": true,
  "message": "ok",
  "result": {},
  "timestamp": 1785383655576
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | int | 业务码。成功 `200`；失败用下表 |
| `success` | bool | 与 `code` 一致：成功 true |
| `message` | string | 人读 |
| `result` | any \| null | 载荷 |
| `timestamp` | int | ms |

**HTTP：** JSON 响应统一 **HTTP 200**（含失败）。鉴权失败仍 HTTP 200 + `code=401`。  
**例外：** `GET /tasks/:taskNo/download` **成功** = 文件流（见 §4）。失败仍走 Envelope。

### 业务码

| code | 含义 |
|------|------|
| 200 | 成功 |
| 201 | 业务暂不可用（如下载无数据） |
| 400 | 通用客户端错误 |
| 401 | 未登录 / token 无效 |
| 422 | 校验失败 |
| 502 | 下游失败 / 不可下载的 JSON CT |

机器可读优先看 `code`，勿依赖 `message` 文案（Hyrum：文案可变）。

## 2. 鉴权

- Header：`Authorization: Bearer <token>`
- 登录拿 token：`POST /auth/login`
- 公开：`POST /auth/login`、`GET /meta/health`
- 其余 JSON/下载：需 token

## 3. 资源

### `POST /auth/login`

**In**

```json
{ "username": "string", "password": "string" }
```

**Out `result`**

```json
{ "token": "string", "username": "string" }
```

### `GET /auth/me`

**Out `result`:** `{ "username": "string" }`

### `GET /tasks`

Query（camelCase）：

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| pageNo | int ≥1 | 1 | |
| pageSize | int 1–100 | 20 | |
| taskType | string? | | |
| taskNo | string? | | |
| countryCode | string? | | |
| taskStatus | int? | | 0 排队 / 1 完成 / 2 进行中 |

**Out `result`**

```json
{
  "pageNo": 1,
  "pageSize": 20,
  "total": 42,
  "data": [ /* Task */ ],
  "adapter": "mock" | "data818"
}
```

**Task（控制平面稳定形，camelCase）**

```json
{
  "taskNo": "string",
  "taskName": "string",
  "taskType": "string",
  "country": "string",
  "status": 0,
  "progress": 0,
  "effectiveQuantity": 0,
  "count": 0,
  "createDate": "string",
  "description": "string"
}
```

下游 snake_case 由 Service **归一**后再返回；客户端只依赖上表。

### `POST /tasks`（multipart）

| 字段 | 必填 | 说明 |
|------|------|------|
| file | 是 | `.txt` |
| filterType | 是 | |
| countryCode | 是 | |
| describe | 否 | |

**Out `result`:** `{ "taskNo": "string", "adapter"?: "mock"|"data818" }`（可含下游额外字段，客户端以 `taskNo` 为准）

### `GET /tasks/:taskNo`

**Out `result`:** Task 形（同列表项）或下游详情对象（至少含可识别 `taskNo`/`status`）。

### `GET /tasks/:taskNo/download`

Query：`format=csv|txt|xlsx|invalid`（默认 `csv`；非法 → 422）。首尾空白忽略。

**成功：** binary body + `Content-Disposition: attachment` + 非 JSON `Content-Type`。  
**失败：** Envelope（如 201 / 502）。

### `GET /tasks/:taskNo/export-remaining`

**成功（文件流）：** 同下载。  
**成功（仅 OSS path）：** Envelope，`result = { objectPath, downloadable: false }`。  
**失败：** Envelope（如 201）。

### `GET /meta/products`

扁平价目行：`[{ taskType, name, price, applicationType, businessType, minCount, maxCount, thirdSource, description }]`。

### `GET /meta/order-task-types`

`[{ taskType, description }]`。

### `GET /notices` · `GET /notices/:id`

Notice 形：`{ id, title, contentMd, bizType, level, publishStatus, createDate, expireDate }`。

### `GET /meta/health`（公开）

```json
{
  "service": "filter-control-plane",
  "version": "0.1.0",
  "adapter": "mock"|"data818",
  "mock": true,
  "tokenKind": "none"|"agent"|"login"|"unknown",
  "time": "2026-07-30T06:00:00Z"
}
```

`version` 来自 `config.APP_VERSION`；`time` 为 UTC ISO8601。`tokenKind=agent` 表示下游为无过期 agent_token，业务列表/订单会 `invalid token`。

### `GET /meta/filter-types` · `GET /meta/countries`

透传下游元数据；形状随适配器，前端容错双命名。稳定化列为远期（加法，不拆现字段）。

## 4. 边界校验

| 入口 | 校验 |
|------|------|
| JSON body | Pydantic Schema |
| Query 列表 | `TaskListSchema` |
| multipart 建任务 | `filterType`/`countryCode` 非空 + 文件后缀 |
| format | strip + lower ∈ {csv,txt} |
| 下载 mime | 禁止成功路径 `application/json` |

下游响应：适配器解包/拉文件；不可信，失败转 `_Exception`。

## 5. 兼容与演进

- **加法优先：** 新可选字段 OK；勿改已有字段类型/改名。
- **One-Version：** 不并行 `/v2`；破坏性变更先 Ask + 迁移窗。
- **不做：** 动词 URL、同端点多响应形（仅下载例外已文档化）。

## 6. 前端消费约定

- JSON：`success === false` → 错误；`code === 401` → 登出。
- 下载：`responseType: 'blob'`；若 CT 含 `json` → 当 Envelope 错。
