from datetime import timedelta
from flask import jsonify, current_app
import functools
import traceback

TIME_DELTA = current_app.config.get("TIME_DELTA", 8)

def exception_handler(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # TODO: save log
            print(traceback.format_exc())
            return jsonify({
                "code": 2,
                "msg": "Server internal error.",
                "data": {}
            }), 500
    return wrapper

def debug_only(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not current_app.debug and not current_app.testing:
            return jsonify({
                "code": -1,
                "msg": "debug function is disabled in production mode.",
                "data": {}
            }), 400
        return func(**kwargs)
    return wrapper

def format_time(now):
    now = now + timedelta(hours=TIME_DELTA)
    return now.strftime('%Y-%m-%d %H:%M:%S')

def format_timestamp(now):
    now = now + timedelta(hours=TIME_DELTA)
    return int(now.timestamp())
