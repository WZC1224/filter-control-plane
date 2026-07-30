"""登录限流与代理头策略。"""

from app.exts.login_rate_limit import login_limiter
from config import settings


def test_login_rate_limit_blocks_after_max(client, monkeypatch):
    monkeypatch.setattr(settings, 'LOGIN_RATE_LIMIT_MAX', 3)
    monkeypatch.setattr(settings, 'LOGIN_RATE_WINDOW_SECONDS', 60.0)
    login_limiter.reset()

    for _ in range(3):
        resp = client.post('/auth/login', json={'username': 'admin', 'password': 'wrong'})
        assert resp.get_json()['code'] == 400

    blocked = client.post('/auth/login', json={'username': 'admin', 'password': 'admin123'})
    body = blocked.get_json()
    assert body['success'] is False
    assert body['code'] == 429


def test_login_rate_limit_ignores_xff_by_default(client, monkeypatch):
    monkeypatch.setattr(settings, 'LOGIN_RATE_LIMIT_MAX', 2)
    monkeypatch.setattr(settings, 'LOGIN_RATE_WINDOW_SECONDS', 60.0)
    monkeypatch.setattr(settings, 'TRUST_PROXY_HEADERS', False)
    login_limiter.reset()

    for i in range(2):
        resp = client.post(
            '/auth/login',
            json={'username': 'admin', 'password': 'wrong'},
            headers={'X-Forwarded-For': f'203.0.113.{i}'},
        )
        assert resp.get_json()['code'] == 400

    blocked = client.post(
        '/auth/login',
        json={'username': 'admin', 'password': 'wrong'},
        headers={'X-Forwarded-For': '203.0.113.99'},
    )
    assert blocked.get_json()['code'] == 429


def test_login_rate_limit_uses_xff_when_trusted(client, monkeypatch):
    monkeypatch.setattr(settings, 'LOGIN_RATE_LIMIT_MAX', 1)
    monkeypatch.setattr(settings, 'LOGIN_RATE_WINDOW_SECONDS', 60.0)
    monkeypatch.setattr(settings, 'TRUST_PROXY_HEADERS', True)
    login_limiter.reset()

    first = client.post(
        '/auth/login',
        json={'username': 'admin', 'password': 'wrong'},
        headers={'X-Forwarded-For': '198.51.100.1'},
    )
    assert first.get_json()['code'] == 400

    other_ip = client.post(
        '/auth/login',
        json={'username': 'admin', 'password': 'wrong'},
        headers={'X-Forwarded-For': '198.51.100.2'},
    )
    assert other_ip.get_json()['code'] == 400

    same_ip = client.post(
        '/auth/login',
        json={'username': 'admin', 'password': 'wrong'},
        headers={'X-Forwarded-For': '198.51.100.1'},
    )
    assert same_ip.get_json()['code'] == 429
