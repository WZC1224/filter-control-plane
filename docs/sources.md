# Source citations（框架写法核对）

> 对照依赖锁定版本。非官方博客不作主源。

## STACK DETECTED

| 包 | 版本（锁文件） |
|----|----------------|
| Flask | 3.0.3 |
| httpx | 0.28.1 |
| Vue | ^3.4.21 |
| Pinia | ^2.1.7 |
| pinia-plugin-persistedstate | ^3.2.3 |
| axios | ^1.6.8 |
| Vite | ^5.1.6 |
| Element Plus | ^2.6.1 |

## 已核对照

| 本仓库写法 | 官方依据 | 结论 |
|------------|----------|------|
| `<script setup lang="ts">` | https://vuejs.org/api/sfc-script-setup.html — “recommended syntax if you are using both SFCs and Composition API” | 对齐 |
| Blueprint 分模块 | https://flask.palletsprojects.com/en/stable/api/#flask.Blueprint | 对齐 |
| 下载：`send_file(BytesIO, as_attachment=True, download_name=...)` | Flask 3.0 helpers：https://github.com/pallets/flask/blob/3.0.0/src/flask/helpers.py | **已对齐**（2026-07-30） |
| httpx `r.content` 二进制 | https://www.python-httpx.org/quickstart/#binary-response-content | 对齐 |
| 大文件：`httpx.stream` / `iter_bytes` | 同上页 Streaming Responses | 现用整包 `content`；大文件 Ask first 再改流式 |
| axios `responseType: 'blob'` | https://axios-http.com/docs/req_config （`responseType`） | 对齐 |
| Pinia setup store | https://pinia.vuejs.org/core-concepts/ | 对齐 |
| Token 持久化用 `pinia-plugin-persistedstate` | Pinia 官文示意 `$subscribe`+localStorage：https://pinia.vuejs.org/core-concepts/state.html#subscribing-to-the-state | 插件非 Pinia 核心；持久化意图官方认可，插件属社区扩展 |

## CONFLICT / 可选改进

1. ~~下载 API 手写 Response~~ — 已改为 `send_file`。
2. **Pinia persist：** 核心文档无内置 persist；插件文档站点本次 fetch 失败（500）。插件 API **UNVERIFIED 于本次抓取** — 以已安装 `^3.2.3` 与现有 `persist: { key, paths }` 实测为准。
