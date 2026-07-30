from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app.exts.extensions import db

ROLE_ADMIN = 'admin'
ROLE_OPERATOR = 'operator'
VALID_ROLES = frozenset({ROLE_ADMIN, ROLE_OPERATOR})


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, comment='登录名')
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default=ROLE_OPERATOR, comment='admin|operator')
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_public(self) -> dict:
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'isActive': bool(self.is_active),
            'createdAt': self.created_at.isoformat(sep=' ', timespec='seconds') if self.created_at else None,
        }
