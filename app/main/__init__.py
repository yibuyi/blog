# coding=utf-8
from app.models import Permission
from flask import Blueprint

main = Blueprint('main', __name__)

from . import views, errors


@main.app_context_processor  # 把permission类加入模板上下文
def inject_permissions():
	return dict(Permission=Permission)
