import datetime
from functools import wraps
import flask
from flask import jsonify, app
import jwt
import conf


def authenticate_with_cookie_token(f):
    """Validates that token is correct for game & player, otherwise error"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        req = flask.request
        cookies = req.cookies.to_dict()
        player = cookies.get('player')
        gid = cookies.get('gid')
        token = cookies.get('token')
        if not player or not gid or not token:
            flask.abort(401)
        try:
            data = jwt.decode(token, conf.secret_key, algorithms=["HS256"])
        except Exception as e: # signature has expired
            print(e)
            flask.abort(403, str(e))
        if data.get('public_id') != player or data.get('gid') != gid:
            flask.abort(403)
        return f(*args, **kwargs)
    return decorated_function


def create_token(player_name, gid):
    return jwt.encode({'public_id': player_name, 'gid': gid, 'exp': datetime.datetime.now() + datetime.timedelta(minutes=120)},
                       conf.secret_key, algorithm="HS256")
