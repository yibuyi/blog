from app import mail
#from app.decorators import async
from flask_mail import Message
from flask import render_template, current_app
from threading import Thread


#@async
def send_async_email(app, msg):
	with app.app_context():
		mail.send(msg)


def send_email(to, subject, template, **kwargs):
	app = current_app._get_current_object()
	#msg = Message(subject, sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
	msg = Message(str(app.config['FLASKY_MAIL_SUBJECT_PREFIX']) + str(' ') + str(subject),
				  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
	msg.body = render_template(template + '.txt', **kwargs)
	msg.html = render_template(template + '.html', **kwargs)
	thr = Thread(target=send_async_email, args=[app, msg])
	thr.start()
	return thr
	#send_async_email(app, msg)
