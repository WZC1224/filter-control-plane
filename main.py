"""应用入口：开发 Flask debug；生产 waitress。"""
from app import create_app
from config import settings

app = create_app()

if __name__ == '__main__':
    host = settings.HOST
    port = settings.PORT
    if settings.is_production:
        from waitress import serve

        print(f'waitress serving on http://{host}:{port} (production)')
        serve(app, host=host, port=port, threads=8)
    else:
        app.run(host=host, port=port, debug=True)
