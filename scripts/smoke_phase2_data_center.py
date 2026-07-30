"""Phase 2 联调冒烟（真实 data-center）：余额 → 类型 → 列表 → 可选建/查/下。

用法:
    python -m scripts.smoke_phase2_data_center
    python -m scripts.smoke_phase2_data_center --create --yes
"""
from __future__ import annotations

import argparse
import io
import sys
from typing import Any

from app.adapters.data_center import DataCenterAdapter
from app.adapters.base import FilePayload
from app.utils.response import _Exception

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def _pick_completed(tasks: list[dict[str, Any]]) -> dict[str, Any] | None:
    for t in tasks:
        if int(t.get('status') or 0) == 1 and t.get('taskNo'):
            return t
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description='Phase2 data-center smoke')
    parser.add_argument('--create', action='store_true')
    parser.add_argument('--filter-type', default='wsValid')
    parser.add_argument('--country', default='AD')
    parser.add_argument('--count', type=int, default=0)
    parser.add_argument('--fmt', default='csv', choices=['csv', 'txt', 'xlsx', 'invalid'])
    parser.add_argument('--no-download', action='store_true')
    parser.add_argument('--yes', action='store_true')
    args = parser.parse_args()

    try:
        adapter = DataCenterAdapter()
    except RuntimeError as exc:
        print(f'BLOCKED: {exc}')
        return 2

    results: list[tuple[str, bool, str]] = []

    def step(name: str, fn) -> Any:
        try:
            out = fn()
            results.append((name, True, ''))
            print(f'PASS {name}')
            return out
        except _Exception as exc:
            results.append((name, False, f'code={exc.code} {exc.message}'))
            print(f'FAIL {name}: code={exc.code} {exc.message}')
            return None
        except Exception as exc:  # noqa: BLE001
            results.append((name, False, str(exc)))
            print(f'FAIL {name}: {exc}')
            return None

    step('余额', adapter.get_balance)
    types = step('筛选类型', adapter.list_filter_types)
    countries = step('国家', adapter.list_countries)
    listing = step('任务列表', lambda: adapter.list_tasks(page_no=1, page_size=10))
    notices = step('公告(应为空)', adapter.list_notices)
    if notices is not None and notices != []:
        results.append(('公告空列表', False, f'got {len(notices)}'))
        print(f'FAIL 公告空列表: got {len(notices)}')
    elif notices is not None:
        print('PASS 公告空列表')

    completed = _pick_completed((listing or {}).get('data') or [])
    created_no = ''

    if args.create:
        meta = next((t for t in (types or []) if t.get('filter_type') == args.filter_type), None)
        if not meta:
            print(f'ABORT: 未知 filterType {args.filter_type}')
            return 2
        min_count = int(meta.get('min_count') or 500)
        n = args.count or min_count
        region = next(
            (str(c.get('countryRegion') or '') for c in (countries or []) if c.get('countryCode') == args.country),
            '',
        )
        if not region:
            print(f'ABORT: 未知国家 {args.country}')
            return 2
        if not args.yes:
            print(f'即将建单：{args.filter_type} {args.country} x{n}（按量计费）')
            print('重跑加 --yes 确认。')
            return 3
        body = ('\n'.join(f'{region}7{i:09d}' for i in range(n)) + '\n').encode()
        created = step(
            f'建任务 {args.filter_type}/{args.country} x{n}',
            lambda: adapter.create_task(
                filter_type=args.filter_type,
                country_code=args.country,
                describe='smoke-phase2',
                filename='smoke.txt',
                file_obj=io.BytesIO(body),
            ),
        )
        created_no = str((created or {}).get('taskNo') or '')
    if created_no:
        step('查询新任务', lambda: adapter.query_task(created_no))

    if not args.no_download:
        target = created_no or (completed or {}).get('taskNo') or ''
        if target:
            payload = step(
                f'下载 {target} ({args.fmt})',
                lambda: adapter.get_download(target, fmt=args.fmt),
            )
            if isinstance(payload, FilePayload):
                print(f'  -> bytes={len(payload.content)} filename={payload.filename}')
        else:
            print('SKIP 下载：无已完成任务，且未 --create')

    ok = sum(1 for _, passed, _ in results if passed)
    total = len(results)
    print(f'\nRESULT {ok}/{total} passed')
    return 0 if ok == total else 1


if __name__ == '__main__':
    sys.exit(main())
