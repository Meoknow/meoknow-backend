from flask import session, redirect, url_for, request, jsonify, render_template
from .util import exception_handler
from .model import CatInfo, Photo
from .cat import ALLOWED_FORMAT, PHOTO_PREFIX
from meoknow import db
from io import BytesIO
from datetime import datetime
import base64
import re
import os
import functools
import uuid
import random
from PIL import Image


def add_functions(app):
	ADMIN_USERNAME = app.config.get("ADMIN_USERNAME", "dev")
	ADMIN_PASSWORD = app.config.get("ADMIN_PASSWORD", "dev")
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

	def admin_login_check(func):
		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			if session.get("verified", False) == False:
				return jsonify({
					"code": 3,
					"msg": "login required",
					"data": {}
				})
			return func(*args, **kwargs)
		return wrapper

	@app.route("/admin/login_api", methods=["POST"])
	@exception_handler
	def admin_login_api():
		data = request.get_json()
		username = data.get("username", "")
		password = data.get("password", "")
		if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
			return jsonify({
				"code": 1,
				"msg": "invalid username or password",
				"data": {}
			})
		session["verified"] = True
		return jsonify({
			"code": 0,
			"msg": "login success",
			"data": {}
		})

	@app.route("/admin/logout_api", methods=["POST"])
	@exception_handler
	def admin_logout_api():
		session["verified"] = False
		return jsonify({
			"code": 0,
			"msg": "logout success",
			"data": {}
		})

	@app.route("/admin/add_cat_api", methods=["POST"])
	@exception_handler
	@admin_login_check
	def admin_add_cat_api():
		data = request.get_json()
		img_64 = data.get("image", None)
		payload = {}
		if isinstance(img_64, str):
			path = upload_photo(img_64, "public")
			if path == None:
				return jsonify({
					"code": 102,
					"msg": "broken image",
					"data": {}
				})
			payload['img_url'] = PHOTO_PREFIX + path
		else:
			return jsonify({
				"code": 100,
				"msg": "image required",
				"data": {}
			})
		attributes = ["name", "gender", "health_status", "desexing_status", "description"]
		for attr in attributes:
			attr_val = data.get(attr, None)
			print(attr, attr_val)
			if not isinstance(attr_val, str):
				return jsonify({
					"code": 101,
					"msg": f"invalid {attr}",
					"data": {}
				})
			payload[attr] = attr_val
		cat = CatInfo(**payload)
		db.session.add(cat)
		db.session.commit()
		return jsonify({
			"code": 0,
			"msg": "success",
			"data": {}
		})
	
	@app.route("/admin/update_cat_api", methods=["POST"])
	@exception_handler
	@admin_login_check
	def admin_update_cat_api():
		data = request.get_json()
		cat_id = data.get("cat_id", None)
		if not isinstance(cat_id, int):
			return jsonify({
				"code": 100,
				"msg": "invalid cat_id",
				"data": {}
			})
		cat = CatInfo.query.filter_by(cat_id=cat_id).one_or_none()
		if cat:
			img_64 = data.get("image", None)
			if isinstance(img_64, str):
				path = upload_photo(img_64, "public")
				if path == None:
					return jsonify({
						"code": 102,
						"msg": "broken image",
						"data": {}
					})
				cat.img_url = PHOTO_PREFIX + path
			attributes = ["name", "gender", "health_status", "desexing_status", "description"]
			for attr in attributes:
				attr_val = data.get(attr, None)
				if isinstance(attr_val, str):
					setattr(cat, attr, attr_val)
			db.session.commit()
			return jsonify({
				"code": 0,
				"msg": "success",
				"data": {}
			})
		else:
			return jsonify({
				"code": 101,
				"msg": "no such cat",
				"data": {}
			})

	@app.route("/admin/delete_cat_api", methods=["POST"])
	@exception_handler
	@admin_login_check
	def admin_delete_cat_api():
		data = request.get_json()
		cat_id = data.get("cat_id", None)
		if not isinstance(cat_id, int):
			return jsonify({
				"code": 100,
				"msg": "invalid cat_id",
				"data": {}
			})
		cat = CatInfo.query.filter_by(cat_id=cat_id).one_or_none()
		if cat:
			db.session.delete(cat)
			db.session.commit()
			return jsonify({
				"code": 0,
				"msg": "success",
				"data": {}
			})
		else:
			return jsonify({
				"code": 101,
				"msg": "no such cat",
				"data": {}
			})

	@app.route("/admin/get_all_cat_api", methods=["GET"])
	@exception_handler
	@admin_login_check
	def admin_get_all_cat_api():
		page = request.args.get("page", 1)
		if not isinstance(page, int):
			return jsonify({
				"code": 100,
				"msg": "invalid page",
				"data": {}
			})
		result = CatInfo.query.paginate(page, 10, False)
		resp = []
		for item in result.items:
			attributes = [
				"cat_id", "name", "gender", "health_status",
				"desexing_status", "description", "upl_time",
				"img_url"
			]
			data = {
				attr: getattr(item, attr)
				for attr in attributes
			}
			resp.append(data)
		return jsonify({
			"code": 0,
			"msg": "",
			"data": {
				"resp": resp
			}
		})

	@app.route("/admin/login")
	def admin_login():
		if session.get("verified", False) == True:
			return redirect(url_for("admin_index"))
		return render_template("login.html")
	
	@app.route("/admin/")
	def admin_index():
		if session.get("verified", False) == False:
			return redirect(url_for("admin_login"))
		return render_template("index.html")
	
	@app.route("/admin/cat")
	def admin_cat():
		if session.get("verified", False) == False:
			return redirect(url_for("admin_login"))
		return render_template("cat.html")