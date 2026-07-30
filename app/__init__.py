from pathlib import Path

from flask import Flask, send_from_directory
from flask_cors import CORS
from pydantic import ValidationError

from config import settings
from app.exts.extensions import db
from app.api import bp_list
from app.utils.response import Fail, Success, _Exception

WEB_DIST = Path(__file__).resolve().parent.parent / 'web' / 'dist'


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(settings)
    CORS(app, supports_credentials=True)

    db.init_app(app)

    for bp in bp_list:
        app.register_blueprint(bp)

    @app.errorhandler(_Exception)
    def handle_biz(err: _Exception):
        return Fail(code=err.code, message=err.message)

    @app.errorhandler(ValidationError)
    def handle_validation(err: ValidationError):
        msg = '; '.join(f"{e['loc']}: {e['msg']}" for e in err.errors())
        return Fail(code=422, message=msg)

    if WEB_DIST.exists():
        @app.route('/')
        @app.route('/login')
        @app.route('/users')
        @app.route('/system')
        @app.route('/tasks')
        @app.route('/tasks/create')
        @app.route('/tasks/<path:_>')
        @app.route('/orders')
        @app.route('/products')
        @app.route('/bills')
        @app.route('/notices')
        @app.route('/notices/<path:_>')
        @app.route('/account')
        def spa_index(_=None):
            return send_from_directory(WEB_DIST, 'index.html')

        @app.route('/assets/<path:filename>')
        def spa_assets(filename: str):
            return send_from_directory(WEB_DIST / 'assets', filename)
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
