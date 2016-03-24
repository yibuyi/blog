#!/usr/bin/python
# -*- coding: ascii -*-
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
	MAIL_SERVER = 'smtp.163.com'
	MAIL_PORT = 465
	MAIL_USE_TLS = False
	MAIL_USE_SSL = True
	MAIL_USERNAME = os.environ.get('MAIL_USERNAME')  # 'li12qiang345@163.com'
	MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')  # 'abcde12345'
	FLASKY_MAIL_SUBJECT_PREFIX = ['Flasky']
	FLASKY_MAIL_SENDER = '<li12qiang345@163.com>'
	FLASKY_ADMIN = 'li12qiang345@163.com'
	SSL_DISABLE = False
	SQLALCHEMY_COMMIT_ON_TEARDOWN = True
	SQLALCHEMY_RECORD_QUERIES = True
	FLASKY_POSTS_PER_PAGE = 5
	FLASKY_FOLLOWERS_PER_PAGE = 50
	FLASKY_COMMENTS_PER_PAGE = 20
	FLASKY_SLOW_DB_QUERY_TIME = 0.5

	@staticmethod
	def init_app(app):
		pass


class DevelopmentConfig(Config):
	DEBUG = True
	SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
							  'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
	TESTING = True
	SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
							  'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')
	WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
	SQLALCHEMY_DATABASW_URI = os.environ.get('TEST_DATABASE_URL') or \
							  'sqlite:///' + os.path.join(basedir, 'data.sqlite')

	@classmethod
	def init_app(cls, app):
		Config.init_app(app)

		# email errors to the administrators
		import logging
		from logging.handlers import SMTPHandler
		credentials = None
		secure = None
		if getattr(cls, 'MAIL_USERNAME', None) is not None:
			credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
			if getattr(cls, 'MAIL_USE_TLS', None):
				secure = ()
		mail_handler = SMTPHandler(
			mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
			fromaddr=cls.FLASKY_MAIL_SENDER,
			toaddrs=[cls.FLASKY_ADMIN],
			subject=cls.FLASKY_MAIL_SUBJECT_PREFIX + 'Application Error', credentials=credentials, secure=secure)
		mail_handler.setLevel(logging.ERROR)
		app.logger.addHandler(mail_handler)


config = {
	'development': DevelopmentConfig,
	'testing': TestingConfig,
	'production': ProductionConfig,
	'default': DevelopmentConfig
}
