"""DataCenter 适配器：X-Api-Key / JWT 分流 + 公告软降级。"""
from __future__ import annotations

import io

import httpx
import pytest

from config import settings
from app.utils.response import _Exception


@pytest.fixture()
def data_center_settings(monkeypatch):
    monkeypatch.setattr(settings, 'DATA_CENTER_BASE_URL', 'http://dc.test')
    monkeypatch.setattr(settings, 'DATA_CENTER_API_KEY', 'dc-api-key')
    monkeypatch.setattr(settings, 'DATA_CENTER_TOKEN', 'dc-login-tok')
    monkeypatch.setattr(settings, 'DATA_CENTER_TIMEOUT', 5.0)


def _mock_client(monkeypatch, handler, *, follow_redirects: bool = False):
    from app.adapters import filter_http as fh

    transport = httpx.MockTransport(handler)
    real = httpx.Client(transport=transport, follow_redirects=follow_redirects)

    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return real

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(fh.httpx, 'Client', _Client)


def test_filter_path_uses_x_api_key(data_center_settings, monkeypatch):
    from app.adapters.data_center import DataCenterAdapter

    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen['api_key'] = request.headers.get('x-api-key', '')
        seen['auth'] = request.headers.get('authorization', '')
        return httpx.Response(
            200,
            json={'code': 200, 'success': True, 'message': 'ok', 'result': 12.5},
            headers={'content-type': 'application/json'},
        )

    _mock_client(monkeypatch, handler)
    out = DataCenterAdapter().get_balance()
    assert out['balance'] == 12.5
    assert out['adapter'] == 'data_center'
    assert seen['api_key'] == 'dc-api-key'
    assert seen['auth'] == ''


def test_business_path_uses_bearer(data_center_settings, monkeypatch):
    from app.adapters.data_center import DataCenterAdapter

    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen['api_key'] = request.headers.get('x-api-key', '')
        seen['auth'] = request.headers.get('authorization', '')
        return httpx.Response(
            200,
            json={
                'code': 200,
                'success': True,
                'message': 'ok',
                'result': {'pageNo': 1, 'pageSize': 20, 'total': 0, 'data': []},
            },
            headers={'content-type': 'application/json'},
        )

    _mock_client(monkeypatch, handler)
    out = DataCenterAdapter().list_tasks(page_no=1, page_size=20)
    assert out['adapter'] == 'data_center'
    assert seen['auth'] == 'Bearer dc-login-tok'
    assert seen['api_key'] == ''


def test_create_task_multipart_with_api_key(data_center_settings, monkeypatch):
    from app.adapters.data_center import DataCenterAdapter

    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen['api_key'] = request.headers.get('x-api-key', '')
        seen['ct'] = request.headers.get('content-type', '')
        return httpx.Response(
            200,
            json={'code': 200, 'success': True, 'message': 'ok', 'result': {'taskNo': 'DC-1'}},
            headers={'content-type': 'application/json'},
        )

    _mock_client(monkeypatch, handler)
    out = DataCenterAdapter().create_task(
        filter_type='wsValid',
        country_code='AD',
        describe='t',
        filename='a.txt',
        file_obj=io.BytesIO(b'37670000001\n'),
    )
    assert out['taskNo'] == 'DC-1'
    assert seen['api_key'] == 'dc-api-key'
    assert seen['ct'].startswith('multipart/form-data')


def test_get_download_follows_result_url(data_center_settings, monkeypatch):
    from app.adapters.data_center import DataCenterAdapter

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url.startswith('http://dc.test/api/filter/get_csv'):
            assert request.headers.get('x-api-key') == 'dc-api-key'
            return httpx.Response(
                200,
                json={
                    'code': 200,
                    'success': True,
                    'message': 'ok',
                    'result': {'resultUrl': 'http://cdn.test/out.csv'},
                },
                headers={'content-type': 'application/json'},
            )
        if url.startswith('http://cdn.test/out.csv'):
            return httpx.Response(
                200,
                content=b'a,b\n1,2\n',
                headers={
                    'content-type': 'text/csv',
                    'content-disposition': 'attachment; filename="out.csv"',
                },
            )
        return httpx.Response(404, text='missing')

    _mock_client(monkeypatch, handler, follow_redirects=True)
    payload = DataCenterAdapter().get_download('T1', fmt='csv')
    assert payload.content == b'a,b\n1,2\n'
    assert payload.filename == 'out.csv'


def test_list_notices_empty(data_center_settings):
    from app.adapters.data_center import DataCenterAdapter

    assert DataCenterAdapter().list_notices() == []


def test_get_notice_not_supported(data_center_settings):
    from app.adapters.data_center import DataCenterAdapter

    with pytest.raises(_Exception) as ei:
        DataCenterAdapter().get_notice('1')
    assert ei.value.code == 404


def test_adapter_name_auto_prefers_data_center(monkeypatch):
    monkeypatch.setattr(settings, 'DOWNSTREAM', 'auto')
    monkeypatch.setattr(settings, 'DATA_CENTER_BASE_URL', 'http://dc.test')
    monkeypatch.setattr(settings, 'DATA_CENTER_API_KEY', 'k')
    monkeypatch.setattr(settings, 'DATA_CENTER_TOKEN', 't')
    monkeypatch.setattr(settings, 'DATA818_BASE_URL', 'http://818.test')
    monkeypatch.setattr(settings, 'DATA818_TOKEN', '818t')
    assert settings.adapter_name == 'data_center'


def test_adapter_name_explicit_data818(monkeypatch):
    monkeypatch.setattr(settings, 'DOWNSTREAM', 'data818')
    monkeypatch.setattr(settings, 'DATA818_BASE_URL', 'http://818.test')
    monkeypatch.setattr(settings, 'DATA818_TOKEN', '818t')
    monkeypatch.setattr(settings, 'DATA_CENTER_BASE_URL', 'http://dc.test')
    monkeypatch.setattr(settings, 'DATA_CENTER_API_KEY', 'k')
    monkeypatch.setattr(settings, 'DATA_CENTER_TOKEN', 't')
    assert settings.adapter_name == 'data818'


def test_adapter_name_explicit_missing_creds(monkeypatch):
    monkeypatch.setattr(settings, 'DOWNSTREAM', 'data_center')
    monkeypatch.setattr(settings, 'DATA_CENTER_BASE_URL', '')
    monkeypatch.setattr(settings, 'DATA_CENTER_API_KEY', '')
    monkeypatch.setattr(settings, 'DATA_CENTER_TOKEN', '')
    with pytest.raises(RuntimeError, match='DATA_CENTER'):
        _ = settings.adapter_name
