# coding=utf-8
from app.models import User, Role
from flask_pagedown.fields import PageDownField
from flask_wtf import Form
from wtforms import StringField, SubmitField, TextAreaField, ValidationError, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Email, Regexp


class NameForm(Form):
	name = StringField('what is your name?', validators=[DataRequired()])
	submit = SubmitField('Submit')


class PostForm(Form):  # 博客文章表单
	head = StringField(u'标题', validators=[DataRequired(), Length(1, 64)])
	body = PageDownField(u'有什么想法就赶紧写出来吧！', validators=[DataRequired()])
	submit = SubmitField(u'提交')


class CommentForm(Form):
	username = StringField('用户名', validators=[DataRequired()])
	body = StringField('说点什么吧：', validators=[DataRequired()])
	submit = SubmitField('提交')


# 用户资料编辑表单
class EditProfileForm(Form):
	name = StringField(u'真实名字', validators=[Length(0, 64)])
	location = StringField(u'位置', validators=[Length(0, 64)])
	about_me = TextAreaField(u'关于我')
	submit = SubmitField(u'提交')


# 管理员使用的资料编辑表单
class EditProfileAdminForm(Form):
	email = StringField(u'邮箱', validators=[DataRequired(), Length(1, 64), Email()])
	username = StringField(u'用户名', validators=[DataRequired(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
																					 'Usernames must have only letters,'
																					 'numbers,dots or underscores')])
	confirmed = BooleanField(u'确认')
	role = SelectField(u'角色', coerce=int)
	name = StringField(u'真实名字', validators=[Length(0, 64)])
	location = StringField(u'位置', validators=Length(0, 64))
	about_me = TextAreaField(u'关于我')
	submit = SubmitField(u'提交')

	def __init__(self, user, *args, **kwargs):
		super(EditProfileAdminForm, self).__init__(*args, **kwargs)
		self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
		self.user = user

	def validate_email(self, field):
		if field.data != self.user.email.data and \
				User.query.filter_by(email=field.data).first():
			raise ValidationError(u'该邮箱已经注册过了！')

	def validate_username(self, field):
		if field.data != self.user.username and \
				User.query.filter_by(username=field.data).first():
			raise ValidationError(u'该用户名已经在使用')
