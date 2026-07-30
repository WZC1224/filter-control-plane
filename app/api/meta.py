from flask import Blueprint, request

from app.exts.auth_guard import login_required
from app.service.task import TaskService
from app.utils.response import Success
from config import settings

bp = Blueprint('meta', __name__, url_prefix='/meta')


@bp.route('/health', methods=['GET'])
def health():
    from datetime import datetime, timezone

    return Success(
        result={
            'service': 'filter-control-plane',
            'version': getattr(settings, 'APP_VERSION', '0.1.0'),
            'adapter': 'mock' if settings.use_mock_adapter else 'data818',
            'mock': settings.use_mock_adapter,
            'time': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        }
    )


@bp.route('/filter-types', methods=['GET'])
@login_required
def filter_types():
    return Success(result=TaskService.filter_types())


@bp.route('/countries', methods=['GET'])
@login_required
def countries():
    return Success(result=TaskService.countries())


@bp.route('/balance', methods=['GET'])
@login_required
def balance():
    return Success(result=TaskService.balance())


@bp.route('/statistics', methods=['GET'])
@login_required
def statistics():
    task_type = (request.args.get('taskType') or '').strip() or None
    return Success(result=TaskService.statistics(task_type=task_type))


@bp.route('/third-balances', methods=['GET'])
@login_required
def third_balances():
    return Success(result=TaskService.third_balances())


@bp.route('/products', methods=['GET'])
@login_required
def products():
    return Success(result=TaskService.list_products())


@bp.route('/order-task-types', methods=['GET'])
@login_required
def order_task_types():
    return Success(result=TaskService.list_order_task_types())


@bp.route('/ledger-types', methods=['GET'])
@login_required
def ledger_types():
    return Success(result=TaskService.list_ledger_types())
