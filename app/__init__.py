from pathlib import Path

from flask import Flask, abort, send_from_directory
from flask_cors import CORS
from pydantic import ValidationError

from config import settings
from app.exts.extensions import db
from app.api import bp_list
from app.utils.response import Fail, Success, _Exception

WEB_DIST = Path(__file__).resolve().parent.parent / 'web' / 'dist'
_SPA_API_ROOTS = frozenset({
    'auth',
    'tasks',
    'meta',
    'orders',
    'bills',
    'notices',
    'users',
})


def create_app() -> Flask:
    settings.assert_production_safe()

    app = Flask(__name__)
    app.config.from_object(settings)

    origins = [o.strip() for o in settings.CORS_ORIGINS.split(',') if o.strip()]
    if origins:
        CORS(app, origins=origins, supports_credentials=True)
    elif not settings.is_production:
        # 开发：Vite :5173 直连 :5100 时需要
        CORS(app, supports_credentials=True)

    db.init_app(app)

    for bp in bp_list:
        app.register_blueprint(bp)

    @app.after_request
    def security_headers(resp):
        resp.headers.setdefault('X-Content-Type-Options', 'nosniff')
        resp.headers.setdefault('X-Frame-Options', 'DENY')
        resp.headers.setdefault('Referrer-Policy', 'same-origin')
        return resp

    @app.errorhandler(_Exception)
    def handle_biz(err: _Exception):
        return Fail(code=err.code, message=err.message)

    @app.errorhandler(ValidationError)
    def handle_validation(err: ValidationError):
        msg = '; '.join(f"{e['loc']}: {e['msg']}" for e in err.errors())
        return Fail(code=422, message=msg)

    if WEB_DIST.exists():
        @app.route('/')
        def spa_root():
            return send_from_directory(WEB_DIST, 'index.html')

        @app.route('/assets/<path:filename>')
        def spa_assets(filename: str):
            return send_from_directory(WEB_DIST / 'assets', filename)

        @app.route('/<path:path>')
        def spa_fallback(path: str):
            root = path.split('/', 1)[0]
            if root in _SPA_API_ROOTS:
                abort(404)
            candidate = WEB_DIST / path
            if candidate.is_file():
                return send_from_directory(WEB_DIST, path)
            return send_from_directory(WEB_DIST, 'index.html')
    else:
        @app.route('/')
        def index_hint():
            return Success(
                message='前端未构建。开发请启动 web: npm run dev（5173）',
                result={'dev': 'http://127.0.0.1:5173', 'build': 'cd web && npm run build'},
            )

    with app.app_context():
        from app import models  # noqa: F401
        db.create_all()
        from app.exts.schema_migrate import ensure_user_schema
        ensure_user_schema()
        from app.service.auth import AuthService
        AuthService.ensure_admin()

    return app
