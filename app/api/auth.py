from flask import Blueprint, g, request

from app.exts.auth_guard import login_required
from app.schema.auth import ChangePasswordSchema, LoginSchema
from app.service.auth import AuthService
from app.utils.response import Success

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['POST'])
def login():
    data = LoginSchema(**(request.get_json(silent=True) or {}))
    result = AuthService.login(data)
    return Success(message='登录成功', result=result)


@bp.route('/me', methods=['GET'])
@login_required
def me():
    return Success(result={'username': g.user.username})


@bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    data = ChangePasswordSchema(**(request.get_json(silent=True) or {}))
    AuthService.change_password(g.user, data)
    return Success(message='密码已更新')
