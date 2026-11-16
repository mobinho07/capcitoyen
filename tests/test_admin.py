import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app as module
from werkzeug.security import generate_password_hash, check_password_hash


class AdminTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.patcher = patch.object(module, 'USERS_FILE', Path(self.tmp.name) / 'users.json')
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        module.app.config.update(TESTING=True)
        module.write_json(module.USERS_FILE, {
            'admin': dict(name='Admin', password=generate_password_hash('secret123'), role='superadmin'),
            'learner': dict(name='Élève', password=generate_password_hash('secret123'),
                            results={'m1': [dict(percent=80)]}, exams=[dict(percent=60)]),
        })
        self.admin = module.app.test_client()
        self.user = module.app.test_client()
        for client, username in [(self.admin, 'admin'), (self.user, 'learner')]:
            self.assertEqual(client.post('/api/login', json=dict(username=username, password='secret123')).status_code, 200)
        self.headers = {'X-CSRF-Token': self.admin.get('/api/dashboard').json['csrf']}

    def test_access_and_csrf(self):
        self.assertEqual(module.app.test_client().get('/api/admin/users').status_code, 401)
        self.assertEqual(self.user.get('/api/admin/users').status_code, 403)
        for method in ('post', 'patch', 'delete'):
            url = '/api/admin/users' if method == 'post' else '/api/admin/users/learner'
            self.assertEqual(getattr(self.user, method)(url, json={}).status_code, 403)
            self.assertEqual(getattr(self.admin, method)(url, json={}).status_code, 403)
        data = self.admin.get('/api/admin/users').json
        self.assertEqual(data['stats'], dict(total=2, active=2, attempts=1, exams=1))
        learner = next(u for u in data['users'] if u['username'] == 'learner')
        self.assertEqual(learner['average'], 70)
        self.assertNotIn('password', learner)

    def test_reset_and_disable_invalidate_sessions(self):
        url = '/api/admin/users/learner'
        self.assertEqual(self.admin.patch(url, json={'password': 'newpass123'}, headers=self.headers).status_code, 200)
        self.assertEqual(self.user.get('/api/dashboard').status_code, 401)
        self.assertEqual(self.user.post('/api/login', json=dict(username='learner', password='secret123')).status_code, 401)
        self.assertEqual(self.user.post('/api/login', json=dict(username='learner', password='newpass123')).status_code, 200)
        saved = module.read_json(module.USERS_FILE, {})['learner']
        self.assertTrue(check_password_hash(saved['password'], 'newpass123'))
        self.assertEqual(saved['exams'], [dict(percent=60)])
        self.admin.patch(url, json={'active': False}, headers=self.headers)
        self.assertEqual(self.user.get('/api/dashboard').status_code, 401)
        self.assertEqual(self.user.post('/api/login', json=dict(username='learner', password='newpass123')).status_code, 401)
        self.admin.patch(url, json={'active': True}, headers=self.headers)
        self.assertEqual(self.user.get('/api/dashboard').status_code, 401)

    def test_management_and_self_protection(self):
        self.assertEqual(self.admin.post('/api/admin/users', json=dict(name='New User', username='new', password='abcdef'), headers=self.headers).status_code, 201)
        self.assertEqual(self.admin.post('/api/admin/users', json=dict(name='New User', username='new', password='abcdef'), headers=self.headers).status_code, 409)
        url = '/api/admin/users/new'
        self.assertEqual(self.admin.patch(url, json=dict(name='New Name', role='superadmin'), headers=self.headers).status_code, 200)
        self.assertEqual(module.read_json(module.USERS_FILE, {})['new']['role'], 'superadmin')
        for payload in ({'role': 'user'}, {'active': False}, {'password': 'short'}, {'role': 'invalid'}):
            self.assertEqual(self.admin.patch('/api/admin/users/admin', json=payload, headers=self.headers).status_code, 400)
        self.assertEqual(self.admin.delete('/api/admin/users/admin', headers=self.headers).status_code, 400)
        self.assertEqual(self.admin.delete(url, headers=self.headers).status_code, 200)
        self.assertEqual(self.admin.patch(url, json={'name': 'Missing'}, headers=self.headers).status_code, 404)

    def test_public_registration_cannot_grant_role(self):
        client = module.app.test_client()
        response = client.post('/api/register', json=dict(name='Public', username='public', password='abcdef', role='superadmin'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(client.get('/api/admin/users').status_code, 403)

    def test_cli_bootstrap(self):
        runner = module.app.test_cli_runner()
        result = runner.invoke(args=['create-superadmin', 'owner', '--name', 'Owner', '--password', 'abcdef'])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(module.read_json(module.USERS_FILE, {})['owner']['role'], 'superadmin')
        self.assertNotEqual(runner.invoke(args=['create-superadmin', 'owner', '--name', 'Owner', '--password', 'abcdef']).exit_code, 0)


if __name__ == '__main__':
    unittest.main()
