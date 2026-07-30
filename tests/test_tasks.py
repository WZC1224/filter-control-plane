from io import BytesIO


def test_list_tasks(client, auth_headers):
    resp = client.get('/tasks', headers=auth_headers)
    data = resp.get_json()
    assert data['success'] is True
    assert data['result']['total'] >= 1
    assert data['result']['adapter'] == 'mock'


def test_create_task(client, auth_headers):
    resp = client.post(
        '/tasks',
        data={
            'filterType': 'wsValid',
            'countryCode': 'US',
            'describe': 'pytest',
            'file': (BytesIO(b'12015550100\n12015550101\n'), 'pytest.txt'),
        },
        content_type='multipart/form-data',
        headers=auth_headers,
    )
    data = resp.get_json()
    assert data['success'] is True
    assert str(data['result']['taskNo']).startswith('MOCK-')


def test_download_file_stream(client, auth_headers):
    resp = client.get('/tasks/MOCK-1001/download?format=csv', headers=auth_headers)
    assert resp.status_code == 200
    assert b'mock' in resp.data
    assert 'attachment' in resp.headers.get('Content-Disposition', '')
    assert not resp.data.startswith(b'{')


def test_download_not_ready_json_error(client, auth_headers):
    resp = client.get('/tasks/MOCK-1002/download', headers=auth_headers)
    data = resp.get_json()
    assert data['success'] is False
    assert data['code'] == 201


def test_list_requires_auth(client):
    resp = client.get('/tasks')
    data = resp.get_json()
    assert data['success'] is False
    assert data['code'] == 401


def test_download_txt_format(client, auth_headers):
    resp = client.get('/tasks/MOCK-1001/download?format=txt', headers=auth_headers)
    assert resp.status_code == 200
    assert b'MOCK-1001' in resp.data
    assert 'text/plain' in (resp.headers.get('Content-Type') or '')


def test_download_rejects_unsupported_format(client, auth_headers):
    resp = client.get('/tasks/MOCK-1001/download?format=foo', headers=auth_headers)
    data = resp.get_json()
    assert data['success'] is False
    assert data['code'] == 422


def test_download_xlsx_format(client, auth_headers):
    resp = client.get('/tasks/MOCK-1001/download?format=xlsx', headers=auth_headers)
    assert resp.status_code == 200
    assert resp.data.startswith(b'PK')


def test_download_invalid_format(client, auth_headers):
    resp = client.get('/tasks/MOCK-1001/download?format=invalid', headers=auth_headers)
    assert resp.status_code == 200
    assert b'invalid' in resp.data


def test_list_filter_by_status(client, auth_headers):
    resp = client.get('/tasks?taskStatus=-1', headers=auth_headers)
    data = resp.get_json()
    assert data['success'] is True
    assert all(row['status'] == -1 for row in data['result']['data'])


def test_list_filter_by_country(client, auth_headers):
    resp = client.get('/tasks?countryCode=US', headers=auth_headers)
    data = resp.get_json()
    assert data['success'] is True
    assert data['result']['total'] >= 1
    assert all(row['country'] == 'US' for row in data['result']['data'])


def test_meta_health(client):
    resp = client.get('/meta/health')
    data = resp.get_json()
    assert data['success'] is True
    assert data['result']['service'] == 'filter-control-plane'
    assert data['result']['adapter'] in ('mock', 'data818', 'data_center')
    assert data['result']['version']
    assert 'mock' in data['result']
    assert data['result']['tokenKind'] in ('none', 'agent', 'login', 'unknown')
    assert 'hasAgentToken' in data['result']
    assert 'hasApiKey' in data['result']
    assert data['result']['time']


def test_change_password(client, auth_headers):
    resp = client.post(
        '/auth/change-password',
        json={'oldPassword': 'admin123', 'newPassword': 'admin456'},
        headers=auth_headers,
    )
    assert resp.get_json()['success'] is True
    bad = client.post('/auth/login', json={'username': 'admin', 'password': 'admin123'})
    assert bad.get_json()['success'] is False
    ok = client.post('/auth/login', json={'username': 'admin', 'password': 'admin456'})
    assert ok.get_json()['success'] is True


def test_close_queued_task(client, auth_headers):
    resp = client.post('/tasks/MOCK-1004/close', headers=auth_headers)
    data = resp.get_json()
    assert data['success'] is True
    detail = client.get('/tasks/MOCK-1004', headers=auth_headers).get_json()
    assert detail['result']['status'] == -1


def test_close_rejects_non_queued(client, auth_headers):
    resp = client.post('/tasks/MOCK-1001/close', headers=auth_headers)
    assert resp.get_json()['success'] is False


def test_refund_completed(client, auth_headers):
    resp = client.post('/tasks/MOCK-1001/refund', headers=auth_headers)
    assert resp.get_json()['success'] is True
    detail = client.get('/tasks/MOCK-1001', headers=auth_headers).get_json()
    assert detail['result']['status'] == -1


def test_retry_failed(client, auth_headers):
    resp = client.post('/tasks/MOCK-1003/retry', headers=auth_headers)
    assert resp.get_json()['success'] is True
    detail = client.get('/tasks/MOCK-1003', headers=auth_headers).get_json()
    assert detail['result']['status'] == 2


def test_meta_statistics(client, auth_headers):
    resp = client.get('/meta/statistics', headers=auth_headers)
    data = resp.get_json()
    assert data['success'] is True
    assert 'series' in data['result']


def test_list_orders(client, auth_headers):
    resp = client.get('/orders', headers=auth_headers)
    data = resp.get_json()
    assert data['success'] is True
    assert data['result']['total'] >= 1
    assert data['result']['data'][0]['orderId']


def test_third_balances(client, auth_headers):
    resp = client.get('/meta/third-balances', headers=auth_headers)
    data = resp.get_json()
    assert data['success'] is True
    assert isinstance(data['result'], list)
    assert data['result'][0]['thirdSourceName']


def test_list_bills(client, auth_headers):
    resp = client.get('/bills', headers=auth_headers)
    data = resp.get_json()
    assert data['success'] is True
    assert data['result']['total'] >= 1
    assert data['result']['data'][0]['billId']


def test_list_bills_filter_ledger(client, auth_headers):
    resp = client.get('/bills?ledgerType=RECHARGE', headers=auth_headers)
    data = resp.get_json()
    assert data['success'] is True
    assert data['result']['total'] >= 1
    assert all(r['ledgerType'] == 'RECHARGE' for r in data['result']['data'])


def test_ledger_types(client, auth_headers):
    resp = client.get('/meta/ledger-types', headers=auth_headers)
    data = resp.get_json()
    assert data['success'] is True
    assert any(r['ledgerType'] == 'ORDER_PAY' for r in data['result'])


def test_list_notices(client, auth_headers):
    resp = client.get('/notices', headers=auth_headers)
    data = resp.get_json()
    assert data['success'] is True
    assert isinstance(data['result'], list)
    assert data['result'][0]['title']


def test_get_notice(client, auth_headers):
    resp = client.get('/notices/1', headers=auth_headers)
    data = resp.get_json()
    assert data['success'] is True
    assert data['result']['id'] == 1
    assert data['result']['title']


def test_meta_products(client, auth_headers):
    resp = client.get('/meta/products', headers=auth_headers)
    data = resp.get_json()
    assert data['success'] is True
    assert data['result'][0]['taskType']
    assert 'price' in data['result'][0]


def test_order_task_types(client, auth_headers):
    resp = client.get('/meta/order-task-types', headers=auth_headers)
    data = resp.get_json()
    assert data['success'] is True
    assert data['result'][0]['taskType']


def test_export_remaining_stream(client, auth_headers):
    resp = client.get('/tasks/MOCK-1001/export-remaining', headers=auth_headers)
    assert resp.status_code == 200
    assert b'remaining' in resp.data or b'1201555' in resp.data
    assert 'attachment' in resp.headers.get('Content-Disposition', '')


def test_export_remaining_not_ready(client, auth_headers):
    resp = client.get('/tasks/MOCK-1002/export-remaining', headers=auth_headers)
    data = resp.get_json()
    assert data['success'] is False
    assert data['code'] == 201

