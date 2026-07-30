from flask import Blueprint

from app.exts.auth_guard import login_required
from app.service.task import TaskService
from app.utils.response import Success

bp = Blueprint('notices', __name__, url_prefix='/notices')


@bp.route('', methods=['GET'])
@login_required
def list_notices():
    return Success(result=TaskService.list_notices())


@bp.route('/<notice_id>', methods=['GET'])
@login_required
def get_notice(notice_id: str):
    return Success(result=TaskService.get_notice(notice_id))
