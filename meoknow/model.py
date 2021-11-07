from meoknow import db
from datetime import datetime

class Comment(db.Model):
	__table_args__ = {"extend_existing": False}
	comment_id = db.Column(db.Integer, primary_key=True)
	main_comment_id = db.Column(db.Integer, nullable=False)
	reply_id = db.Column(db.Integer, nullable=False)
	is_reply = db.Column(db.Boolean, nullable=False)
	like = db.Column(db.Integer, nullable=False)
	create_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
	owner = db.Column(db.String(80), nullable=False)
	parent_owner = db.Column(db.String(80), nullable=False)
	cat_id = db.Column(db.Integer, nullable=False)
	content = db.Column(db.String, nullable=False)
	images_path = db.Column(db.String, nullable=False)
	is_hidden = db.Column(db.Boolean, nullable=False)

class Comment_Like(db.Model):
	__table_args__ = {"extend_existing": False}
	idx = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.String(80))
	comment_id = db.Column(db.Integer)
	owner = db.Column(db.String(80))
	create_time = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
	__table_args__ = {"extend_existing": False}
	user_id = db.Column(db.String(80), primary_key=True)
	nickname = db.Column(db.String(80))
	avatar_path = db.Column(db.String(120))