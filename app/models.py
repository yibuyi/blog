from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from app import login_manager
from app import db
from flask import current_app, url_for
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from markdown import markdown
import bleach
from wtforms import ValidationError


class Permission:
	FOLLOW = 0x01
	COMMENT = 0x02
	WRITE_ARTICLES = 0x04
	MODERATE_COMMENTS = 0x08
	ADMINISTER = 0x80


class Role(db.Model):
	__tablename__ = 'roles'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64), unique=True)
	default = db.Column(db.Boolean, default=False, index=True)
	permissions = db.Column(db.Integer)
	users = db.relationship('User', backref='role', lazy='dynamic')

	@staticmethod  # 在数据库中创建角色
	def insert_roles():
		roles = {
			'User': (Permission.FOLLOW |
					 Permission.COMMENT |
					 Permission.WRITE_ARTICLES, True),
			'Moderator': (Permission.FOLLOW |
						  Permission.COMMENT |
						  Permission.WRITE_ARTICLES |
						  Permission.MODERATE_COMMENTS, False),
			'Administrator': (0xff, False)
		}
		for r in roles:
			role = Role.query.filter_by(name=r).first()
			if role is None:
				role = Role(name=r)
			role.permissions = roles[r][0]
			role.default = roles[r][1]
			db.session.add(role)
		db.session.commit()

	def __repr__(self):
		return '<Role %r>' % self.name


# 关注关联表的模型实现
class Follow(db.Model):
	__tablename__ = 'follows'
	follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
	followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
	timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(64), unique=True, index=True)
	username = db.Column(db.String(64), unique=True, index=True)
	role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
	password_hash = db.Column(db.String(128))
	confirmed = db.Column(db.Boolean, default=False)
	name = db.Column(db.String(64))
	location = db.Column(db.String(64))
	about_me = db.Column(db.Text())
	member_since = db.Column(db.DateTime(), default=datetime.utcnow)
	last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
	posts = db.relationship('Post', backref='author', lazy='dynamic')
	followed = db.relationship('Follow', foreign_keys=[Follow.follower_id],
							   backref=db.backref('follower', lazy='joined'),
							   lazy='dynamic', cascade='all, delete-orphan')
	followers = db.relationship('Follow', foreign_keys=[Follow.followed_id],
								backref=db.backref('followed', lazy='joined'),
								lazy='dynamic', cascade='all, delete-orphan')
	comments = db.relationship('Comment', backref='author', lazy='dynamic')

	def __init__(self, **kwargs):  # 定义默认的用户角色
		super(User, self).__init__(**kwargs)
		if self.role is None:
			if self.email == current_app.config['FLASKY_ADMIN']:
				self.role = Role.query.filter_by(permissions=0xff).first()
			if self.role is None:
				self.role = Role.query.filter_by(default=True).first()
			# self.follow(self)  # 构建用户时把用户设为自己的关注者

	@property  # 在user模型中加入密码散列
	def password(self):
		raise ArithmeticError('password is not a readable attributes')

	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)

	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)

	def generate_confirmation_token(self, expiration=3600):
		s = Serializer(current_app.config['SECRET_KEY'])
		return s.dumps({'confirm': self.id})

	def confirm(self, token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return False
		if data.get('confirm') != self.id:
			return False
		self.confirmed = True
		db.session.add(self)
		return True

	def generate_reset_token(self, expiration=3600):
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		return s.dumps({'reset': self.id})

	def reset_password(self, token, new_password):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return False
		if data.get('reset') != self.id:
			return False
		db.session.add(self)
		return True

	def generate_email_change_token(self, new_email, expiration=3600):
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		return s.dumps({'change_email': self.id, 'new_email': new_email})

	def change_email(self, token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return False
		if data.get('change_email') != self.id:
			return False
		new_email = data.get('new_email')
		if new_email is None:
			return False
		if self.query.filter_by(email=new_email).first() is not None:
			return False
		return True

	def can(self, permissions):  # 检查用户是否有指定的权限
		return self.role is not None and \
			   (self.role.permissions and permissions) == permissions

	def is_administrator(self):  # 检查用户是否有指定的权限
		return self.can(Permission.ADMINISTER)

	def ping(self):  # 刷新用户的最后访问时间
		self.last_seen = datetime.utcnow()
		db.session.add(self)

	def follow(self, user):  # 关注关系的辅助方法
		if not self.is_following(user):
			f = Follow(follower=self, followed=user)
			db.session.add(f)

	def unfollow(self, user):
		f = self.followed.filter_by(followed_id=user.id).first()
		if f:
			db.session.delete(f)

	def is_following(self, user):
		return self.followed.filter_by(followed_id=user.id).first() is not None

	def is_followed_by(self, user):
		return self.followers.filter_by(follower_id=user.id).first() is not None

	@property  # 获取所关注用户的文章
	def followed_posts(self):
		return Post.query.join(Follow, Follow.followed_id == Post.author_id) \
			.filter(Follow.follower_id == self.id)

	def to_json(self):  # 把用户转换成JSON格式的序列化字典
		json_user = {
			'url': url_for('api.get_post', id=self.id, _external=True),
			'username': self.username,
			'member_since': self.member_since,
			'last_seen': self.last_seen,
			'posts': url_for('api.get_user.posts', id=self.id, _external=True),
			'followed_posts': url_for('api.get_user_followed_posts',
									  id=self.id, _external=True),
			'post_count': self.posts.count()
		}
		return json_user

	def generate_auth_token(self, expiration):  # 支持基于令牌的认证
		s = Serializer(current_app.config['SECRET_KEY'],
					   expires_in=expiration)
		return s.dumps({'id': self.d}).decode('ascii')

	@staticmethod
	def verify_auth_token(token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return None
		return User.query.get(data['id'])

	def __repr__(self):
		return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):  # 检查用户是否有指定的权限
	def can(self, permissions):
		return False

	def is_administrator(self):
		return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader  # 加载用户的回调函数
def load_user(user_id):
	return User.query.get(int(user_id))


# 文章模型
class Post(db.Model):
	__tablename__ = 'posts'
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.Text)
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	body_html = db.Column(db.Text)
	comments = db.relationship('Comment', backref='post', lazy='dynamic')

	def on_changed_body(target, value, oldvalue, initiator):
		allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
						'h1', 'h2', 'h3,', 'p']
		target.body_html = bleach.linkify(bleach.clean(markdown(value, output_format='html'),
													   tags=allowed_tags, strip=True))

	def to_json(self):  # 把文章转换成json格式的序列化字典
		json_post = {
			'url': url_for('api.get_post', id=self.id, _external=True),
			'body': self.body,
			'body_html': self.body_html,
			'timestamp': self.timestamp,
			'author': url_for('api.get_user', id=self.author_id, _external=True),
			'comments': url_for('api.get_post_comments', id=self.id, _external=True),
			'comment_count': self.comments.count()
		}
		return json_post

	@staticmethod
	def from_json(json_post):
		body = json_post.get('body')
		if body is None or body == '':
			raise ValidationError('post does not have a body')
		return Post(body=body)


db.event.listen(Post.body, 'set', Post.on_changed_body)


class Comment(db.Model):
	__tablename__ = 'comments'
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.Text)
	body_html = db.Column(db.Text)
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	disabled = db.Column(db.Boolean)
	author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

	@staticmethod
	def on_changed_body(target, value, oldvalue, initiator):
		allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i', 'strong']
		target.body_html = bleach.linkify(bleach.clean(
			markdown(value, output_format='html'),
			tags=allowed_tags, strip=True))


db.event.listen(Comment.body, 'set', Comment.on_changed_body)
