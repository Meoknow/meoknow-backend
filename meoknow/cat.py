import os
from io import StringIO, BytesIO
import base64
from PIL import Image
import re
import random
import PIL
import time
import multiprocessing as mp

from flask import (
	flash, g, redirect, render_template, request, session, url_for, send_from_directory, send_file
)
from flask.helpers import make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref
from werkzeug.utils import secure_filename
from datetime import datetime

from meoknow import db

ALLOWED_FORMAT = ['jpg', 'jpeg', 'png']
PHOTO_PREFIX = "localhost:5000/photos/"

ERROR_INVALID_DATA = ({"code":100, "msg": "Invalid Data", "data": {}}, 400)
ERROR_NO_CAT = ({"code":101, "msg": "No Cat Found", "data": {}}, 400)
ERROR_PERMISSION_DENIED = ({"code":3, "msg":"Permission Denied", "data":{}}, 401)
ERROR_INTERNAL = ({"code":2, "msg":"Server Internal Error", "data":{}}, 500)

RESP_OK = {"code":0, "msg":"", "data":{}}

# Photo : this class, an image with other infos
# Image : only a file
class Photo(db.Model):
	__table_args__ = {"extend_existing": False}
	id = db.Column(db.Integer, primary_key=True)
	# corresponding to User system
	owner = db.Column(db.String(80), unique=False, nullable=False)
	upl_time = db.Column(db.DateTime, default=datetime.utcnow)
	name = db.Column(db.String(120), unique=True, nullable=False)
	# corresponding to cat
	# cat_id = db.Column(db.Integer, db.ForeignKey('cat_info.cat_id'))
	
	def __repr__(self):
		return '<Name %r>' % self.name

class CatInfo(db.Model):
	__table_args__ = {"extend_existing": False}
	cat_id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(80), unique=True, nullable=False)
	upl_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
	gender = db.Column(db.String(80))
	health_status = db.Column(db.String(80))
	desexing_status = db.Column(db.String(80))
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

def add_functions(app):

	from . import ml
	mp.set_start_method('spawn')
	parent_conn, child_conn = mp.Pipe()
	ml_process = mp.Process(target=ml.run, args=(child_conn,))
	ml_process.start()
	ml_lock = mp.Lock()

	@app.route('/mptest/<test_arg>')
	def mptest(test_arg):
		print("mptest start ", test_arg)
		time.sleep(10)
		print("mptest finish", test_arg)
		return "ok"

	# translate a base64 image to file and save it to db and dir
	def upload_photo(img_64, owner):
		
		try:
			file_fmt = re.findall("^data:image/(.+?);base64,", img_64)
			if file_fmt == None:
				return None
			file_fmt = file_fmt[0]
			if file_fmt not in ALLOWED_FORMAT:
				return None
			img_64 = re.sub("^data:image/.+;base64,", "", img_64)
			byte_data = base64.b64decode(img_64)
			img = Image.open(BytesIO(byte_data))
			img_name = "".join(re.findall("[0-9]", str(datetime.utcnow())))
			img_name = owner+img_name+str(random.randint(0,9999)).zfill(4)+"."+file_fmt
			img_url = os.path.join(app.instance_path, "images", img_name)
			img.save(os.path.join(app.instance_path, img_url))
			photo = Photo(owner=owner, name=img_name)
			db.session.add(photo)
			db.session.commit()
			return img_name
		except Exception as e:
			print(e)
			return None

	def get_cat_data(info):
		return {
			"cat_id":info.cat_id, 
			"name":info.name,
			"img_url":info.img_url,
			"gender":info.gender,
			"health_status":info.health_status,
			"desexing_status":info.desexing_status,
			"description":info.description
		}

	@app.route('/identify/', methods=['GET', 'POST'])
	def identify():
		if request.method == "POST":
			img_64 = request.values.get("image")
			# change the owner to current user only
			# TODO
			owner = "public"
			img_name = upload_photo(img_64, owner)
			if img_name == None:
				return ERROR_INVALID_DATA
			img_url = os.path.join(app.instance_path, "images", img_name)
			pho_url = PHOTO_PREFIX + img_name
			# give the image to model
			# TODO
			ml_lock.acquire()
			try:
				parent_conn.send(img_url)
				res = parent_conn.recv()

				res_cat = res["cat"]
				res_sco = res["score"]
				res_err = res["error"]

				# if we successfully find cat, save this record to database
				if len(res_cat) != len(res_sco):
					resp = ERROR_INTERNAL
				elif res_err != []:
					print(res_err)
					resp = ERROR_INTERNAL
				else:
					cats = []
					for i in range(0, len(res_cat)):
						catinfo = CatInfo.query.filter_by(name=res_cat[i]).first()
						if catinfo != None:
							cats.append({"cat_id":catinfo.cat_id, "confidence":res_sco[i]})
					if cats == []:
						resp = ERROR_NO_CAT
					else:
						idhis = IdentifyHistory(
							img_url=img_url,
							owner=owner,
							res=str(cats)
						)
						db.session.add(idhis)
						db.session.commit()
					
						resp = {"code":0, "msg":"", "data":{"cats":cats}}
			
			except Exception as e:
				print(e)
				resp = ERROR_INTERNAL
			finally:
				ml_lock.release()

			return resp
		elif request.method == "GET":
			page_size = request.values.get("page_size")
			page = request.values.get("page")
			# change the owner to current user only
			# TODO
			owner = "public"
			try:
				if owner == "admin":
					idhis = IdentifyHistory.query.order_by(IdentifyHistory.upl_time.desc()).all()
				else:
					idhis = IdentifyHistory.query.filter_by(owner=owner).order_by(IdentifyHistory.upl_time).all()
			except Exception as e:
				return ERROR_INTERNAL
			idhis = idhis[::-1]
			if len(idhis) < (page-1) * page_size:
				return {"code":0, "msg":"", "data":[]}
			data = []
			for i in range((page-1)*page_size, min(page*page_size, len(idhis))):
				data.append({
					"cats":eval(idhis[i].res),
					"img_url":idhis[i].img_url
				})
			return {"code":0, "msg":"", "data":data}
			
	@app.route('/cats/', methods = ['GET', 'POST'])
	def cats():
		if request.method == 'GET':
			infos = CatInfo.query.all()
			cats_data = []
			for info in infos:
				cats_data.append(get_cat_data(info))
			return {"code": 0, "msg": "", "data" : cats_data}
		elif request.method == 'POST':
			# require admin
			name = request.values.get("name")
			img_64 = request.values.get("image")
			img_url = request.values.get("img_url")

			if img_64 == None and img_url != None:
				pass
			elif img_64 != None and img_url == None:
				img_url = PHOTO_PREFIX+upload_photo(img_64, "public")
			else:
				return ERROR_INVALID_DATA

			gender = request.values.get("gender")
			health_status = request.values.get("health_status")
			desexing_status = request.values.get("desexing_status")
			description = request.values.get("description")
			cat_info = CatInfo(
				name=name,
				img_url=img_url,
				gender=gender,
				health_status=health_status,
				desexing_status=desexing_status,
				description=description
			)
			try:
				db.session.add(cat_info)
				db.session.commit()
			except Exception as e:
				print(e)
				return ERROR_INVALID_DATA
			return RESP_OK
	
	@app.route('/cats/<cat_id>', methods = ['GET', 'POST', 'PATCH'])
	def onecat(cat_id):
		if request.method == 'GET':
			try:
				info = CatInfo.query.filter_by(cat_id=cat_id).first()
				if info is None:
					return ERROR_INVALID_DATA
				print(type(info))
				cat_data = get_cat_data(info)
				return {"code":0, "msg":"", "data":cat_data}
			except Exception as e:
				print(e)
				return ERROR_INVALID_DATA
			

		else:
			# require admin
			name = request.values.get("name")
			img_64 = request.values.get("image")
			img_url = request.values.get("img_url")

			if img_64 == None:
				pass
			elif img_64 != None and img_url == None:
				img_url = PHOTO_PREFIX+upload_photo(img_64, "public")
			else:
				return ERROR_INVALID_DATA
					
			gender = request.values.get("gender")
			health_status = request.values.get("health_status")
			desexing_status = request.values.get("desexing_status")
			description = request.values.get("description")
			cat = CatInfo.query.get(cat_id)
			if cat == None:
				return ERROR_INVALID_DATA

			if request.method == "PUT" or img_url != None:
				cat.img_url = request.values.get("img_url")
			if request.method == "PUT" or gender != None:
				cat.gender = request.values.get("gender")
			if request.method == "PUT" or health_status != None:
				cat.health_status = request.values.get("health_status")
			if request.method == "PUT" or desexing_status != None:
				cat.desexing_status = request.values.get("desexing_status")
			if request.method == "PUT" or description != None:
				cat.description = request.values.get("description")

			try:
				db.session.commit()
			except Exception as e:
				print(e)
				return ERROR_INVALID_DATA
			return RESP_OK


	@app.route('/photos/<photo_name>', methods = ['GET', 'DELETE'])
	def image(photo_name):
		if request.method == 'GET':

			photo = Photo.query.filter_by(name=photo_name).first()
			if photo == None:
				error = "no photo"
				flash(error)
			
			if photo.owner == 'public':
				img_url = os.path.join(app.instance_path, "images", photo_name)

				try:
					img = Image.open(img_url)
					img_byte = BytesIO()
					img_fmt = photo_name.split('.')[-1]
					img.save(img_byte, format=img_fmt)
					return send_file(BytesIO(img_byte.getvalue()),
						mimetype='image/'+img_fmt,
						as_attachment=False,
						attachment_filename=photo_name
					)
				except Exception as e:
					print(e)
					return ERROR_INVALID_DATA
			# check user's access to the photo
			# TODO
			else:
				return ERROR_PERMISSION_DENIED
		else:
			photo = Photo.query.filter(name=photo_name).first()

			
	# require admin
	@app.route('/photos/', methods = ['POST'])
	def addimage():
		img_64 = request.values.get("image")
		owner = request.values.get("owner")
		print(img_64, type(img_64))
		print(owner, type(owner))
		# owner must be one of 1. public 2. client itself 3. admin
		# TODO check it
		if owner == None:
			owner = "public"
		img_name = upload_photo(img_64, owner)
		if img_name == None:
			return ERROR_INVALID_DATA
		img_url = PHOTO_PREFIX + img_name
		return {"code":0, "msg":"", "data":{"url":img_url}}

