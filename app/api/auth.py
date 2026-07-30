from flask import Blueprint, g, request

from app.exts.auth_guard import admin_required, login_required
from app.schema.auth import ChangePasswordSchema, CreateUserSchema, LoginSchema, PatchUserSchema
from app.service.auth import AuthService
from app.utils.response import Success

bp = Blueprint('auth', __name__, url_prefix='/auth')
users_bp = Blueprint('users', __name__, url_prefix='/users')


@bp.route('/login', methods=['POST'])
def login():
    data = LoginSchema(**(request.get_json(silent=True) or {}))
    result = AuthService.login(data)
    return Success(message='登录成功', result=result)


@bp.route('/me', methods=['GET'])
@login_required
def me():
    return Success(
        result={
            'username': g.user.username,
            'role': g.user.role,
            'isActive': bool(g.user.is_active),
        }
    )


@bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    data = ChangePasswordSchema(**(request.get_json(silent=True) or {}))
    AuthService.change_password(g.user, data)
    return Success(message='密码已更新')


@users_bp.route('', methods=['GET'])
@admin_required
def list_users():
    return Success(result=AuthService.list_users())


@users_bp.route('', methods=['POST'])
@admin_required
def create_user():
    data = CreateUserSchema(**(request.get_json(silent=True) or {}))
    return Success(message='已创建', result=AuthService.create_user(data))


@users_bp.route('/<int:user_id>', methods=['PATCH'])
@admin_required
def patch_user(user_id: int):
    data = PatchUserSchema(**(request.get_json(silent=True) or {}))
    return Success(result=AuthService.patch_user(user_id, data, actor=g.user))
