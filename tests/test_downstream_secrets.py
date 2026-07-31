"""下游凭证覆盖：admin 可写、脱敏可读、热清 adapter。"""

import json

from config import settings
from app.adapters import get_adapter
from app.exts import downstream_secrets as ds


def test_downstream_secrets_admin_only(client, auth_headers):
    deny = client.get('/meta/downstream-secrets')
    assert deny.get_json()['code'] == 401

    # operator
    created = client.post(
        '/users',
        json={'username': 'op_sec', 'password': 'op123456', 'role': 'operator'},
        headers=auth_headers,
    ).get_json()
    assert created['success']
    login = client.post(
        '/auth/login', json={'username': 'op_sec', 'password': 'op123456'}
    ).get_json()
    op_h = {'Authorization': f"Bearer {login['result']['token']}"}
    forbidden = client.get('/meta/downstream-secrets', headers=op_h)
    assert forbidden.get_json()['code'] == 403


def test_downstream_secrets_put_masks_and_hot_applies(client, auth_headers, tmp_path, monkeypatch):
    # 伪造带 exp 的 JWT payload（不验签，仅脱敏/kind）
    # header.payload.sig — payload={"exp": 2000000000}
    import base64

    def b64(obj: dict) -> str:
        raw = json.dumps(obj, separators=(',', ':')).encode()
        return base64.urlsafe_b64encode(raw).decode().rstrip('=')

    fake = f'{b64({"alg":"none"})}.{b64({"exp": 2000000000})}.x'
    agent = f'{b64({"alg":"none"})}.{b64({"user_id": 1})}.y'

    before = client.get('/meta/downstream-secrets', headers=auth_headers).get_json()
    assert before['success'] is True
    assert before['result']['data818Token']['configured'] is False

    put = client.put(
        '/meta/downstream-secrets',
        json={'data818Token': f'Bearer {fake}', 'data818AgentToken': agent},
        headers=auth_headers,
    ).get_json()
    assert put['success'] is True
    assert put['result']['data818Token']['configured'] is True
    assert put['result']['data818Token']['kind'] == 'login'
    assert put['result']['data818Token']['source'] == 'file'
    assert put['result']['data818Token']['exp']
    assert fake not in json.dumps(put)
    assert put['result']['data818Token']['masked'].startswith(fake[:6])

    assert settings.DATA818_TOKEN == fake
    assert settings.DATA818_AGENT_TOKEN == agent
    assert ds.SECRETS_PATH.is_file()

    get_adapter.cache_clear()
    # 清覆盖回退空底
    cleared = client.put(
        '/meta/downstream-secrets',
        json={'data818Token': '', 'data818AgentToken': ''},
        headers=auth_headers,
    ).get_json()
    assert cleared['success'] is True
    assert settings.DATA818_TOKEN == ''
    assert cleared['result']['data818Token']['configured'] is False
