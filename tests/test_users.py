"""Phase 2：多账号 / 角色。"""


def _make_operator(client, auth_headers, username: str, password: str = 'op123456'):
    created = client.post(
        '/users',
        json={'username': username, 'password': password, 'role': 'operator'},
        headers=auth_headers,
    ).get_json()
    assert created['success'] is True, created
    login = client.post('/auth/login', json={'username': username, 'password': password}).get_json()
    assert login['success'] is True, login
    return {'Authorization': f"Bearer {login['result']['token']}"}, created['result']


def test_login_returns_role(client):
    resp = client.post('/auth/login', json={'username': 'admin', 'password': 'admin123'})
    data = resp.get_json()
    assert data['success'] is True
    assert data['result']['role'] == 'admin'


def test_me_returns_role(client, auth_headers):
    data = client.get('/auth/me', headers=auth_headers).get_json()
    assert data['success'] is True
    assert data['result']['role'] == 'admin'
    assert data['result']['username'] == 'admin'


def test_operator_cannot_list_users(client, auth_headers):
    op_headers, _ = _make_operator(client, auth_headers, 'op1')
    resp = client.get('/users', headers=op_headers).get_json()
    assert resp['success'] is False
    assert resp['code'] == 403


def test_admin_can_create_and_list_users(client, auth_headers):
    _, created = _make_operator(client, auth_headers, 'op2')
    assert created['username'] == 'op2'
    assert created['role'] == 'operator'
    assert created['isActive'] is True

    listing = client.get('/users', headers=auth_headers).get_json()
    assert listing['success'] is True
    names = {u['username'] for u in listing['result']}
    assert 'admin' in names and 'op2' in names


def test_inactive_user_cannot_login(client, auth_headers):
    _, created = _make_operator(client, auth_headers, 'op3')
    patched = client.patch(
        f"/users/{created['id']}",
        json={'isActive': False},
        headers=auth_headers,
    ).get_json()
    assert patched['success'] is True

    login = client.post('/auth/login', json={'username': 'op3', 'password': 'op123456'}).get_json()
    assert login['success'] is False
    assert login['code'] == 400


def test_cannot_deactivate_last_admin(client, auth_headers):
    admin_list = client.get('/users', headers=auth_headers).get_json()['result']
    admin = next(u for u in admin_list if u['username'] == 'admin')
    resp = client.patch(
        f"/users/{admin['id']}",
        json={'isActive': False},
        headers=auth_headers,
    ).get_json()
    assert resp['success'] is False
    assert resp['code'] == 422


def test_operator_cannot_close_task(client, auth_headers):
    op_headers, _ = _make_operator(client, auth_headers, 'op4')
    resp = client.post('/tasks/MOCK-1004/close', headers=op_headers).get_json()
    assert resp['success'] is False
    assert resp['code'] == 403


def test_operator_cannot_third_balances(client, auth_headers):
    op_headers, _ = _make_operator(client, auth_headers, 'op5')
    resp = client.get('/meta/third-balances', headers=op_headers).get_json()
    assert resp['success'] is False
    assert resp['code'] == 403


def test_admin_can_third_balances(client, auth_headers):
    resp = client.get('/meta/third-balances', headers=auth_headers).get_json()
    assert resp['success'] is True
    assert isinstance(resp['result'], list)
