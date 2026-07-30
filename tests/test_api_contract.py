from app.service.task import normalize_task


def test_normalize_task_prefers_camel_and_maps_snake():
    assert normalize_task({
        'task_no': 'T1',
        'task_name': 'n',
        'task_type': 'wsValid',
        'country_code': 'US',
        'status': 1,
        'effective_quantity': 9,
    }) == {
        'taskNo': 'T1',
        'taskName': 'n',
        'taskType': 'wsValid',
        'country': 'US',
        'status': 1,
        'progress': None,
        'effectiveQuantity': 9,
        'count': None,
        'createDate': '',
        'description': '',
    }


def test_create_requires_filter_type(client, auth_headers):
    from io import BytesIO

    resp = client.post(
        '/tasks',
        data={
            'filterType': '',
            'countryCode': 'US',
            'file': (BytesIO(b'1\n'), 'a.txt'),
        },
        content_type='multipart/form-data',
        headers=auth_headers,
    )
    data = resp.get_json()
    assert data['success'] is False
    assert data['code'] == 422
