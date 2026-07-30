def test_login_ok(client):
    resp = client.post('/auth/login', json={'username': 'admin', 'password': 'admin123'})
    data = resp.get_json()
    assert data['success'] is True
    assert data['result']['token']
    assert data['result']['username'] == 'admin'


def test_login_fail(client):
    resp = client.post('/auth/login', json={'username': 'admin', 'password': 'wrong'})
    data = resp.get_json()
    assert data['success'] is False
    assert data['code'] == 400
