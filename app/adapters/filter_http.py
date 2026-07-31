"""818 形 HTTP 下游共享实现（路径同构；鉴权由子类 _headers_for 决定）。"""
from __future__ import annotations

from typing import Any, BinaryIO
from urllib.parse import unquote

import httpx

from app.adapters.base import DownstreamAdapter, DownloadFormat, FilePayload
from app.utils.response import _Exception

_FORMAT_PATH = {
    'csv': '/api/filter/get_csv',
}

# 对齐 data818 GetDownloadPathByIdSchema.downloadType
_BUSINESS_DOWNLOAD_TYPES = frozenset({'csv', 'txt', 'xlsx', 'parquet', 'zip'})


class FilterHttpAdapter(DownstreamAdapter):
    """开放筛选 + 业务面 HTTP 适配器基类。"""

    adapter_label: str = 'filter_http'

    def __init__(self, *, base_url: str, timeout: float) -> None:
        self.base = base_url.rstrip('/')
        self.timeout = timeout

    def _headers_for(self, path: str) -> dict[str, str]:
        raise NotImplementedError

    @staticmethod
    def _bearer(token: str) -> str:
        t = token.strip()
        if not t.lower().startswith('bearer '):
            return f'Bearer {t}'
        return t

    def _tag(self, result: Any) -> Any:
        if isinstance(result, dict):
            return {**result, 'adapter': self.adapter_label}
        return result

    def _unwrap(self, payload: dict[str, Any], *, context: str) -> Any:
        if not isinstance(payload, dict):
            raise _Exception(502, f'{context}: invalid response')
        code = int(payload.get('code') or 0)
        success = payload.get('success')
        if success is False or code >= 400:
            raise _Exception(code or 502, payload.get('message') or f'{context} failed')
        return payload.get('result')

    def _response_json(self, resp: httpx.Response, *, context: str) -> Any:
        """下游偶发 SPA HTML / 空体时避免 JSONDecodeError 打成 500。"""
        try:
            payload = resp.json()
        except ValueError as exc:
            snippet = (resp.text or '')[:80].replace('\n', ' ')
            raise _Exception(
                502,
                f'{context}: non-JSON body (HTTP {resp.status_code}) {snippet}',
            ) from exc
        return self._unwrap(payload, context=context)

    def _get(self, path: str, params: dict | None = None) -> Any:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f'{self.base}{path}', headers=self._headers_for(path), params=params or {})
                resp.raise_for_status()
                return self._response_json(resp, context=path)
        except _Exception:
            raise
        except httpx.HTTPError as exc:
            raise _Exception(502, f'{self.adapter_label} GET {path}: {exc}') from exc

    def _post_json(self, path: str, body: dict) -> Any:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f'{self.base}{path}', headers=self._headers_for(path), json=body)
                resp.raise_for_status()
                return self._response_json(resp, context=path)
        except _Exception:
            raise
        except httpx.HTTPError as exc:
            raise _Exception(502, f'{self.adapter_label} POST {path}: {exc}') from exc

    def _post_multipart(self, path: str, data: dict, files: dict) -> Any:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f'{self.base}{path}',
                    headers=self._headers_for(path),
                    data=data,
                    files=files,
                )
                resp.raise_for_status()
                return self._response_json(resp, context=path)
        except _Exception:
            raise
        except httpx.HTTPError as exc:
            raise _Exception(502, f'{self.adapter_label} POST {path}: {exc}') from exc

    def list_tasks(
        self,
        *,
        page_no: int = 1,
        page_size: int = 20,
        task_type: str | None = None,
        task_no: str | None = None,
        country_code: str | None = None,
        task_status: int | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {'pageNo': page_no, 'pageSize': page_size}
        if task_type:
            params['taskType'] = task_type
        if task_no:
            params['taskNo'] = task_no
        if country_code:
            params['countryCode'] = country_code
        if task_status is not None:
            params['taskStatus'] = task_status
        result = self._get('/business/taskRecord/list', params)
        if isinstance(result, dict):
            return self._tag(result)
        return {
            'pageNo': page_no,
            'pageSize': page_size,
            'total': 0,
            'data': result or [],
            'adapter': self.adapter_label,
        }

    def create_task(
        self,
        *,
        filter_type: str,
        country_code: str,
        describe: str,
        filename: str,
        file_obj: BinaryIO,
    ) -> dict[str, Any]:
        result = self._post_multipart(
            '/api/filter/create_task',
            data={
                'filterType': filter_type,
                'countryCode': country_code,
                'describe': describe or 'control-plane',
            },
            files={'file': (filename or 'upload.txt', file_obj, 'text/plain')},
        )
        if isinstance(result, dict):
            return self._tag(result)
        return {'taskNo': result, 'adapter': self.adapter_label}

    def _lookup_admin_task(self, key: str) -> dict[str, Any] | None:
        """管理端 task_list 按 taskNo / orderId / partitionId 精确回落（跨账号可见）。"""
        needle = (key or '').strip()
        if not needle:
            return None
        for field in ('taskNo', 'orderId', 'partitionId'):
            try:
                result = self._post_json(
                    '/admin/third_management/task_list',
                    {'pageNo': 1, 'pageSize': 5, field: needle},
                )
            except _Exception:
                continue
            rows: list[Any]
            if isinstance(result, dict):
                rows = result.get('data') or []
            elif isinstance(result, list):
                rows = result
            else:
                rows = []
            for row in rows:
                if not isinstance(row, dict):
                    continue
                if needle in {
                    str(row.get('taskNo') or ''),
                    str(row.get('orderId') or ''),
                    str(row.get('partitionId') or ''),
                }:
                    return row
        return None

    def query_task(self, task_no: str) -> dict[str, Any]:
        # /api/filter/task_query 仅 agent 本账号；订单页常点进他人单 → 管理端回退。
        try:
            result = self._get('/api/filter/task_query', {'taskNo': task_no})
            if isinstance(result, dict):
                return self._tag(result)
            return {'result': result, 'adapter': self.adapter_label}
        except _Exception as exc:
            row = self._lookup_admin_task(task_no)
            if row:
                return self._tag(row)
            raise exc

    def _filename_from_disposition(self, header: str | None, fallback: str) -> str:
        if not header:
            return fallback
        starred: str | None = None
        plain: str | None = None
        for part in header.split(';'):
            part = part.strip()
            lower = part.lower()
            if lower.startswith('filename*='):
                value = part.split('=', 1)[1].strip().strip('"')
                if "''" in value:
                    value = value.split("''", 1)[1]
                starred = unquote(value) or None
            elif lower.startswith('filename='):
                plain = part.split('=', 1)[1].strip().strip('"') or None
        return starred or plain or fallback

    def _resolve_order_id(self, task_no: str) -> str:
        """开放筛选/业务下载的 id = order_id；管理端另有 partitionId 勿混淆。"""
        needle = (task_no or '').strip()
        if not needle:
            return needle
        row = self._lookup_admin_task(needle)
        if row:
            oid = str(row.get('orderId') or row.get('order_id') or '').strip()
            if oid:
                return oid
        return needle

    def _oss_public_url(self, object_path: str) -> str:
        from config import settings

        path = (object_path or '').strip()
        if path.startswith('http://') or path.startswith('https://'):
            return path
        base = (settings.DATA818_OSS_PUBLIC_BASE or '').rstrip('/')
        if not base:
            raise _Exception(502, '未配置 DATA818_OSS_PUBLIC_BASE，无法拉取 OSS 文件')
        return f'{base}/{path.lstrip("/")}'

    def _download_via_business(self, order_id: str, fmt: str) -> FilePayload:
        """POST /business/taskRecord/getDownloadPathById → OSS path → 拉文件。"""
        raw = self._post_json(
            '/business/taskRecord/getDownloadPathById',
            {'id': order_id, 'downloadType': fmt},
        )
        object_path = ''
        if isinstance(raw, str):
            object_path = raw.strip()
        elif isinstance(raw, dict):
            object_path = str(
                raw.get('object_path')
                or raw.get('objectPath')
                or raw.get('url')
                or raw.get('path')
                or ''
            ).strip()
        if not object_path:
            raise _Exception(201, '暂无可下载数据')
        url = self._oss_public_url(object_path)
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                resp = client.get(url)
                resp.raise_for_status()
                name = object_path.replace('\\', '/').rsplit('/', 1)[-1] or f'{order_id}.{fmt}'
                filename = self._filename_from_disposition(
                    resp.headers.get('content-disposition'),
                    name,
                )
                return FilePayload(
                    content=resp.content,
                    content_type=resp.headers.get('content-type') or 'application/octet-stream',
                    filename=filename,
                )
        except httpx.HTTPError as exc:
            raise _Exception(502, f'拉取下载文件失败: {exc}') from exc

    def _download_via_filter_csv(self, order_id: str) -> FilePayload:
        """本账号 agent：GET /api/filter/get_csv（常 JSON + resultUrl）。"""
        path = _FORMAT_PATH['csv']
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                resp = client.get(
                    f'{self.base}{path}',
                    headers=self._headers_for(path),
                    params={'taskNo': order_id},
                )
                resp.raise_for_status()
                content_type = (resp.headers.get('content-type') or '').lower()
                if 'application/json' in content_type:
                    payload = resp.json()
                    if isinstance(payload, dict) and (
                        payload.get('success') is False
                        or int(payload.get('code') or 0) >= 400
                        or int(payload.get('code') or 0) == 201
                    ):
                        raise _Exception(
                            int(payload.get('code') or 502),
                            payload.get('message') or f'{path} failed',
                        )
                    result = payload.get('result') if isinstance(payload, dict) else None
                    url = None
                    if isinstance(result, dict):
                        url = result.get('resultUrl') or result.get('url')
                    elif isinstance(result, str) and result.startswith('http'):
                        url = result
                    if not url:
                        raise _Exception(502, f'{path}: 无可用下载地址')
                    file_resp = client.get(url)
                    file_resp.raise_for_status()
                    filename = self._filename_from_disposition(
                        file_resp.headers.get('content-disposition'),
                        f'{order_id}.csv',
                    )
                    return FilePayload(
                        content=file_resp.content,
                        content_type=file_resp.headers.get('content-type')
                        or 'application/octet-stream',
                        filename=filename,
                    )
                filename = self._filename_from_disposition(
                    resp.headers.get('content-disposition'),
                    f'{order_id}.csv',
                )
                return FilePayload(
                    content=resp.content,
                    content_type=resp.headers.get('content-type') or 'application/octet-stream',
                    filename=filename,
                )
        except _Exception:
            raise
        except httpx.HTTPError as exc:
            raise _Exception(502, f'{self.adapter_label} GET {path}: {exc}') from exc

    def get_download(self, task_no: str, *, fmt: DownloadFormat = 'csv') -> FilePayload:
        if fmt not in _BUSINESS_DOWNLOAD_TYPES:
            raise _Exception(422, f'不支持的 format: {fmt}')
        order_id = self._resolve_order_id(task_no)
        # 运营台主路径：业务 getDownloadPathById（登录 JWT，可跨账号）
        try:
            return self._download_via_business(order_id, fmt)
        except _Exception as biz_exc:
            if fmt == 'csv':
                try:
                    return self._download_via_filter_csv(order_id)
                except _Exception:
                    raise biz_exc from None
            raise

    def list_filter_types(self) -> list[dict[str, Any]]:
        result = self._get('/api/filter/type/get')
        return result or []

    def list_countries(self) -> list[dict[str, Any]]:
        result = self._get('/api/filter/country_info/get')
        return result or []

    def get_balance(self) -> dict[str, Any]:
        result = self._get('/api/filter/get_balance')
        if isinstance(result, dict):
            return self._tag(result)
        return {'balance': result, 'adapter': self.adapter_label}

    def close_task(self, task_no: str) -> dict[str, Any]:
        order_id = self._resolve_order_id(task_no)
        self._post_json('/admin/third_management/task/close', {'orderId': order_id})
        return {'taskNo': order_id, 'status': -1, 'adapter': self.adapter_label}

    def refund_task(self, task_no: str) -> dict[str, Any]:
        order_id = self._resolve_order_id(task_no)
        self._post_json('/admin/third_management/task/refund', {'orderId': order_id})
        return {'taskNo': order_id, 'status': -1, 'adapter': self.adapter_label}

    def retry_task(self, task_no: str) -> dict[str, Any]:
        order_id: Any = int(task_no) if task_no.isdigit() else task_no
        self._post_json('/admin/super/query/retry', {'orderId': order_id})
        return {'taskNo': task_no, 'status': 2, 'adapter': self.adapter_label}

    def statistics(self, *, task_type: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if task_type:
            params['taskType'] = task_type
        result = self._get('/business/statisticsForTable', params)
        if isinstance(result, dict) and 'series' in result:
            return self._tag(result)
        if isinstance(result, list):
            series = []
            for row in result:
                if not isinstance(row, dict):
                    continue
                items = row.get('tasks') or []
                total = 0
                norm_items = []
                for it in items:
                    if not isinstance(it, dict):
                        continue
                    n = int(it.get('taskNumber') or 0)
                    total += n
                    norm_items.append(
                        {
                            'taskType': it.get('taskType'),
                            'taskNumber': n,
                            'taskName': it.get('description') or it.get('taskType'),
                        }
                    )
                series.append(
                    {
                        'date': row.get('createTime') or '',
                        'items': norm_items,
                        'total': total,
                    }
                )
            return {'days': 30, 'series': series, 'adapter': self.adapter_label}
        return {'raw': result, 'adapter': self.adapter_label}

    def list_orders(
        self,
        *,
        page_no: int = 1,
        page_size: int = 20,
        order_id: str | None = None,
        task_type: str | None = None,
        description: str | None = None,
        username: str | None = None,
        consume_type: int | None = None,
        create_time_begin: str | None = None,
        create_time_end: str | None = None,
    ) -> dict[str, Any]:
        # 运营台要对齐 818 管理端可见范围，不用 /order/list（仅 Token 本人）。
        # consumeType 管理端无此筛；个人流水接口才有，此处忽略以免 silent wrong filter。
        _ = consume_type
        body: dict[str, Any] = {'pageNo': page_no, 'pageSize': page_size}
        if order_id:
            body['orderId'] = order_id
        if task_type:
            body['taskType'] = task_type
        if description:
            body['description'] = description
        if username:
            body['username'] = username
        if create_time_begin:
            body['startDate'] = create_time_begin
        if create_time_end:
            body['endDate'] = create_time_end
        result = self._post_json('/admin/third_management/task_list', body)
        if isinstance(result, dict):
            return self._tag(result)
        return {
            'pageNo': page_no,
            'pageSize': page_size,
            'total': 0,
            'data': result or [],
            'adapter': self.adapter_label,
        }

    def third_balances(self) -> list[dict[str, Any]]:
        """下游三方余额偶发 500；失败软降级为空列表。"""
        try:
            result = self._get('/admin/third_management/get_third_balance')
        except _Exception:
            return []
        rows = result if isinstance(result, list) else []
        out: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            out.append(
                {
                    'thirdSourceName': row.get('thirdSourceName')
                    or row.get('third_source_name')
                    or row.get('name')
                    or '',
                    'balance': row.get('balance'),
                }
            )
        return out

    def list_bills(
        self,
        *,
        page_no: int = 1,
        page_size: int = 20,
        bill_id: str | None = None,
        order_id: str | None = None,
        ledger_type: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {'pageNo': page_no, 'pageSize': page_size}
        if bill_id:
            body['billId'] = bill_id
        if order_id:
            body['orderId'] = order_id
        if ledger_type:
            body['ledgerType'] = ledger_type
        result = self._post_json('/admin/bill/list', body)
        if isinstance(result, dict):
            return self._tag(result)
        return {
            'pageNo': page_no,
            'pageSize': page_size,
            'total': 0,
            'data': result or [],
            'adapter': self.adapter_label,
        }

    def list_notices(self) -> list[dict[str, Any]]:
        result = self._get('/sys_msg/list')
        return result if isinstance(result, list) else []

    def get_notice(self, notice_id: str) -> dict[str, Any]:
        result = self._get('/sys_msg/detail', {'id': notice_id})
        if isinstance(result, dict):
            return result
        raise _Exception(502, '公告详情无效')

    def list_products(self) -> list[dict[str, Any]]:
        raw = self._get('/product/list')
        return flatten_product_tree(raw)

    def list_order_task_types(self) -> list[dict[str, Any]]:
        result = self._get('/order/taskTypeList')
        rows = result if isinstance(result, list) else []
        out: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            out.append(
                {
                    'taskType': row.get('taskType') or row.get('task_type') or '',
                    'description': row.get('description') or row.get('taskType') or '',
                }
            )
        return out

    def list_ledger_types(self) -> list[dict[str, Any]]:
        return [
            {'ledgerType': 'ORDER_PAY', 'description': '订单支付'},
            {'ledgerType': 'ORDER_REFUND', 'description': '订单退款'},
            {'ledgerType': 'RECHARGE', 'description': '充值'},
            {'ledgerType': 'ADJUST', 'description': '管理员调整'},
        ]

    def export_remaining(self, task_no: str) -> FilePayload | dict[str, Any]:
        order_id = self._resolve_order_id(task_no)
        path = self._post_json('/business/taskRecord/exportRemainingPhone', {'id': order_id})
        object_path = ''
        url = None
        if isinstance(path, str):
            object_path = path
            url = path if path.startswith('http') else None
        elif isinstance(path, dict):
            object_path = str(
                path.get('object_path') or path.get('objectPath') or path.get('url') or ''
            )
            candidate = path.get('url') or path.get('object_path') or path.get('objectPath')
            if isinstance(candidate, str) and candidate.startswith('http'):
                url = candidate
        if not url:
            if not object_path:
                raise _Exception(201, '无可导出剩余号')
            # 相对 OSS path：尝试公网拉取；失败则返回 path 供前端复制
            try:
                url = self._oss_public_url(object_path)
            except _Exception:
                return {
                    'objectPath': object_path,
                    'downloadable': False,
                    'adapter': self.adapter_label,
                }
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                resp = client.get(url)
                resp.raise_for_status()
                filename = self._filename_from_disposition(
                    resp.headers.get('content-disposition'),
                    f'{order_id}-remaining.txt',
                )
                return FilePayload(
                    content=resp.content,
                    content_type=resp.headers.get('content-type') or 'text/plain; charset=utf-8',
                    filename=filename,
                )
        except httpx.HTTPError:
            return {
                'objectPath': object_path or url,
                'downloadable': False,
                'adapter': self.adapter_label,
            }


def flatten_product_tree(raw: Any) -> list[dict[str, Any]]:
    """product/list 树 → 扁平价目行。"""
    rows: list[dict[str, Any]] = []
    if not isinstance(raw, dict):
        return rows
    for app_type, biz_list in raw.items():
        if not isinstance(biz_list, list):
            continue
        for biz in biz_list:
            if not isinstance(biz, dict):
                continue
            biz_name = biz.get('business_type') or biz.get('name') or ''
            for p in biz.get('products') or []:
                if not isinstance(p, dict):
                    continue
                rows.append(
                    {
                        'taskType': p.get('task_type') or p.get('taskType') or '',
                        'name': p.get('name') or '',
                        'price': p.get('price'),
                        'applicationType': app_type,
                        'businessType': biz_name,
                        'minCount': p.get('min_count') if p.get('min_count') is not None else p.get('minCount'),
                        'maxCount': p.get('max_count') if p.get('max_count') is not None else p.get('maxCount'),
                        'thirdSource': p.get('third_source') or p.get('thirdSource') or '',
                        'description': p.get('description') or '',
                    }
                )
    return rows
