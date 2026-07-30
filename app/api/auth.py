from flask import Blueprint, g, request

from app.exts.auth_guard import admin_required, login_required
from app.exts.login_rate_limit import login_limiter
from app.schema.auth import ChangePasswordSchema, CreateUserSchema, LoginSchema, PatchUserSchema
from app.service.auth import AuthService
from app.utils.response import Fail, Success
from config import settings

bp = Blueprint('auth', __name__, url_prefix='/auth')
users_bp = Blueprint('users', __name__, url_prefix='/users')


def _login_client_key() -> str:
    if settings.TRUST_PROXY_HEADERS:
        xff = (request.headers.get('X-Forwarded-For') or '').strip()
        if xff:
            return xff.split(',')[0].strip() or 'unknown'
    return request.remote_addr or 'unknown'


@bp.route('/login', methods=['POST'])
def login():
    key = _login_client_key()
    if not login_limiter.allow(
        key,
        max_hits=settings.LOGIN_RATE_LIMIT_MAX,
        window_seconds=settings.LOGIN_RATE_WINDOW_SECONDS,
    ):
        return Fail(code=429, message='登录尝试过多，请稍后再试')
    data = LoginSchema(**(request.get_json(silent=True) or {}))
    result = AuthService.login(data)
    return Success(message='登录成功', result=result)


@bp.route('/me', methods=['GET'])
@login_required
def me():
    u = g.user
    return Success(result={'username': u.username, 'role': u.role, 'isActive': bool(u.is_active)})


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
    return Success(result=AuthService.patch_user(user_id, data))
