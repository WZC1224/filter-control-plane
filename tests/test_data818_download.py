"""Data818 下载相关：先写失败用例，再补实现（TDD）。"""
import httpx
import pytest

from config import settings
from app.utils.response import _Exception


@pytest.fixture()
def data818_settings(monkeypatch):
    monkeypatch.setattr(settings, 'DATA818_BASE_URL', 'http://data818.test')
    monkeypatch.setattr(settings, 'DATA818_TOKEN', 'test-token')
    monkeypatch.setattr(settings, 'DATA818_TIMEOUT', 5.0)


def test_filename_from_disposition_decodes_rfc5987(data818_settings):
    from app.adapters.data818 import Data818Adapter

    adapter = Data818Adapter()
    name = adapter._filename_from_disposition(
        "attachment; filename=\"fallback.csv\"; filename*=UTF-8''%E4%B8%AD%E6%96%87.csv",
        'x.csv',
    )
    assert name == '中文.csv'


def test_get_download_follows_result_url(data818_settings, monkeypatch):
    from app.adapters import data818 as data818_mod
    from app.adapters.data818 import Data818Adapter

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url.startswith('http://data818.test/api/filter/get_csv'):
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
                content=b'phone,status\n1,ok\n',
                headers={
                    'content-type': 'text/csv',
                    'content-disposition': 'attachment; filename="out.csv"',
                },
            )
        return httpx.Response(404, text='missing')

    transport = httpx.MockTransport(handler)
    real = httpx.Client(transport=transport, follow_redirects=True)

    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return real

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(data818_mod.httpx, 'Client', _Client)
    adapter = Data818Adapter()
    payload = adapter.get_download('TASK-1', fmt='csv')
    assert payload.content == b'phone,status\n1,ok\n'
    assert payload.filename == 'out.csv'


def test_get_download_json_business_error(data818_settings, monkeypatch):
    from app.adapters import data818 as data818_mod
    from app.adapters.data818 import Data818Adapter

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={'code': 201, 'success': False, 'message': '暂无数据', 'result': None},
            headers={'content-type': 'application/json'},
        )

    transport = httpx.MockTransport(handler)
    real = httpx.Client(transport=transport)

    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return real

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(data818_mod.httpx, 'Client', _Client)
    adapter = Data818Adapter()
    with pytest.raises(_Exception) as ei:
        adapter.get_download('TASK-1', fmt='csv')
    assert ei.value.code == 201
