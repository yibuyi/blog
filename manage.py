# encoding=utf-8
import os
from app.models import Comment, User, Role, Permission, Follow, Post
from app import create_app, db
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

COV = None
if os.environ.get('FLASKY_COVERAGE'):
	import coverage

	COV = coverage.coverage(branch=True, include='app/*')
	COV.start()
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
	return dict(app=app, db=db, User=User, Role=Role, Follow=Follow, Permission=Permission, Post=Post, Comment=Comment)


manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():
	"""Run the unit tests."""
	if coverage and not os.environ.get('FLASKY_COVERAGE'):
		import sys
		os.environ['FLASKY_COVERAGE'] = '1'
		os.execvp(sys.executable, [sys.executable] + sys.argv)
	import unittest
	tests = unittest.TestLoader().discover('tests')
	unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def deploy():
	"""Run deployment tasks."""
	import flask_migrate
	from app.models import Role, User
	flask_migrate.upgrade()
	Role.insert_roles()
	User.add_self_follows()


if __name__ == '__main__':
	manager.run()
