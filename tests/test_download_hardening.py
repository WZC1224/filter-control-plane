from app.adapters.base import FilePayload
from app.service.task import resolve_download_mimetype, safe_download_name
from app.utils.response import _Exception
import pytest


def test_safe_download_name_strips_path_and_quotes():
    assert safe_download_name('../../evil/out.csv', 'x.csv') == 'out.csv'
    assert '"' not in safe_download_name('a"b.csv', 'x.csv')
    assert safe_download_name('中文.csv', 'x.csv') == '中文.csv'
    assert safe_download_name('', 'fb.csv') == 'fb.csv'


def test_resolve_mimetype_rejects_json():
    with pytest.raises(_Exception) as ei:
        resolve_download_mimetype('application/json; charset=utf-8')
    assert ei.value.code == 502


def test_resolve_mimetype_empty_falls_back():
    assert resolve_download_mimetype('') == 'application/octet-stream'
    assert resolve_download_mimetype('; charset=utf-8') == 'application/octet-stream'


def test_download_format_strips_whitespace(client, auth_headers):
    resp = client.get('/tasks/MOCK-1001/download?format=%20csv%20', headers=auth_headers)
    assert resp.status_code == 200
    assert b'mock' in resp.data


def test_download_rejects_json_content_type(client, auth_headers, monkeypatch):
    class BadAdapter:
        def get_download(self, task_no, *, fmt='csv'):
            return FilePayload(b'{"ok":true}', 'application/json', 'x.json')

    monkeypatch.setattr('app.service.task.get_adapter', lambda: BadAdapter())
    resp = client.get('/tasks/MOCK-1001/download', headers=auth_headers)
    data = resp.get_json()
    assert data['success'] is False
    assert data['code'] == 502


def test_download_empty_mime_uses_octet_stream(client, auth_headers, monkeypatch):
    class BadAdapter:
        def get_download(self, task_no, *, fmt='csv'):
            return FilePayload(b'hello', '; charset=utf-8', 'a.csv')

    monkeypatch.setattr('app.service.task.get_adapter', lambda: BadAdapter())
    resp = client.get('/tasks/MOCK-1001/download', headers=auth_headers)
    assert resp.status_code == 200
    assert resp.data == b'hello'
    assert 'octet-stream' in (resp.headers.get('Content-Type') or '')
