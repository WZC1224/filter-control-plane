from io import BytesIO

from flask import send_file
from werkzeug.datastructures import FileStorage

from app.adapters import get_adapter
from app.adapters.base import DownloadFormat, FilePayload
from app.schema.auth import TaskListSchema
from app.utils.response import _Exception
from config import settings

_SUPPORTED_FORMATS = frozenset({'csv', 'txt', 'xlsx', 'parquet', 'zip'})


def safe_download_name(name: str | None, fallback: str) -> str:
    """剥路径与控制字符；保留非 ASCII 文件名（secure_filename 会抹掉中文）。"""
    raw = (name or '').replace('\\', '/').rsplit('/', 1)[-1].strip()
    cleaned = ''.join(ch for ch in raw if ord(ch) >= 32 and ch not in '"\\')
    return cleaned or fallback


def resolve_download_mimetype(content_type: str | None) -> str:
    """成功附件禁止 application/json；空 mime 回退 octet-stream。"""
    mime = (content_type or '').split(';')[0].strip().lower()
    if 'json' in mime:
        raise _Exception(502, '下游 Content-Type 为 JSON，无法作为附件下载')
    return mime or 'application/octet-stream'


def normalize_task(item: dict) -> dict:
    """控制平面对外 Task 形（camelCase）。见 docs/api-contract.md。

    data818 开放筛选 / 业务下载的 id = order_id；管理端行里另有 partitionId/taskNo，
    对外 taskNo 优先 orderId，避免点进详情后下载用错号。
    """
    return {
        'taskNo': (
            item.get('orderId')
            or item.get('order_id')
            or item.get('taskNo')
            or item.get('task_no')
            or ''
        ),
        'taskName': item.get('taskName') or item.get('task_name') or '',
        'taskType': item.get('taskType') or item.get('task_type') or '',
        'country': item.get('country') or item.get('countryCode') or item.get('country_code') or '',
        'status': item.get('status') if item.get('status') is not None else item.get('taskStatus'),
        'progress': item.get('progress') if item.get('progress') is not None else item.get('taskProgress'),
        'effectiveQuantity': (
            item.get('effectiveQuantity')
            if item.get('effectiveQuantity') is not None
            else item.get('effective_quantity')
            if item.get('effective_quantity') is not None
            else item.get('taskEffectiveQuantity')
        ),
        'count': item.get('count') if item.get('count') is not None else item.get('taskNumber'),
        'createDate': (
            item.get('createDate')
            or item.get('create_date')
            or item.get('createTime')
            or item.get('create_time')
            or ''
        ),
        'description': item.get('description') or item.get('describe') or '',
        'orderId': item.get('orderId') or item.get('order_id') or '',
        'userName': item.get('userName') or item.get('username') or '',
        'partitionId': item.get('partitionId') or item.get('partition_id') or '',
    }


def normalize_order(item: dict) -> dict:
    """控制平面对外 Order 形。

    兼容两路下游：
    - `/order/list` → Order.order_to（含 unitPrice / balanceDeduction）
    - `/admin/third_management/task_list` → Order.to_all（含 taskStatus / accountExpend）
    """
    consume_status = item.get('consumeStatus')
    if consume_status is None:
        consume_status = item.get('taskStatus')
    if consume_status is None:
        consume_status = item.get('status')

    return {
        'orderId': item.get('orderId') or item.get('order_id') or '',
        'partitionId': item.get('partitionId') or item.get('partition_id') or '',
        'userName': item.get('userName') or item.get('username') or '',
        'taskType': item.get('taskType') or item.get('task_type') or '',
        'consumeType': (
            item.get('consumeType')
            if item.get('consumeType') is not None
            else item.get('consume_type')
        ),
        'consumeStatus': consume_status,
        'taskCount': (
            item.get('taskCount')
            or item.get('taskNumber')
            or item.get('count')
            or ''
        ),
        'unitPrice': item.get('unitPrice') or item.get('unit_price') or '',
        'balanceDeduction': item.get('balanceDeduction') or item.get('balance_deduction') or '',
        'actualDeduction': (
            item.get('actualDeduction')
            or item.get('actual_deduction')
            or item.get('accountExpend')
            or ''
        ),
        'currentBalance': item.get('currentBalance') or item.get('current_balance') or '',
        'createTime': item.get('createTime') or item.get('create_date') or item.get('createDate') or '',
        'description': item.get('description') or '',
        'thirdSource': item.get('thirdSource') or item.get('third_source') or '',
        'countryCode': item.get('countryCode') or item.get('country') or '',
        'taskNo': item.get('taskNo') or item.get('task_no') or '',
    }


def normalize_bill(item: dict) -> dict:
    return {
        'billId': item.get('billId') or item.get('bill_id') or '',
        'username': item.get('username') or '',
        'amount': item.get('amount'),
        'ledgerType': item.get('ledgerType') or item.get('ledger_type') or '',
        'consumeType': item.get('consumeType') or item.get('consume_type') or '',
        'balanceBefore': item.get('balanceBefore') or item.get('balance_before'),
        'balanceAfter': item.get('balanceAfter') or item.get('balance_after'),
        'bizType': item.get('bizType') or item.get('biz_type') or '',
        'bizId': item.get('bizId') or item.get('biz_id') or '',
        'description': item.get('description') or '',
        'createDate': item.get('createDate') or item.get('create_date') or '',
    }


def normalize_notice(item: dict) -> dict:
    return {
        'id': item.get('id'),
        'title': item.get('title') or '',
        'contentMd': item.get('contentMd') or item.get('content_md') or '',
        'bizType': item.get('bizType') or item.get('biz_type') or '',
        'level': item.get('level') or '',
        'publishStatus': item.get('publishStatus') or item.get('publish_status') or '',
        'createDate': item.get('createDate') or item.get('create_date') or '',
        'expireDate': item.get('expireDate') or item.get('expire_date') or '',
    }


class TaskService:
    @staticmethod
    def adapter_mode() -> str:
        return settings.adapter_name

    @staticmethod
    def list_tasks(data: TaskListSchema) -> dict:
        adapter = get_adapter()
        result = adapter.list_tasks(
            page_no=data.pageNo,
            page_size=data.pageSize,
            task_type=data.taskType,
            task_no=data.taskNo,
            country_code=data.countryCode,
            task_status=data.taskStatus,
        )
        rows = result.get('data') or []
        result['data'] = [normalize_task(r) if isinstance(r, dict) else r for r in rows]
        return result

    @staticmethod
    def create_task(
        *,
        filter_type: str,
        country_code: str,
        describe: str,
        upload: FileStorage,
    ) -> dict:
        if not upload or not upload.filename:
            raise _Exception(422, '缺少上传文件')
        if not upload.filename.lower().endswith('.txt'):
            raise _Exception(422, '仅支持 .txt')
        adapter = get_adapter()
        return adapter.create_task(
            filter_type=filter_type,
            country_code=country_code,
            describe=describe,
            filename=upload.filename,
            file_obj=upload.stream,
        )

    @staticmethod
    def query_task(task_no: str) -> dict:
        raw = get_adapter().query_task(task_no)
        return normalize_task(raw) if isinstance(raw, dict) else raw

    @staticmethod
    def download(task_no: str, *, fmt: str = 'csv'):
        fmt = (fmt or 'csv').strip().lower()
        if fmt not in _SUPPORTED_FORMATS:
            raise _Exception(422, 'format 仅支持 csv / txt / xlsx / parquet / zip')
        payload: FilePayload = get_adapter().get_download(
            task_no, fmt=fmt  # type: DownloadFormat
        )
        mime = resolve_download_mimetype(payload.content_type)
        filename = safe_download_name(payload.filename, f'{task_no}.{fmt}')
        return send_file(
            BytesIO(payload.content),
            mimetype=mime,
            as_attachment=True,
            download_name=filename,
        )

    @staticmethod
    def filter_types() -> list:
        return get_adapter().list_filter_types()

    @staticmethod
    def countries() -> list:
        return get_adapter().list_countries()

    @staticmethod
    def balance() -> dict:
        return get_adapter().get_balance()

    @staticmethod
    def close_task(task_no: str) -> dict:
        return get_adapter().close_task(task_no)

    @staticmethod
    def refund_task(task_no: str) -> dict:
        return get_adapter().refund_task(task_no)

    @staticmethod
    def retry_task(task_no: str) -> dict:
        return get_adapter().retry_task(task_no)

    @staticmethod
    def statistics(*, task_type: str | None = None) -> dict:
        return get_adapter().statistics(task_type=task_type)

    @staticmethod
    def list_orders(data) -> dict:
        from app.schema.auth import OrderListSchema

        assert isinstance(data, OrderListSchema)
        adapter = get_adapter()
        result = adapter.list_orders(
            page_no=data.pageNo,
            page_size=data.pageSize,
            order_id=data.orderId,
            task_type=data.taskType,
            description=data.description,
            username=data.username,
            consume_type=data.consumeType,
            create_time_begin=data.createTimeBegin,
            create_time_end=data.createTimeEnd,
        )
        rows = result.get('data') or []
        result['data'] = [normalize_order(r) if isinstance(r, dict) else r for r in rows]
        return result

    @staticmethod
    def third_balances() -> list:
        return get_adapter().third_balances()

    @staticmethod
    def list_bills(data) -> dict:
        from app.schema.auth import BillListSchema

        assert isinstance(data, BillListSchema)
        result = get_adapter().list_bills(
            page_no=data.pageNo,
            page_size=data.pageSize,
            bill_id=data.billId,
            order_id=data.orderId,
            ledger_type=data.ledgerType,
        )
        rows = result.get('data') or []
        result['data'] = [normalize_bill(r) if isinstance(r, dict) else r for r in rows]
        return result

    @staticmethod
    def list_notices() -> list:
        rows = get_adapter().list_notices() or []
        return [normalize_notice(r) if isinstance(r, dict) else r for r in rows]

    @staticmethod
    def get_notice(notice_id: str) -> dict:
        raw = get_adapter().get_notice(notice_id)
        return normalize_notice(raw) if isinstance(raw, dict) else raw

    @staticmethod
    def list_products() -> list:
        return get_adapter().list_products() or []

    @staticmethod
    def list_order_task_types() -> list:
        return get_adapter().list_order_task_types() or []

    @staticmethod
    def list_ledger_types() -> list:
        return get_adapter().list_ledger_types() or []

    @staticmethod
    def export_remaining(task_no: str):
        result = get_adapter().export_remaining(task_no)
        if isinstance(result, FilePayload):
            mime = resolve_download_mimetype(result.content_type)
            filename = safe_download_name(result.filename, f'{task_no}-remaining.txt')
            return send_file(
                BytesIO(result.content),
                mimetype=mime,
                as_attachment=True,
                download_name=filename,
            )
        return result
