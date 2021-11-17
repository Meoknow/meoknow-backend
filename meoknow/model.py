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

# Photo : this class, an image with other infos
# Image : only a file
class Photo(db.Model):
	__table_args__ = {"extend_existing": False}
	id = db.Column(db.Integer, primary_key=True)
	# corresponding to User system
	owner = db.Column(db.String(80), nullable=False)
	upl_time = db.Column(db.DateTime, default=datetime.utcnow)
	name = db.Column(db.String(120), unique=True, nullable=False)
	# corresponding to cat
	# cat_id = db.Column(db.Integer, db.ForeignKey('cat_info.cat_id'))
	
	def __repr__(self):
		return '<Name %r>' % self.name

class CatInfo(db.Model):
	__table_args__ = {"extend_existing": True}
	cat_id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(80), unique=True, nullable=False)
	upl_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
	gender = db.Column(db.String(80))
	health_status = db.Column(db.String(80))
	desexing_status = db.Column(db.String(80))
	desexing_time = db.Column(db.String(80))
	description = db.Column(db.String(80))

	img_url = db.Column(db.String(120), unique=True, nullable=False)
	# cat_photo = db.relationship('Photo', backref='catinfo')

	def __repr__(self):
		return '<Name %r>' % self.name

class IdentifyHistory(db.Model):
	__table_args__ = {"extend_existing": False}
	id = db.Column(db.Integer, primary_key=True)
	img_url = db.Column(db.String(120), unique=False, nullable=False)
	owner = db.Column(db.String(80), unique=False, nullable=False)
	res = db.Column(db.String(120), unique=False, nullable=False)
	upl_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
	# cat_photo = db.relationship('Photo', backref='catinfo')

	def __repr__(self):
		return '<url %r>' % self.img_url