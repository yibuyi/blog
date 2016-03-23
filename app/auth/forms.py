# -*- coding: utf-8 -*-
from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Length, Email, DataRequired, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User


class LoginForm(Form):
	email = StringField(label=u'邮箱', validators=[DataRequired(), Length(1, 64), Email()])
	password = PasswordField(label=u'密码', validators=[DataRequired()])
	remember_me = BooleanField(label=u'记住我')
	submit = SubmitField(label=u'提交')


def validate_username(field):
	if User.query.filter_by(username=field.data).first():
		raise ValidationError('用户名已经被使用')


class RegistrationForm(Form):
	email = StringField(label=u'邮箱', validators=[DataRequired(), Length(1, 64), Email()])
	username = StringField(label=u'用户名', validators=[
		DataRequired(), Length(1, 64), Regexp('^[A-Za-z0-9_.]*$', 0, '用户名只能包含字母、数字和点')])
	password = PasswordField(label=u'密码', validators=[
		DataRequired(), EqualTo('password2', message=u'两次密码必须一致')])
	password2 = PasswordField(label=u'确认密码', validators=[DataRequired()])
	submit = SubmitField(label=u'注册')

	def validate_email(self, field):
		if User.query.filter_by(email=field.data).first():
			raise ValidationError('邮箱已经被注册')

	def validate_username(self, field):
		if User.query.filter_by(username=field.data).first():
			raise ValidationError('用户名已经被使用')


class ChangePasswordForm(Form):
	old_password = PasswordField(u'旧密码', validators=[DataRequired()])
	password = PasswordField(u'新密码', validators=[
		DataRequired(), EqualTo(u'再输入一次', message=u'密码必须一致')])
	password2 = PasswordField(u'确认密码', validators=[DataRequired()])
	submit = SubmitField(u'更新密码')


class PasswordResetRequestForm(Form):
	email = StringField(u'邮箱', validators=[DataRequired(), Length(1, 64), Email()])
	submit = SubmitField(u'重置密码')


class PasswordResetForm(Form):
	email = StringField(u'邮箱', validators=[DataRequired(), Length(1, 64), Email()])
	password = PasswordField(u'新密码', validators=[DataRequired(), EqualTo('password2', message=u'密码必须一致'), ])
	password2 = PasswordField(u'确认密码', validators=[DataRequired()])
	submit = SubmitField(u'重置密码')

	def validate_email(self, field):
		if User.query.filter_by(email=field.data) is None:
			raise ValidationError(u'邮箱地址无效')


class ChangeEmailForm(Form):
	email = StringField(u'新邮箱', validators=[DataRequired(), Length(1, 64), Email()])
	password = PasswordField(u'密码', validators=[DataRequired()])
	submit = SubmitField(u'更新邮箱地址')

	def validate_eamil(self, field):
		if User.query.filter_by(email=field.data).first():
			raise ValidationError(u'该邮箱已经注册过了')
