from werkzeug.security import check_password_hash, generate_password_hash

from app.exts.extensions import db
from app.exts.jwt_auth import jwt_auth
from app.models import ROLE_ADMIN, User
from app.schema.auth import ChangePasswordSchema, CreateUserSchema, LoginSchema, PatchUserSchema
from app.utils.response import _Exception
from config import settings

# 用户不存在时仍跑一次哈希校验，减轻用户名枚举 timing
_DUMMY_PASSWORD_HASH = generate_password_hash('__fcp_dummy_password__')


class AuthService:
    @staticmethod
    def ensure_admin() -> None:
        user = User.query.filter_by(username=settings.ADMIN_USERNAME).first()
        if not user:
            user = User(username=settings.ADMIN_USERNAME, role=ROLE_ADMIN, is_active=True)
            user.set_password(settings.ADMIN_PASSWORD)
            db.session.add(user)
            db.session.commit()
            return
        if user.role != ROLE_ADMIN:
            user.role = ROLE_ADMIN
            db.session.commit()

    @staticmethod
    def login(data: LoginSchema) -> dict:
        user = User.query.filter_by(username=data.username).first()
        if user is None:
            check_password_hash(_DUMMY_PASSWORD_HASH, data.password)
            raise _Exception(400, '用户名或密码错误')
        if not user.check_password(data.password):
            raise _Exception(400, '用户名或密码错误')
        if not user.is_active:
            raise _Exception(400, '账号已停用')
        token = jwt_auth.create_token(user.id, user.username, user.role)
        return {'token': token, 'username': user.username, 'role': user.role}

    @staticmethod
    def change_password(user: User, data: ChangePasswordSchema) -> None:
        if not user.check_password(data.oldPassword):
            raise _Exception(400, '原密码错误')
        if data.oldPassword == data.newPassword:
            raise _Exception(422, '新密码不能与原密码相同')
        user.set_password(data.newPassword)
        db.session.commit()

    @staticmethod
    def list_users() -> list[dict]:
        return [u.to_public() for u in User.query.order_by(User.id.asc()).all()]

    @staticmethod
    def create_user(data: CreateUserSchema) -> dict:
        # role 已由 CreateUserSchema pattern 约束
        if User.query.filter_by(username=data.username).first():
            raise _Exception(400, '用户名已存在')
        user = User(username=data.username, role=data.role, is_active=True)
        user.set_password(data.password)
        db.session.add(user)
        db.session.commit()
        return user.to_public()

    @staticmethod
    def patch_user(user_id: int, data: PatchUserSchema) -> dict:
        user = db.session.get(User, user_id)
        if not user:
            raise _Exception(404, '用户不存在')

        new_role = data.role if data.role is not None else user.role
        new_active = data.isActive if data.isActive is not None else user.is_active
        if user.role == ROLE_ADMIN and (new_role != ROLE_ADMIN or not new_active):
            AuthService._assert_not_last_admin(exclude_id=user.id)

        if data.role is not None:
            user.role = data.role
        if data.isActive is not None:
            user.is_active = data.isActive
        if data.password:
            user.set_password(data.password)

        db.session.commit()
        return user.to_public()

    @staticmethod
    def _assert_not_last_admin(*, exclude_id: int) -> None:
        remaining = User.query.filter(
            User.role == ROLE_ADMIN,
            User.is_active.is_(True),
            User.id != exclude_id,
        ).count()
        if remaining < 1:
            raise _Exception(422, '不能停用或降级最后一个管理员')
