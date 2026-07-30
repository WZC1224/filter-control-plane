from functools import wraps

from flask import g, request

from app.exts.extensions import db
from app.exts.jwt_auth import jwt_auth
from app.models import User
from app.utils.response import Fail


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        ok, payload = jwt_auth.verify(request.headers.get('Authorization', ''))
        if not ok:
            return Fail(code=401, message=str(payload))
        user = db.session.get(User, payload['user_id'])
        if not user:
            return Fail(code=401, message='user not found')
        g.user = user
        return fn(*args, **kwargs)

    return wrapper
