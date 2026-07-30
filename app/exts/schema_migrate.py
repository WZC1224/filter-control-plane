"""SQLite 轻量列迁移：create_all 不改已有表。"""
from __future__ import annotations

from sqlalchemy import inspect, text

from app.exts.extensions import db
from app.models import ROLE_ADMIN


def ensure_user_schema() -> None:
    engine = db.engine
    insp = inspect(engine)
    if 'users' not in insp.get_table_names():
        return
    cols = {c['name'] for c in insp.get_columns('users')}
    with engine.begin() as conn:
        if 'role' not in cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(32) NOT NULL DEFAULT 'operator'"))
        if 'is_active' not in cols:
            conn.execute(text('ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1'))
        # 种子管理员补齐角色（历史库）
        conn.execute(
            text("UPDATE users SET role = :role WHERE username = :u AND (role IS NULL OR role = '')"),
            {'role': ROLE_ADMIN, 'u': _admin_username()},
        )


def _admin_username() -> str:
    from config import settings

    return settings.ADMIN_USERNAME
