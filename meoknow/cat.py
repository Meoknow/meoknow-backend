from io import BytesIO
from PIL import Image
import base64, re, random, time, json, os
import multiprocessing as mp

from flask import (
	flash, g, redirect, render_template, request, session, url_for, send_from_directory, send_file, current_app, abort
)
from flask.helpers import make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref
from werkzeug.utils import secure_filename
from datetime import datetime

from meoknow import db
from .model import Photo, CatInfo, IdentifyHistory
from .util import exception_handler, format_time, format_timestamp
from .auth import login_check
from . import ml

ALLOWED_FORMAT = ['jpg', 'jpeg', 'png']
PHOTO_PREFIX = current_app.config.get("URI_AUTHORITY", "localhost:5000") + "/photos/"

ERROR_INVALID_DATA = ({"code":100, "msg": "Invalid Data", "data": {}}, 400)
ERROR_NO_CAT = ({"code":101, "msg": "No Cat Found", "data": {}}, 400)
ERROR_PERMISSION_DENIED = ({"code":3, "msg":"Permission Denied", "data":{}}, 401)
ERROR_INTERNAL = ({"code":2, "msg":"Server Internal Error", "data":{}}, 500)

RESP_OK = {"code":0, "msg":"", "data":{}}


def add_functions(app):

	if mp.get_start_method() == None:
		mp.set_start_method('spawn')
	parent_conn, child_conn = mp.Pipe()
	ml_process = mp.Process(target=ml.run, args=(child_conn,))
	ml_process.start()
	ml_lock = mp.Lock()

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

	@app.route('/identify/', methods=['POST'])
	@exception_handler
	@login_check()
	def identify():
		rdata = request.get_json()
		img_64 = rdata.get("image")
		# change the owner to current user only
		owner = request.user_id
		img_name = upload_photo(img_64, owner)
		if img_name == None:
			return ERROR_INVALID_DATA
		img_url = os.path.join(app.instance_path, "images", img_name)
		pho_url = PHOTO_PREFIX + img_name
		# give the image to model
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
						cats.append({"cat_id":catinfo.cat_id, "confidence":str(round(res_sco[i],2))})
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
				
					resp = {"code":0, "msg":"", "data":{
						"cats":cats,
						"url":img_url,
						"time":format_time(idhis.upl_time),
						"timestamp":format_timestamp(idhis.upl_time)
						}}
		
		except Exception as e:
			print(e)
			resp = ERROR_INTERNAL
		finally:
			ml_lock.release()

		return resp
	
	@app.route('/identify/', methods = ['GET'])
	@exception_handler
	@login_check()
	def get_identify_history():
		page_size = request.values.get("page_size")
		page = request.values.get("page")
		if type(page_size) != int or type(page) != int:
			return ERROR_INVALID_DATA
		# change the owner to current user only
		owner = request.user_id
		try:
			# check if current user is admin
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
				"url":idhis[i].img_url,
				"time":format_time(idhis[i].upl_time),
				"timestamp":format_timestamp(idhis[i].upl_time)
			})
		return {"code":0, "msg":"", "data":data}
	
	@app.route('/cats/', methods = ['GET'])
	@exception_handler
	def getallcats():
		infos = CatInfo.query.all()
		cats_data = []
		for info in infos:
			cats_data.append(get_cat_data(info))
		return {"code": 0, "msg": "", "data" : cats_data}
	
	@app.route('/cats/', methods = ['POST'])
	@exception_handler
	@login_check(admin=True)
	def addcat():
		rdata = request.get_json()
		name = rdata.get("name")
		if name == None:
			return ERROR_INVALID_DATA
		img_64 = rdata.get("image")
		img_url = rdata.get("img_url")

		if img_64 == None and img_url != None:
			pass
		elif img_64 != None and img_url == None:
			img_url = PHOTO_PREFIX+upload_photo(img_64, "public")
		else:
			return ERROR_INVALID_DATA

		gender = rdata.get("gender")
		health_status = rdata.get("health_status")
		desexing_status = rdata.get("desexing_status")
		description = rdata.get("description")
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
	
	@app.route('/cats/<int:cat_id>', methods = ['GET'])
	@exception_handler
	def get_onecat(cat_id):
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

	@app.route('/cats/<int:cat_id>', methods=['POST', 'PATCH'])
	@exception_handler
	@login_check(admin=True)
	def update_onecat(cat_id):
		rdata = request.get_json()
		name = rdata.get("name")
		img_64 = rdata.get("image")
		img_url = rdata.get("img_url")

		if img_64 == None:
			pass
		elif img_64 != None and img_url == None:
			img_url = PHOTO_PREFIX+upload_photo(img_64, "public")
		else:
			return ERROR_INVALID_DATA
				
		gender = rdata.get("gender")
		health_status = rdata.get("health_status")
		desexing_status = rdata.get("desexing_status")
		description = rdata.get("description")
		cat = CatInfo.query.get(cat_id)
		if cat == None:
			return ERROR_INVALID_DATA

		if request.method == "PUT" or name != None:
			cat.name = name
		if request.method == "PUT" or img_url != None:
			cat.img_url = img_url
		if request.method == "PUT" or gender != None:
			cat.gender = gender
		if request.method == "PUT" or health_status != None:
			cat.health_status = health_status
		if request.method == "PUT" or desexing_status != None:
			cat.desexing_status = desexing_status
		if request.method == "PUT" or description != None:
			cat.description = description

		try:
			db.session.add(cat)
			db.session.commit()
		except Exception as e:
			print(e)
			return ERROR_INVALID_DATA
		return RESP_OK

	@app.route('/photos/<photo_name>', methods = ['GET'])
	@exception_handler
	# @login_check()
	def get_image(photo_name):
		photo = Photo.query.filter_by(name=photo_name).first()
		if photo == None:
			abort(404)
		
		# check if current user is admin
		if photo.owner == 'public' or photo.owner == request.user_id or request.user_id == 'admin':
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
		else:
			return ERROR_PERMISSION_DENIED
	
	@app.route('/photos/<photo_name>', methods = ['DELETE'])
	@exception_handler
	@login_check(admin=True)
	def delete_image(photo_name):
		photo = Photo.query.filter_by(name=photo_name).first()
		if photo == None:
			abort(404)
		db.session.delete(photo)
		db.session.commit()
		return RESP_OK
		
	@app.route('/photos/', methods = ['POST'])
	@exception_handler
	@login_check()
	def addimage():
		rdata = request.get_json()
		img_64 = rdata.get("image")
		owner = rdata.get("owner")
		if img_64 == None:
			return ERROR_INVALID_DATA
		print(img_64, type(img_64))
		print(owner, type(owner))
		# owner must be one of 1. public 2. private 3. admin
		if not owner in [None, 'public', 'private', 'admin']:
			return ERROR_INVALID_DATA
		if owner == None:
			owner = 'public'
		elif owner == 'private':
			owner = request.user_id
		img_name = upload_photo(img_64, owner)
		if img_name == None:
			return ERROR_INVALID_DATA
		img_url = PHOTO_PREFIX + img_name
		return {"code":0, "msg":"", "data":{"url":img_url}}

