from flask import Blueprint, request

from app.exts.auth_guard import login_required
from app.schema.auth import BillListSchema
from app.service.task import TaskService
from app.utils.response import Success

bp = Blueprint('bills', __name__, url_prefix='/bills')


@bp.route('', methods=['GET'])
@login_required
def list_bills():
    data = BillListSchema(**request.args.to_dict())
    return Success(result=TaskService.list_bills(data))
