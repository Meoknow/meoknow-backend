from flask import jsonify, request, abort, send_file, current_app
from meoknow import db
from .util import exception_handler, format_time, format_timestamp
from .auth import login_check
from .model import Comment, User, Comment_Like, CatInfo
import json, uuid, re, base64, os
from io import BytesIO
from PIL import Image

def get_url_from_path(img_path):
	scheme = current_app.config.get("URI_SCHEME", "http")
	authority = current_app.config.get("URI_AUTHORITY", "localhost:5000")
	prefix = f"{scheme}://{authority}"
	return prefix + "/comment_photo/" + img_path

def is_liked_by_current_user(comment_id):
	return Comment_Like.query.filter_by(
		user_id=request.user_id,
		comment_id=comment_id
	).one_or_none() != None

def get_avatar_by_userid(userid):
	user = User.query.filter_by(user_id=userid).one_or_none()
	if user:
		return user.avatar_path
	raise ValueError("Invalid Userid")

def get_nickname_by_userid(userid):
	user = User.query.filter_by(user_id=userid).one_or_none()
	if user:
		return user.nickname
	raise ValueError("Invalid Userid")

def add_functions(app):
	def save_img(img_64):
		try:
			file_fmt = re.findall("^data:image/(.+?);base64,", img_64)
			if file_fmt == None:
				return None
			img_64 = re.sub("^data:image/.+;base64,", "", img_64)
			byte_data = base64.b64decode(img_64)
			img = Image.open(BytesIO(byte_data))
			img_name = "%s.%s" % (str(uuid.uuid4()).replace("-", ""), file_fmt[0])
			img_url = os.path.join(app.instance_path, "images", img_name)
			img.save(img_url)
			return img_name
		except Exception as e:
			return None
	
	@app.route("/cats/<int:cat_id>/comments/", methods=["POST"])
	@exception_handler
	@login_check()
	def new_comments(cat_id):
		if CatInfo.query.filter_by(cat_id=cat_id).one_or_none() == None:
			return jsonify({
				"code": 100,
				"msg": "Invalid parameter: cat_id.",
				"data": {}
			}), 400
		
		rdata = request.get_json()

		if rdata is None:
			return jsonify({
				"code": 101,
				"msg": "Invalid Content.",
				"data": {}
			}), 400

		content = rdata.get("content", "")
		images = rdata.get("images", [])
		paths = []

		if content == "" or not isinstance(content, str):
			return jsonify({
				"code": 101,
				"msg": "Invalid Content.",
				"data": {}
			}), 400
		
		try:
			if len(images) > 9 or not isinstance(images, list):
				raise ValueError("Too Many Images.")
			for img_64 in images:
				path = save_img(img_64)
				if path:
					paths.append(path)
				else:
					raise ValueError("Invalid Image.")
		except Exception:
			return jsonify({
				"code": 102,
				"msg": "Invalid Image.",
				"data": {}
			}), 400

		comment = Comment(
			like=0,
			owner=request.user_id,
			cat_id=cat_id,
			content=content,
			images_path=json.dumps(paths),
			is_hidden=False,
		)

		db.session.add(comment)
		db.session.commit()
		return jsonify({
			"code": 0,
			"msg": "",
			"data": {}
		}), 200
	
	@app.route("/cats/<int:cat_id>/comments/", methods=["GET"])
	@exception_handler
	@login_check()
	def get_comments(cat_id):
		rdata = request.args
		try:
			page = int(rdata.get("page", 1))
			page_size = int(rdata.get("page_size", 20))
			if page <= 0 or page_size <= 0:
				raise ValueError("Invalid page_size or page.")
		except Exception as e:
			return jsonify({
				"code": 101,
				"msg": "Invalid page_size or page.",
				"data": {}
			}), 400
		
		cat = CatInfo.query.filter_by(cat_id=cat_id).one_or_none()
		if cat == None:
			return jsonify({
				"code": 100,
				"msg": "Invalid parameter: cat_id.",
				"data": {}
			}), 400

		result = Comment.query.filter_by(
			cat_id=cat_id,
			is_hidden=False
		).order_by(Comment.create_time.desc()).paginate(page, page_size, False)
		total = result.total
		items = result.items

		resp = []
		for item in items:
			images_path = json.loads(item.images_path)
			data = {
				"comment_id": item.comment_id,
				"content": item.content,
				"images": [get_url_from_path(x) for x in images_path],
				"like": item.like,
				"avatar": get_avatar_by_userid(item.owner),
				"username": get_nickname_by_userid(item.owner),
				"is_liked": is_liked_by_current_user(item.comment_id)
			}
			resp.append(data)
		
		return jsonify({
			"code": 0,
			"msg": "",
			"data": {
				"total": total,
				"comments": resp
			}
		}), 200
	
	@app.route("/comments/<int:comment_id>", methods=["GET"])
	@exception_handler
	@login_check()
	def get_comment(comment_id):
		rdata = request.args
		
		comment = Comment.query.filter_by(
			comment_id=comment_id,
			is_hidden=False
		).one_or_none()
		if comment == None:
			return jsonify({
				"code": 100,
				"msg": "Invalid parameter: comment_id.",
				"data": {}
			}), 400
		
		resp = {
			"cat_id": comment.cat_id,
			"is_liked": is_liked_by_current_user(comment.comment_id),
			"like": comment.like,
			"time": format_time(comment.create_time),
			"timestamp": format_timestamp(comment.create_time),
			"username": get_nickname_by_userid(comment.owner),
			"avatar": get_avatar_by_userid(comment.owner)
		}

		return jsonify({
			"code": 0,
			"msg": "",
			"data": resp
		})
	
	@app.route("/comments/<int:comment_id>", methods=["DELETE"])
	@exception_handler
	@login_check(admin=True)
	def delete_comment(comment_id):
		comment = Comment.query.filter_by(comment_id=comment_id).one_or_none()
		if comment == None:
			return jsonify({
				"code": 100,
				"msg": "Invalid parameter: comment_id.",
				"data": {}
			}), 400
		comment.is_hidden = True
		db.session.commit()
		return jsonify({
			"code": 0,
			"msg": "",
			"data": {}
		}), 200
	
	@app.route("/comments/<int:comment_id>/like", methods=["PUT"])
	@exception_handler
	@login_check()
	def like_comment(comment_id):
		comment = Comment.query.filter_by(
			comment_id=comment_id,
			is_hidden=False
		).one_or_none()
		if comment == None:
			return jsonify({
				"code": 100,
				"msg": "Invalid parameter: comment_id.",
				"data": {}
			}), 400

		record = Comment_Like.query.filter_by(
			comment_id=comment_id,
			user_id=request.user_id
		).one_or_none()

		if record == None:
			comment.like += 1
			cl = Comment_Like(
				comment_id=comment_id,
				user_id=request.user_id,
				owner=comment.owner
			)
			db.session.add(cl)
			db.session.commit()
		
		return jsonify({
			"code": 0,
			"msg": "",
			"data": {
				"like": comment.like
			}
		}), 200
	
	@app.route("/comments/<int:comment_id>/like", methods=["DELETE"])
	@exception_handler
	@login_check()
	def unlike_comment(comment_id):
		comment = Comment.query.filter_by(
			comment_id=comment_id,
			is_hidden=False
		).one_or_none()
		if comment == None:
			return jsonify({
				"code": 100,
				"msg": "Invalid parameter: comment_id.",
				"data": {}
			}), 400

		record = Comment_Like.query.filter_by(
			comment_id=comment_id,
			user_id=request.user_id
		).one_or_none()

		if record:
			comment.like -= 1
			db.session.delete(record)
			db.session.commit()
		
		return jsonify({
			"code": 0,
			"msg": "",
			"data": {
				"like": comment.like
			}
		}), 200
	
	@app.route("/status/likes", methods=["GET"])
	@exception_handler
	@login_check()
	def recent_liked():
		rdata = request.args
		try:
			page = int(rdata.get("page", 1))
			page_size = int(rdata.get("page_size", 20))
			if page <= 0 or page_size <= 0:
				raise ValueError("Invalid page_size or page.")
		except Exception as e:
			return jsonify({
				"code": 100,
				"msg": "Invalid page_size or page.",
				"data": {}
			}), 400
		result = Comment_Like.query.filter_by(
			owner=request.user_id
		).order_by(Comment_Like.create_time.desc()).paginate(page, page_size)
		total = result.total
		likes = []
		for item in result.items:
			likes.append({
				"username": get_nickname_by_userid(item.user_id),
				"avatar": get_avatar_by_userid(item.user_id),
				"time": format_time(item.create_time),
				"timestamp": format_timestamp(item.create_time),
				"comment_id": item.comment_id
			})

		resp = {
			"count": total,
			"likes": likes
		}

		return jsonify({
			"code": 0,
			"msg": "",
			"data": resp
		}), 200

	@app.route("/comment_photo/<string:photo_name>", methods=["GET"])
	def get_photo(photo_name):
		img_url = os.path.join(app.instance_path, "images", photo_name)
		if os.path.exists(img_url):
			if os.path.isdir(img_url):
				abort(404)
			img_fmt = photo_name.split('.')[-1]
			return send_file(
				img_url,
				mimetype='image/'+img_fmt,
				as_attachment=False,
				attachment_filename=photo_name
			)
		else:
			abort(404)