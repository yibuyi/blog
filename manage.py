# coding=utf-8
import os
from app.models import Comment, User, Role, Permission, Follow, Post
from app import create_app, db
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

if os.path.exists('.env'):
	print('Importing environment from .env...')
	for line in open('.env'):
		var = line.strip().split('=')
		if len(var) == 2:
			os.environ[var[0]] = var[1]

app = create_app(os.getenv('FLASKY_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app)


def make_shell_context():
	return dict(app=app, db=db, User=User, Role=Role, Follow=Follow, Permission=Permission, Post=Post, Comment=Comment)


manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():
	import unittest
	tests = unittest.TestLoader().discover('tests')
	unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def deploy():
	import flask_migrate
	from app.models import Role, User
	flask_migrate.upgrade()


# Role.insert_roles()
# User.add_self_follows()

if __name__ == '__main__':
	manager.run()
