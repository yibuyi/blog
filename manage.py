# coding=utf-8
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
	if COV:
		COV.stop()
		COV.save()
		print('Coverage Summary')
		COV.report()
		basedir = os.path.abspath(os.path.dirname(__file__))
		covdir = os.path.join(basedir, 'tmp/coverage')
		COV.html_report(directory=covdir)
		print('HTML version: file//%s/index.html' % covdir)
		COV.erase()


@manager.command
def profile(length=25, profile_dir=None):
	"""Start the application under the code profiler."""
	from werkzeug.contrib.profiler import ProfilerMiddleware
	app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length], profile_dir=profile_dir)
	app.run()


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
