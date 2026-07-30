"""Phase 2：多账号 / 角色（先写失败用例）。"""


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
    created = client.post(
        '/users',
        json={'username': 'op1', 'password': 'op123456', 'role': 'operator'},
        headers=auth_headers,
    ).get_json()
    assert created['success'] is True

    login = client.post('/auth/login', json={'username': 'op1', 'password': 'op123456'}).get_json()
    op_headers = {'Authorization': f"Bearer {login['result']['token']}"}
    resp = client.get('/users', headers=op_headers).get_json()
    assert resp['success'] is False
    assert resp['code'] == 403


def test_admin_can_create_and_list_users(client, auth_headers):
    created = client.post(
        '/users',
        json={'username': 'op2', 'password': 'op123456', 'role': 'operator'},
        headers=auth_headers,
    ).get_json()
    assert created['success'] is True
    assert created['result']['username'] == 'op2'
    assert created['result']['role'] == 'operator'
    assert created['result']['isActive'] is True

    listing = client.get('/users', headers=auth_headers).get_json()
    assert listing['success'] is True
    names = {u['username'] for u in listing['result']}
    assert 'admin' in names and 'op2' in names


def test_inactive_user_cannot_login(client, auth_headers):
    created = client.post(
        '/users',
        json={'username': 'op3', 'password': 'op123456', 'role': 'operator'},
        headers=auth_headers,
    ).get_json()
    uid = created['result']['id']
    patched = client.patch(
        f'/users/{uid}',
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
    client.post(
        '/users',
        json={'username': 'op4', 'password': 'op123456', 'role': 'operator'},
        headers=auth_headers,
    )
    login = client.post('/auth/login', json={'username': 'op4', 'password': 'op123456'}).get_json()
    op_headers = {'Authorization': f"Bearer {login['result']['token']}"}
    resp = client.post('/tasks/MOCK-1004/close', headers=op_headers).get_json()
    assert resp['success'] is False
    assert resp['code'] == 403


def test_operator_cannot_third_balances(client, auth_headers):
    client.post(
        '/users',
        json={'username': 'op5', 'password': 'op123456', 'role': 'operator'},
        headers=auth_headers,
    )
    login = client.post('/auth/login', json={'username': 'op5', 'password': 'op123456'}).get_json()
    op_headers = {'Authorization': f"Bearer {login['result']['token']}"}
    resp = client.get('/meta/third-balances', headers=op_headers).get_json()
    assert resp['success'] is False
    assert resp['code'] == 403


def test_admin_can_third_balances(client, auth_headers):
    resp = client.get('/meta/third-balances', headers=auth_headers).get_json()
    assert resp['success'] is True
    assert isinstance(resp['result'], list)
