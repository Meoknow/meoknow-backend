from flask import request, jsonify, current_app, session
from .util import exception_handler, debug_only
from .model import User
from meoknow import db
from urllib.parse import urlencode
import jwt
import requests
import time
import functools


APPID = current_app.config.get("MINI_PROGRAM_APPID", "dev")
APPSECRET = current_app.config.get("MINI_PROGRAM_APPSECRET", "dev")
JWT_SECRET = current_app.config.get("JWT_SECRET", "dev")

JWT_ALGORITHM = current_app.config.get("JWT_ALGORITHM", "HS512")
EXPIRE_SECONDS = current_app.config.get("JWT_EXPIRE_SECONDS", 30 * 86400) # 1 month

BYPASS_LOGIN_CHECK = current_app.config.get("BYPASS_LOGIN_CHECK", False)

def get_jwt_uid(payload):
	try:
		data = jwt.decode(payload, JWT_SECRET, algorithms=[JWT_ALGORITHM])
		return data["uid"]
	except Exception:
		return False

def check_jwt(payload, check_admin=False):
	try:
		data = jwt.decode(payload, JWT_SECRET, algorithms=[JWT_ALGORITHM])
		if time.time() > data.get("expired", 0): # expired
			return False
		if check_admin and data.get("role", "user") != "admin":
			return False
		return True
	except Exception:
		return False

def gen_jwt(uid, is_admin=False):
	payload = {
		"uid": uid,
		"role": "admin" if is_admin else "user",
		"expired": int(time.time()) + EXPIRE_SECONDS
	}
	return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def login_check(admin=False):
	def decorator(func):
		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			# temporarily disabling login_check
			if BYPASS_LOGIN_CHECK:
				request.user_id = None
				return func(*args, **kwargs)
			if session.get("verified", False):
				request.user_id = "admin"
				return func(*args, **kwargs)
			token = request.headers.get("Auth-Token", "")
			if check_jwt(token) == False:
				return jsonify({
					"code": 1,
					"msg": "Invalid token.",
					"data": {}
				}), 401
			if admin and check_jwt(token, admin) == False:
				return jsonify({
					"code": 3,
					"msg": "Permission Denied.",
					"data": {}
				}), 401
			request.user_id = get_jwt_uid(token)
			return func(*args, **kwargs)
		return wrapper
	return decorator

def wechat_login(js_code):
	'''
		return openid or False
	'''
	try:
		url = "https://api.weixin.qq.com/sns/jscode2session?" + urlencode({
			"appid": APPID,
			"secret": APPSECRET,
			"js_code": js_code,
			"grant_type": "authorization_code"
		})
		resp = requests.get(url, timeout=3).json()
		return resp['openid']
	except:
		return False

def add_functions(app):
	@app.route("/userinfo", methods=["POST"])
	@exception_handler
	@login_check()
	def update_nickname():
		rdata = request.get_json()
		user = User.query.filter_by(user_id=request.user_id).one_or_none()
		nickname = rdata.get("nickname", "")
		avatar = rdata.get("avatar", "")
		if not all([isinstance(nickname, str), isinstance(avatar, str)]):
			return jsonify({
				"code": 100,
				"msg": "Invalid nickname or avatar",
				"data": {}
			})
		user.nickname = nickname
		user.avatar_path = avatar
		db.session.commit()
		return jsonify({
			"code": 0,
			"msg": {},
			"data": {}
		})

	@app.route("/session")
	@exception_handler
	def login():
		code = request.args.get("code", None)
		if code == None:
			return jsonify({
				"code": 100,
				"msg": "Invalid parameter: code.",
				"data": {}
			})
		openid = wechat_login(code)
		if openid:
			user = User.query.filter_by(user_id=openid).one_or_none()
			if user == None:
				user = User(
					user_id=openid,
					nickname="default_username",
					avatar_path=""
				)
				db.session.add(user)
				db.session.commit()
			return jsonify({
				"code": 0,
				"msg": "",
				"data": {
					"token": gen_jwt(openid)
				}
			})
		else:
			return jsonify({
				"code": 101,
				"msg": "Failed in authentication.",
				"data": {}
			})

	@app.route("/gensession")
	@exception_handler
	@debug_only
	def gensession():
		import uuid
		openid = str(uuid.uuid4())
		user = User.query.filter_by(user_id=openid).one_or_none()
		nickname = request.args.get("nickname", "default_username")
		avatar_path = ""
		if user == None:
			user = User(
				user_id=openid,
				nickname=nickname,
				avatar_path=avatar_path
			)
			db.session.add(user)
			db.session.commit()
		return jsonify({
			"code": 0,
			"msg": "",
			"data": {
				"token": gen_jwt(openid, request.args.get("admin", False) != False),
				"user_id": openid
			}
		})

	@app.route("/test/auth")
	@exception_handler
	@debug_only
	@login_check()
	def testauth():
		return jsonify({
			"code": 0,
			"msg": "login success!",
			"data": {}
		})
	
	@app.route("/test/adminauth")
	@exception_handler
	@debug_only
	@login_check(admin=True)
	def testadminauth():
		return jsonify({
			"code": 0,
			"msg": "admin login success!",
			"data": {}
		})
