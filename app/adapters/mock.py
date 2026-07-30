from __future__ import annotations

import time
import uuid
from typing import Any, BinaryIO

from app.adapters.base import DownstreamAdapter, DownloadFormat, FilePayload
from app.utils.response import _Exception


class MockAdapter(DownstreamAdapter):
    """无下游配置时的内存假数据，保证控制平面可本地演示。"""

    def __init__(self) -> None:
        self._balance = 12850.5
        self._tasks: list[dict[str, Any]] = [
            {
                'taskNo': 'MOCK-1001',
                'taskName': 'demo-wsValid',
                'taskType': 'wsValid',
                'country': 'US',
                'status': 1,
                'count': 1000,
                'effectiveQuantity': 860,
                'progress': 100,
                'createDate': '2026-07-29 10:00:00',
                'description': 'mock completed task',
            },
            {
                'taskNo': 'MOCK-1002',
                'taskName': 'demo-running',
                'taskType': 'wsActive',
                'country': 'GB',
                'status': 2,
                'count': 500,
                'effectiveQuantity': 0,
                'progress': 42,
                'createDate': '2026-07-30 09:00:00',
                'description': 'mock running task',
            },
            {
                'taskNo': 'MOCK-1003',
                'taskName': 'demo-failed',
                'taskType': 'wsValid',
                'country': 'ID',
                'status': -1,
                'count': 200,
                'effectiveQuantity': 0,
                'progress': 0,
                'createDate': '2026-07-28 18:00:00',
                'description': 'mock failed task',
            },
            {
                'taskNo': 'MOCK-1004',
                'taskName': 'demo-queued',
                'taskType': 'tgValid',
                'country': 'US',
                'status': 0,
                'count': 300,
                'effectiveQuantity': 0,
                'progress': 0,
                'createDate': '2026-07-30 11:00:00',
                'description': 'mock queued task',
                'actualDeduction': 3.0,
            },
        ]

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
        rows = self._tasks
        if task_type:
            rows = [t for t in rows if t['taskType'] == task_type]
        if task_no:
            rows = [t for t in rows if task_no in t['taskNo']]
        if country_code:
            rows = [t for t in rows if t['country'] == country_code]
        if task_status is not None:
            rows = [t for t in rows if t['status'] == task_status]
        total = len(rows)
        start = (page_no - 1) * page_size
        data = rows[start: start + page_size]
        return {
            'pageNo': page_no,
            'pageSize': page_size,
            'total': total,
            'data': data,
            'adapter': 'mock',
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
        content = file_obj.read()
        if isinstance(content, bytes):
            text = content.decode('utf-8', errors='ignore')
        else:
            text = str(content)
        lines = [ln for ln in text.splitlines() if ln.strip()]
        task_no = f'MOCK-{uuid.uuid4().hex[:8].upper()}'
        item = {
            'taskNo': task_no,
            'taskName': filename or task_no,
            'taskType': filter_type,
            'country': country_code.upper(),
            'status': 2,
            'count': len(lines),
            'effectiveQuantity': 0,
            'progress': 0,
            'createDate': time.strftime('%Y-%m-%d %H:%M:%S'),
            'description': describe or 'created via mock',
        }
        self._tasks.insert(0, item)
        self._balance = max(0.0, self._balance - max(len(lines), 1) * 0.01)
        return {'taskNo': task_no, 'adapter': 'mock'}

    def query_task(self, task_no: str) -> dict[str, Any]:
        for t in self._tasks:
            if t['taskNo'] == task_no:
                # 进行中任务每次查询推进一点，便于前端轮询演示
                if t.get('status') == 2:
                    t['progress'] = min(100, int(t.get('progress') or 0) + 8)
                    if t['progress'] >= 100:
                        t['status'] = 1
                        t['effectiveQuantity'] = max(1, int((t.get('count') or 1) * 0.8))
                return {**t, 'adapter': 'mock'}
        return {'taskNo': task_no, 'status': -1, 'message': 'not found', 'adapter': 'mock'}

    def get_download(self, task_no: str, *, fmt: DownloadFormat = 'csv') -> FilePayload:
        task = next((t for t in self._tasks if t['taskNo'] == task_no), None)
        if not task:
            raise _Exception(400, '任务不存在')
        if task.get('status') != 1:
            raise _Exception(201, '暂无可下载数据')
        if fmt == 'txt':
            body = f"12015550100\n12015550101\n# mock {task_no}\n".encode('utf-8')
            return FilePayload(content=body, content_type='text/plain; charset=utf-8', filename=f'{task_no}.txt')
        if fmt == 'invalid':
            body = f"12015550999\n# mock invalid {task_no}\n".encode('utf-8')
            return FilePayload(
                content=body,
                content_type='text/plain; charset=utf-8',
                filename=f'{task_no}-invalid.txt',
            )
        if fmt == 'xlsx':
            # 假 xlsx：最小 ZIP/PK 头，仅供流式下载联调（非真 Office 文件）
            body = b'PK\x03\x04mock-xlsx-' + task_no.encode('ascii', errors='ignore')
            return FilePayload(
                content=body,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                filename=f'{task_no}.xlsx',
            )
        body = f'phone,status\n12015550100,valid\n12015550101,valid\n# mock {task_no}\n'.encode('utf-8')
        return FilePayload(content=body, content_type='text/csv; charset=utf-8', filename=f'{task_no}.csv')

    def list_filter_types(self) -> list[dict[str, Any]]:
        return [
            {'filter_type': 'wsValid', 'description': 'WhatsApp 有效性', 'min_count': 1, 'max_count': 100000},
            {'filter_type': 'wsActive', 'description': 'WhatsApp 活跃', 'min_count': 1, 'max_count': 100000},
            {'filter_type': 'tgValid', 'description': 'Telegram 有效性', 'min_count': 1, 'max_count': 100000},
        ]

    def list_countries(self) -> list[dict[str, Any]]:
        return [
            {'countryCode': 'US', 'countryName': 'United States'},
            {'countryCode': 'GB', 'countryName': 'United Kingdom'},
            {'countryCode': 'ID', 'countryName': 'Indonesia'},
        ]

    def get_balance(self) -> dict[str, Any]:
        return {'balance': self._balance, 'currency': 'CNY', 'adapter': 'mock'}

    def _find(self, task_no: str) -> dict[str, Any]:
        task = next((t for t in self._tasks if t['taskNo'] == task_no), None)
        if not task:
            raise _Exception(400, '任务不存在')
        return task

    def close_task(self, task_no: str) -> dict[str, Any]:
        task = self._find(task_no)
        if task.get('status') != 0:
            raise _Exception(400, '仅排队且未上传任务可关闭')
        refund = float(task.get('actualDeduction') or 0)
        self._balance += refund
        task['status'] = -1
        task['actualDeduction'] = 0
        task['description'] = (task.get('description') or '') + ' [closed]'
        return {'taskNo': task_no, 'status': -1, 'adapter': 'mock'}

    def refund_task(self, task_no: str) -> dict[str, Any]:
        task = self._find(task_no)
        if task.get('status') not in (1, 3):
            raise _Exception(400, '当前订单无法退款')
        refund = float(task.get('actualDeduction') or max(1, int(task.get('count') or 1)) * 0.01)
        self._balance += refund
        task['status'] = -1
        task['description'] = (task.get('description') or '') + ' [refunded]'
        return {'taskNo': task_no, 'status': -1, 'adapter': 'mock'}

    def retry_task(self, task_no: str) -> dict[str, Any]:
        task = self._find(task_no)
        if task.get('status') not in (-1, 3, 1):
            raise _Exception(400, '当前状态不可重试')
        task['status'] = 2
        task['progress'] = 0
        task['effectiveQuantity'] = 0
        task['description'] = (task.get('description') or '') + ' [retry]'
        return {'taskNo': task_no, 'status': 2, 'adapter': 'mock'}

    def statistics(self, *, task_type: str | None = None) -> dict[str, Any]:
        """近 30 天按日汇总（Mock：用完成任务的 createDate + count）。"""
        from datetime import datetime, timedelta, timezone

        today = datetime.now(timezone.utc).date()
        days = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(29, -1, -1)]
        by_day: dict[str, list[dict[str, Any]]] = {d: [] for d in days}
        for t in self._tasks:
            if t.get('status') != 1:
                continue
            if task_type and t.get('taskType') != task_type:
                continue
            day = str(t.get('createDate') or '')[:10]
            if day not in by_day:
                continue
            by_day[day].append(
                {
                    'taskType': t.get('taskType'),
                    'taskNumber': t.get('count') or 0,
                    'taskName': t.get('taskType'),
                }
            )
        series = [{'date': d, 'items': by_day[d], 'total': sum(i['taskNumber'] for i in by_day[d])} for d in days]
        return {'days': 30, 'series': series, 'adapter': 'mock'}

    def list_orders(
        self,
        *,
        page_no: int = 1,
        page_size: int = 20,
        order_id: str | None = None,
        task_type: str | None = None,
    ) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        for t in self._tasks:
            deduction = float(t.get('actualDeduction') or max(1, int(t.get('count') or 1)) * 0.01)
            rows.append(
                {
                    'orderId': t['taskNo'],
                    'userName': 'mock',
                    'taskType': t.get('taskType'),
                    'consumeStatus': t.get('status'),
                    'taskCount': str(t.get('count') or 0),
                    'actualDeduction': f'{deduction:.2f}',
                    'createTime': t.get('createDate') or '',
                    'description': t.get('description') or '',
                    'thirdSource': 'mock',
                }
            )
        if order_id:
            rows = [r for r in rows if order_id in str(r['orderId'])]
        if task_type:
            rows = [r for r in rows if r.get('taskType') == task_type]
        total = len(rows)
        start = (page_no - 1) * page_size
        return {
            'pageNo': page_no,
            'pageSize': page_size,
            'total': total,
            'data': rows[start: start + page_size],
            'adapter': 'mock',
        }

    def third_balances(self) -> list[dict[str, Any]]:
        return [
            {'thirdSourceName': 'tntpub', 'balance': 5200.25},
            {'thirdSourceName': 'aipushai', 'balance': 880.0},
            {'thirdSourceName': 'mock-channel', 'balance': 9999.0},
        ]

    def list_bills(
        self,
        *,
        page_no: int = 1,
        page_size: int = 20,
        bill_id: str | None = None,
        order_id: str | None = None,
        ledger_type: str | None = None,
    ) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        for t in self._tasks:
            amount = float(t.get('actualDeduction') or max(1, int(t.get('count') or 1)) * 0.01)
            rows.append(
                {
                    'billId': f'BILL-{t["taskNo"]}',
                    'username': 'mock',
                    'amount': amount,
                    'ledgerType': 'ORDER_PAY',
                    'consumeType': 'OUT',
                    'balanceBefore': self._balance + amount,
                    'balanceAfter': self._balance,
                    'bizType': t.get('taskType'),
                    'bizId': t['taskNo'],
                    'description': t.get('description') or 'mock consume',
                    'createDate': t.get('createDate') or '',
                }
            )
        rows.append(
            {
                'billId': 'BILL-RECHARGE-1',
                'username': 'mock',
                'amount': 100.0,
                'ledgerType': 'RECHARGE',
                'consumeType': 'IN',
                'balanceBefore': self._balance - 100,
                'balanceAfter': self._balance,
                'bizType': 'recharge',
                'bizId': '',
                'description': 'mock recharge',
                'createDate': '2026-07-28 08:00:00',
            }
        )
        if bill_id:
            rows = [r for r in rows if bill_id in str(r['billId'])]
        if order_id:
            rows = [r for r in rows if order_id in str(r['bizId'])]
        if ledger_type:
            rows = [r for r in rows if r.get('ledgerType') == ledger_type]
        total = len(rows)
        start = (page_no - 1) * page_size
        return {
            'pageNo': page_no,
            'pageSize': page_size,
            'total': total,
            'data': rows[start: start + page_size],
            'adapter': 'mock',
        }

    def list_notices(self) -> list[dict[str, Any]]:
        return [
            {
                'id': 1,
                'title': '控制台 Mock 公告',
                'contentMd': '本地 Mock 模式运行中。配置 `DATA818_*` 后对接真实下游。',
                'bizType': 'SYSTEM',
                'level': 'INFO',
                'publishStatus': 'PUBLISHED',
                'createDate': '2026-07-30 12:00:00',
            },
            {
                'id': 2,
                'title': '运维提示',
                'contentMd': '关单/退款/三方余额需要下游 admin 权限 Token。',
                'bizType': 'OPS',
                'level': 'WARN',
                'publishStatus': 'PUBLISHED',
                'createDate': '2026-07-29 09:00:00',
            },
        ]

    def get_notice(self, notice_id: str) -> dict[str, Any]:
        for n in self.list_notices():
            if str(n.get('id')) == str(notice_id):
                return n
        raise _Exception(400, '公告不存在')

    def list_products(self) -> list[dict[str, Any]]:
        return [
            {
                'taskType': 'wsValid',
                'name': 'WhatsApp 有效性',
                'price': '0.01',
                'applicationType': 'WhatsApp',
                'businessType': '有效性',
                'minCount': 1,
                'maxCount': 100000,
                'thirdSource': 'mock',
            },
            {
                'taskType': 'wsActive',
                'name': 'WhatsApp 活跃',
                'price': '0.02',
                'applicationType': 'WhatsApp',
                'businessType': '活跃',
                'minCount': 1,
                'maxCount': 100000,
                'thirdSource': 'mock',
            },
            {
                'taskType': 'tgValid',
                'name': 'Telegram 有效性',
                'price': '0.015',
                'applicationType': 'Telegram',
                'businessType': '有效性',
                'minCount': 1,
                'maxCount': 50000,
                'thirdSource': 'mock',
            },
        ]

    def list_order_task_types(self) -> list[dict[str, Any]]:
        return [
            {'taskType': 'wsValid', 'description': 'WhatsApp 有效性'},
            {'taskType': 'wsActive', 'description': 'WhatsApp 活跃'},
            {'taskType': 'tgValid', 'description': 'Telegram 有效性'},
            {'taskType': 'recharge', 'description': '充值'},
        ]

    def list_ledger_types(self) -> list[dict[str, Any]]:
        return [
            {'ledgerType': 'ORDER_PAY', 'description': '订单支付'},
            {'ledgerType': 'ORDER_REFUND', 'description': '订单退款'},
            {'ledgerType': 'RECHARGE', 'description': '充值'},
            {'ledgerType': 'ADJUST', 'description': '管理员调整'},
        ]

    def export_remaining(self, task_no: str) -> FilePayload | dict:
        task = self._find(task_no)
        if task.get('status') != 1:
            raise _Exception(201, '仅完成任务可导出剩余号')
        total = int(task.get('count') or 0)
        valid = int(task.get('effectiveQuantity') or 0)
        remain = max(0, total - valid)
        if remain <= 0:
            raise _Exception(201, '无可导出剩余号')
        lines = [f'1201555{i:04d}' for i in range(remain)]
        body = ('\n'.join(lines) + f'\n# mock remaining {task_no}\n').encode('utf-8')
        return FilePayload(
            content=body,
            content_type='text/plain; charset=utf-8',
            filename=f'{task_no}-remaining.txt',
        )
