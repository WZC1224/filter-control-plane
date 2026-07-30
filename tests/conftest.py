import pytest

from config import settings
from app.adapters import get_adapter


@pytest.fixture()
def app(tmp_path, monkeypatch):
    db_file = tmp_path / 'test.db'
    uri = 'sqlite:///' + str(db_file).replace('\\', '/')
    monkeypatch.setattr(settings, 'SQLALCHEMY_DATABASE_URI', uri)
    monkeypatch.setattr(settings, 'DOWNSTREAM', 'auto')
    monkeypatch.setattr(settings, 'DATA818_BASE_URL', '')
    monkeypatch.setattr(settings, 'DATA818_TOKEN', '')
    monkeypatch.setattr(settings, 'DATA818_AGENT_TOKEN', '')
    monkeypatch.setattr(settings, 'DATA_CENTER_BASE_URL', '')
    monkeypatch.setattr(settings, 'DATA_CENTER_API_KEY', '')
    monkeypatch.setattr(settings, 'DATA_CENTER_TOKEN', '')
    monkeypatch.setattr(settings, 'ADMIN_USERNAME', 'admin')
    monkeypatch.setattr(settings, 'ADMIN_PASSWORD', 'admin123')
    get_adapter.cache_clear()

    from app import create_app

    application = create_app()
    application.config['TESTING'] = True
    yield application
    get_adapter.cache_clear()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_headers(client):
    resp = client.post('/auth/login', json={'username': 'admin', 'password': 'admin123'})
    data = resp.get_json()
    assert data['success'], data
    token = data['result']['token']
    return {'Authorization': f'Bearer {token}'}
