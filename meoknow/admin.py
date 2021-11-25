from flask import session, redirect, url_for, request, jsonify, render_template
from .util import exception_handler
from .model import CatInfo, Photo, Comment
from .comment import get_nickname_by_userid, get_avatar_by_userid, get_url_from_path
from .cat import ALLOWED_FORMAT, PHOTO_PREFIX
from meoknow import db
from io import BytesIO
from datetime import datetime
import base64
import re
import json
import os
import functools
import uuid
import random
import string
import hashlib
from PIL import Image


def add_functions(app):
	ADMIN_USERNAME = app.config.get("ADMIN_USERNAME", "dev")
	ADMIN_PASSWORD = app.config.get("ADMIN_PASSWORD", "dev")
	ADMIN_LOGINNONCE = ''.join(random.choices(string.ascii_uppercase, k=16))
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
		sha256pwd = hashlib.sha256(
			(ADMIN_PASSWORD + ADMIN_LOGINNONCE).encode("utf-8")
		).hexdigest().lower()
		if username != ADMIN_USERNAME or password.lower() != sha256pwd:
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
		try:
			page = int(request.args.get("page", 1))
		except:
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

	def format_comment(comment):
		attributes = [
			"comment_id", "main_comment_id", "reply_id", "is_reply",
			"like", "create_time", "owner", "parent_owner", "cat_id",
			"content", "is_hidden"
		]
		data = {
			attr: getattr(comment, attr)
			for attr in attributes
		}
		data["images"] = [
			get_url_from_path(x) for x in json.loads(comment.images_path)
		]
		data["nickname"] = get_nickname_by_userid(data["owner"])
		data["avatar"] = get_avatar_by_userid(data["owner"])
		data["parent_nickname"] = get_nickname_by_userid(data["parent_owner"])
		data["parent_avatar"] = get_avatar_by_userid(data["parent_owner"])
		return data

	@app.route("/admin/get_all_comments_api", methods=["GET"])
	@exception_handler
	@admin_login_check
	def admin_get_all_comments_api():
		page_size = 10
		try:
			page = int(request.args.get("page", 1))
		except:
			return jsonify({
				"code": 100,
				"msg": "invalid page",
				"data": {}
			})
		result = (Comment.query.order_by(Comment.create_time.desc())
			.paginate(page, page_size, False))
		resp = []
		for item in result.items:
			resp.append(format_comment(item))
		return jsonify({
			"code": 0,
			"msg": "",
			"data": {
				"resp": resp,
				"maxpage": (result.total + page_size - 1) // page_size
			}
		})
	
	@app.route("/admin/get_comments_by_cat", methods=["GET"])
	@exception_handler
	@admin_login_check
	def admin_get_comments_by_cat():
		page_size = 10
		try:
			page = int(request.args.get("page", 1))
			cat_id = int(request.args.get("cat_id", 1))
		except:
			return jsonify({
				"code": 100,
				"msg": "invalid page or cat_id",
				"data": {}
			})
		result = (Comment.query.order_by(Comment.create_time.desc())
			.filter_by(cat_id=cat_id, is_reply=False).paginate(page, page_size, False))
		resp = []
		for item in result.items:
			resp.append(format_comment(item))
		return jsonify({
			"code": 0,
			"msg": "",
			"data": {
				"resp": resp,
				"maxpage": (result.total + page_size - 1) // page_size
			}
		})
	
	@app.route("/admin/get_comment", methods=["GET"])
	@exception_handler
	@admin_login_check
	def admin_get_comment():
		try:
			comment_id = int(request.args.get("comment_id", -1))
			comment = Comment.query.filter_by(comment_id=comment_id).one_or_none()
			if comment:
				return jsonify({
					"code": 0,
					"msg": "",
					"data": {
						"comment": format_comment(comment)
					}
				})
			raise ValueError("Invalid comment_id")
		except:
			return jsonify({
				"code": 100,
				"msg": "Invalid comment_id",
				"data": {}
			})

	@app.route("/admin/hide_comment_api", methods=["POST"])
	@exception_handler
	@admin_login_check
	def admin_hide_comment_api():
		data = request.get_json()
		comment_id = data.get("comment_id", -1)
		if isinstance(comment_id, int):
			comment = Comment.query.filter_by(comment_id=comment_id).one_or_none()
			if comment:
				comment.is_hidden = True
				db.session.commit()
				return jsonify({
					"code": 0,
					"msg": "",
					"data": {}
				})
		return jsonify({
			"code": 100,
			"msg": "Invalid comment_id.",
			"data": {}
		})

	@app.route("/admin/show_comment_api", methods=["POST"])
	@exception_handler
	@admin_login_check
	def admin_show_comment_api():
		data = request.get_json()
		comment_id = data.get("comment_id", -1)
		if isinstance(comment_id, int):
			comment = Comment.query.filter_by(comment_id=comment_id).one_or_none()
			if comment:
				comment.is_hidden = False
				db.session.commit()
				return jsonify({
					"code": 0,
					"msg": "",
					"data": {}
				})
		return jsonify({
			"code": 100,
			"msg": "Invalid comment_id.",
			"data": {}
		})

	@app.route("/admin/login")
	def admin_login():
		if session.get("verified", False) == True:
			return redirect(url_for("admin_index"))
		return render_template("login.html", nonce=ADMIN_LOGINNONCE)
	
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
	
	@app.route("/admin/comment")
	def admin_comment():
		if session.get("verified", False) == False:
			return redirect(url_for("admin_login"))
		return render_template("comment.html")