from __future__ import annotations

from typing import Any, BinaryIO
from urllib.parse import unquote

import httpx

from app.adapters.base import DownstreamAdapter, DownloadFormat, FilePayload
from app.utils.response import _Exception
from config import settings

_FORMAT_PATH = {
    'csv': '/api/filter/get_csv',
    'txt': '/api/filter/get_valid_txt',
    'xlsx': '/api/filter/get_xlsx',
    'invalid': '/api/filter/get_invalid_txt',
}


class Data818Adapter(DownstreamAdapter):
    """通过 HTTP 对接 data818 开放筛选 / 业务任务接口。"""

    def __init__(self) -> None:
        if not settings.DATA818_BASE_URL or not settings.DATA818_TOKEN:
            raise RuntimeError('DATA818_BASE_URL / DATA818_TOKEN required')
        self.base = settings.DATA818_BASE_URL
        self.timeout = settings.DATA818_TIMEOUT
        token = settings.DATA818_TOKEN
        if not token.lower().startswith('bearer '):
            token = f'Bearer {token}'
        self.headers = {'Authorization': token}

    def _unwrap(self, payload: dict[str, Any], *, context: str) -> Any:
        if not isinstance(payload, dict):
            raise _Exception(502, f'{context}: invalid response')
        code = int(payload.get('code') or 0)
        success = payload.get('success')
        if success is False or code >= 400:
            raise _Exception(code or 502, payload.get('message') or f'{context} failed')
        return payload.get('result')

    def _get(self, path: str, params: dict | None = None) -> Any:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f'{self.base}{path}', headers=self.headers, params=params or {})
                resp.raise_for_status()
                return self._unwrap(resp.json(), context=path)
        except httpx.HTTPError as exc:
            raise _Exception(502, f'data818 GET {path}: {exc}') from exc

    def _post_json(self, path: str, body: dict) -> Any:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f'{self.base}{path}', headers=self.headers, json=body)
                resp.raise_for_status()
                return self._unwrap(resp.json(), context=path)
        except httpx.HTTPError as exc:
            raise _Exception(502, f'data818 POST {path}: {exc}') from exc

    def _post_multipart(self, path: str, data: dict, files: dict) -> Any:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f'{self.base}{path}',
                    headers=self.headers,
                    data=data,
                    files=files,
                )
                resp.raise_for_status()
                return self._unwrap(resp.json(), context=path)
        except httpx.HTTPError as exc:
            raise _Exception(502, f'data818 POST {path}: {exc}') from exc

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
            result = {**result, 'adapter': 'data818'}
            return result
        return {'pageNo': page_no, 'pageSize': page_size, 'total': 0, 'data': result or [], 'adapter': 'data818'}

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
            return {**result, 'adapter': 'data818'}
        return {'taskNo': result, 'adapter': 'data818'}

    def query_task(self, task_no: str) -> dict[str, Any]:
        result = self._get('/api/filter/task_query', {'taskNo': task_no})
        if isinstance(result, dict):
            return {**result, 'adapter': 'data818'}
        return {'result': result, 'adapter': 'data818'}

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

    def get_download(self, task_no: str, *, fmt: DownloadFormat = 'csv') -> FilePayload:
        path = _FORMAT_PATH.get(fmt)
        if not path:
            raise _Exception(422, f'不支持的 format: {fmt}')
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                resp = client.get(
                    f'{self.base}{path}',
                    headers=self.headers,
                    params={'taskNo': task_no},
                )
                resp.raise_for_status()
                content_type = (resp.headers.get('content-type') or '').lower()
                # data818 业务错误常为 JSON envelope（HTTP 仍可能 200）
                if 'application/json' in content_type:
                    payload = resp.json()
                    if isinstance(payload, dict) and (
                        payload.get('success') is False or int(payload.get('code') or 0) >= 400
                        or int(payload.get('code') or 0) == 201
                    ):
                        raise _Exception(
                            int(payload.get('code') or 502),
                            payload.get('message') or f'{path} failed',
                        )
                    # get_csv 成功时常返回 { result: { resultUrl } }
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
                        f'{task_no}.{fmt}',
                    )
                    return FilePayload(
                        content=file_resp.content,
                        content_type=file_resp.headers.get('content-type') or 'application/octet-stream',
                        filename=filename,
                    )

                filename = self._filename_from_disposition(
                    resp.headers.get('content-disposition'),
                    f'{task_no}.{fmt}',
                )
                return FilePayload(
                    content=resp.content,
                    content_type=resp.headers.get('content-type') or 'application/octet-stream',
                    filename=filename,
                )
        except _Exception:
            raise
        except httpx.HTTPError as exc:
            raise _Exception(502, f'data818 GET {path}: {exc}') from exc

    def list_filter_types(self) -> list[dict[str, Any]]:
        result = self._get('/api/filter/type/get')
        return result or []

    def list_countries(self) -> list[dict[str, Any]]:
        result = self._get('/api/filter/country_info/get')
        return result or []

    def get_balance(self) -> dict[str, Any]:
        result = self._get('/api/filter/get_balance')
        if isinstance(result, dict):
            return {**result, 'adapter': 'data818'}
        return {'balance': result, 'adapter': 'data818'}

    def close_task(self, task_no: str) -> dict[str, Any]:
        self._post_json('/admin/third_management/task/close', {'orderId': task_no})
        return {'taskNo': task_no, 'status': -1, 'adapter': 'data818'}

    def refund_task(self, task_no: str) -> dict[str, Any]:
        self._post_json('/admin/third_management/task/refund', {'orderId': task_no})
        return {'taskNo': task_no, 'status': -1, 'adapter': 'data818'}

    def retry_task(self, task_no: str) -> dict[str, Any]:
        # data818 schema: orderId int；数字串则转 int，否则原样（可能被下游拒绝）
        order_id: Any = int(task_no) if task_no.isdigit() else task_no
        self._post_json('/admin/super/query/retry', {'orderId': order_id})
        return {'taskNo': task_no, 'status': 2, 'adapter': 'data818'}

    def statistics(self, *, task_type: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if task_type:
            params['taskType'] = task_type
        result = self._get('/business/statisticsForTable', params)
        if isinstance(result, dict) and 'series' in result:
            return {**result, 'adapter': 'data818'}
        # data818: [{ createTime, tasks: [{taskType, taskNumber, description}] }, ...]
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
            return {'days': 30, 'series': series, 'adapter': 'data818'}
        return {'raw': result, 'adapter': 'data818'}

    def list_orders(
        self,
        *,
        page_no: int = 1,
        page_size: int = 20,
        order_id: str | None = None,
        task_type: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {'pageNo': page_no, 'pageSize': page_size}
        if order_id:
            params['orderId'] = order_id
        if task_type:
            params['taskType'] = task_type
        result = self._get('/order/list', params)
        if isinstance(result, dict):
            return {**result, 'adapter': 'data818'}
        return {
            'pageNo': page_no,
            'pageSize': page_size,
            'total': 0,
            'data': result or [],
            'adapter': 'data818',
        }

    def third_balances(self) -> list[dict[str, Any]]:
        result = self._get('/admin/third_management/get_third_balance')
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
            return {**result, 'adapter': 'data818'}
        return {
            'pageNo': page_no,
            'pageSize': page_size,
            'total': 0,
            'data': result or [],
            'adapter': 'data818',
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
        # data818 LedgerType 枚举固定；无单独 list API
        return [
            {'ledgerType': 'ORDER_PAY', 'description': '订单支付'},
            {'ledgerType': 'ORDER_REFUND', 'description': '订单退款'},
            {'ledgerType': 'RECHARGE', 'description': '充值'},
            {'ledgerType': 'ADJUST', 'description': '管理员调整'},
        ]

    def export_remaining(self, task_no: str) -> FilePayload | dict[str, Any]:
        # 下游多为 OSS object_path；仅 http(s) 可二次拉取成文件流
        path = self._post_json('/business/taskRecord/exportRemainingPhone', {'id': task_no})
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
            return {
                'objectPath': object_path,
                'downloadable': False,
                'adapter': 'data818',
            }
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                resp = client.get(url, headers=self.headers)
                resp.raise_for_status()
                filename = self._filename_from_disposition(
                    resp.headers.get('content-disposition'),
                    f'{task_no}-remaining.txt',
                )
                return FilePayload(
                    content=resp.content,
                    content_type=resp.headers.get('content-type') or 'text/plain; charset=utf-8',
                    filename=filename,
                )
        except httpx.HTTPError as exc:
            raise _Exception(502, f'拉取剩余号失败: {exc}') from exc


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
