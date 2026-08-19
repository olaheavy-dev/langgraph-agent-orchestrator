def test_health_needs_no_key(client):
    assert client.get('/health').json() == {'status': 'ok'}


def test_create_and_list(client, key):
    created = client.post('/tasks', json={'title': 'write the runbook'}, headers={'X-API-Key': key})
    assert created.status_code == 201
    assert created.json()['status'] == 'open'

    listed = client.get('/tasks', headers={'X-API-Key': key})
    assert [task['title'] for task in listed.json()] == ['write the runbook']


def test_blank_title_is_rejected(client, key):
    response = client.post('/tasks', json={'title': '   '}, headers={'X-API-Key': key})
    assert response.status_code == 400


def test_tasks_are_scoped_to_the_key_that_made_them(client, key, other_key):
    client.post('/tasks', json={'title': 'mine'}, headers={'X-API-Key': key})
    assert client.get('/tasks', headers={'X-API-Key': other_key}).json() == []


def test_complete_marks_done(client, key):
    task = client.post('/tasks', json={'title': 'ship'}, headers={'X-API-Key': key}).json()
    done = client.post(f'/tasks/{task["id"]}/complete', headers={'X-API-Key': key})
    assert done.json()['status'] == 'done'


def test_completing_another_keys_task_is_a_404(client, key, other_key):
    task = client.post('/tasks', json={'title': 'mine'}, headers={'X-API-Key': key}).json()
    response = client.post(f'/tasks/{task["id"]}/complete', headers={'X-API-Key': other_key})
    assert response.status_code == 404
