from app.exts.extensions import db
from app.exts.jwt_auth import jwt_auth
from app.models import User
from app.schema.auth import ChangePasswordSchema, LoginSchema
from app.utils.response import _Exception
from config import settings


class AuthService:
    @staticmethod
    def ensure_admin() -> None:
        if User.query.filter_by(username=settings.ADMIN_USERNAME).first():
            return
        user = User(username=settings.ADMIN_USERNAME)
        user.set_password(settings.ADMIN_PASSWORD)
        db.session.add(user)
        db.session.commit()

    @staticmethod
    def login(data: LoginSchema) -> dict:
        user = User.query.filter_by(username=data.username).first()
        if not user or not user.check_password(data.password):
            raise _Exception(400, '用户名或密码错误')
        token = jwt_auth.create_token(user.id, user.username)
        return {'token': token, 'username': user.username}

    @staticmethod
    def change_password(user: User, data: ChangePasswordSchema) -> None:
        if not user.check_password(data.oldPassword):
            raise _Exception(400, '原密码错误')
        if data.oldPassword == data.newPassword:
            raise _Exception(422, '新密码不能与原密码相同')
        user.set_password(data.newPassword)
        db.session.commit()
