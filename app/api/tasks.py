from flask import Blueprint, request

from app.exts.auth_guard import login_required
from app.schema.auth import CreateTaskFieldsSchema, TaskListSchema
from app.service.task import TaskService
from app.utils.response import Success

bp = Blueprint('tasks', __name__, url_prefix='/tasks')


@bp.route('', methods=['GET'])
@login_required
def list_tasks():
    data = TaskListSchema(**request.args.to_dict())
    return Success(result=TaskService.list_tasks(data))


@bp.route('', methods=['POST'])
@login_required
def create_task():
    form = request.form.to_dict()
    fields = CreateTaskFieldsSchema(
        filterType=form.get('filterType') or '',
        countryCode=form.get('countryCode') or '',
        describe=form.get('describe') or '',
    )
    upload = request.files.get('file')
    result = TaskService.create_task(
        filter_type=fields.filterType,
        country_code=fields.countryCode,
        describe=fields.describe,
        upload=upload,
    )
    return Success(message='任务已提交', result=result)


@bp.route('/<task_no>', methods=['GET'])
@login_required
def query_task(task_no: str):
    return Success(result=TaskService.query_task(task_no))


@bp.route('/<task_no>/download', methods=['GET'])
@login_required
def download(task_no: str):
    fmt = (request.args.get('format') or 'csv').strip().lower()
    return TaskService.download(task_no, fmt=fmt)


@bp.route('/<task_no>/close', methods=['POST'])
@login_required
def close_task(task_no: str):
    return Success(message='已关闭', result=TaskService.close_task(task_no))


@bp.route('/<task_no>/refund', methods=['POST'])
@login_required
def refund_task(task_no: str):
    return Success(message='已退款', result=TaskService.refund_task(task_no))


@bp.route('/<task_no>/retry', methods=['POST'])
@login_required
def retry_task(task_no: str):
    return Success(message='已重试', result=TaskService.retry_task(task_no))


@bp.route('/<task_no>/export-remaining', methods=['GET'])
@login_required
def export_remaining(task_no: str):
    result = TaskService.export_remaining(task_no)
    if isinstance(result, dict):
        return Success(message='剩余号已生成（OSS 路径）', result=result)
    return result
