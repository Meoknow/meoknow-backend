import base64, re, random, time, json, os

from flask import (
	flash, g, redirect, render_template, request, session, url_for, send_from_directory, send_file, current_app, abort
)
from flask.helpers import make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref
from werkzeug.utils import secure_filename
from datetime import datetime

from meoknow import db
from .model import CatMarker, CatInfo
from .util import exception_handler, format_time, format_timestamp
from .auth import login_check
from .comment import get_nickname_by_userid, get_url_from_path, get_avatar_by_userid

MARKER_COUNT_MAX = 10
MARKER_TIME_MAX_MINUTE = 120

def add_functions(app):

	@app.route("/map/", methods=["GET"])
	@exception_handler
	@login_check()
	def get_markers():
		markers = CatMarker.query.order_by(CatMarker.upl_time).limit(MARKER_COUNT_MAX)
		data = []
		for marker in markers:
			
			if (datetime.utcnow() - marker.upl_time).seconds / 60 < MARKER_TIME_MAX_MINUTE:
				
				if marker.user_id == None:
					username = None
					avatar = None
				else:
					try:
						username = get_nickname_by_userid(marker.user_id)
						avatar = get_avatar_by_userid(marker.user_id)
					except ValueError as e:
						print(e)
						username = None
						avatar = None

				data.append({
					"id": marker.id,
					"latitude": marker.latitude,
					"longitude": marker.longitude,
					"cat_id": marker.cat_id,
					"username": username,
					"avatar": avatar,
					"time": format_time(marker.upl_time),
					"timestamp": format_timestamp(marker.upl_time),
					"img_url": marker.img_url
				})
		
		return {"code":0, "msg":"", "data":data}

	@app.route("/map/", methods=["POST"])
	@exception_handler
	@login_check()
	def post_marker():
		rdata = request.get_json()
		latitude = rdata.get("latitude")
		longitude = rdata.get("longitude")
		cat_id = rdata.get("cat_id")
		anonymous = rdata.get("anonymous")
		img_url = rdata.get("img_url")
		user_id = request.user_id
		if anonymous == True:
			user_id = None
		if CatInfo.query.filter_by(cat_id=cat_id).one_or_none() == None:
			return ({"code":100, "msg": "Invalid cat_id", "data": {}}, 400)
		
		marker = CatMarker(
			latitude = latitude,
			longitude = longitude,
			cat_id = cat_id,
			user_id = user_id,
			img_url = img_url
		)

		db.session.add(marker)
		db.session.commit()

		return {"code":0, "msg":"", "data":{}}