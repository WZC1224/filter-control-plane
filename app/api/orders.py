from flask import Blueprint, request

from app.exts.auth_guard import login_required
from app.schema.auth import OrderListSchema
from app.service.task import TaskService
from app.utils.response import Success

bp = Blueprint('orders', __name__, url_prefix='/orders')


@bp.route('', methods=['GET'])
@login_required
def list_orders():
    data = OrderListSchema(**request.args.to_dict())
    return Success(result=TaskService.list_orders(data))
