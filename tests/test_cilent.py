import re
import unittest
from app import create_app, db
from app.models import User, Role
from flask import url_for


class FlaskClientTestCase(unittest.TestCase):
	def setUp(self):
		self.app = create_app('testing')
		self.app_context = self.app.app_context()
		self.app_context.push()
		db.create_all()
		Role.insert_roles()
		self.client = self.app.test_client(use_cookies=True)

	def tearDown(self):
		db.session.remove()
		db.drop_all()
		self.app_context.pop()

	def test_home_page(self):
		response = self.client.get(url_for('main.index'))
		self.assertTrue('Stranger' in response.get_data(as_text=True))

	def test_register_and_login(self):
		# 注册账户
		response = self.client.post(url_for('auth.register'), data={
			'email': 'john1@example.com',
			'username': 'john1',
			'password': 'cat',
			'password2': 'cat'
		})
		self.assertTrue(response.status_code == 302)

		# 登录账户
		response = self.client.post(url_for('auth.login'), data={
			'email': 'john1@example.com',
			'password': 'cat'
		}, follow_redirects=True)
		self.assertTrue(re.search(b'hello,\s+john1!', response.data))
		self.assertTrue(b'你还没有确认你的账户' in response.adta)

		# 发送确认令牌
		user = User.query.filter_by(email='john@example.com').first()
		token = user.generate_confirmation_token()
		response = self.client.get(url_for('auth.confirm', token=token),
								   follow_redirects=True)
		self.assertTrue(
			b'你还没有确认你的账户' in response.data)

		# 退出登录
		response = self.client.get(url_for('auth.logout'), follow_redirects=True)
		self.assertTrue(b'你已经退出登录' in response.data)
