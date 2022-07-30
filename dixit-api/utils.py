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
        players = cookies.get('players')
        gids = cookies.get('gids')
        token = cookies.get('token')
        if not players or not gids or not token:
            flask.abort(401)
        try:
            data = jwt.decode(token, conf.secret_key, algorithms=["HS256"])
        except Exception as e:  # signature has expired
            print(e)
            flask.abort(403, str(e))
        if data.get('public_ids') != players or data.get('gids') != gids:
            flask.abort(403)
        return f(*args, **kwargs)
    return decorated_function


def create_token(player_name, gid):
    return jwt.encode({'public_ids': player_name, 'gids': gid, 'exp': datetime.datetime.now() + datetime.timedelta(minutes=120)},
                       conf.secret_key, algorithm="HS256")


def get_games_from_cookie(request):
    cookies = request.cookies.to_dict()
    token = cookies.get('token')
    if token is None:
        return []
    data = jwt.decode(token, conf.secret_key, algorithms=["HS256"])
    return data.get('gids', [])


def generate_response_with_jwt_token(request, response, player_name, gid):
    """Generate a jwt token which encodes all the games the person is a member of (usually will be only one)."""
    cookies = request.cookies.to_dict()
    if not cookies.get('token'):
        response.set_cookie("players", player_name, httponly=True, samesite='Strict')
        response.set_cookie("gids", gid, httponly=True, samesite='Strict')
        response.set_cookie("token", create_token(player_name, gid), httponly=True, samesite='Strict')
    else:
        existing_names = cookies.get('players')
        existing_games = cookies.get('gids')
        new_names = existing_names + ',' + player_name
        new_games = existing_games + ',' + gid
        response.set_cookie("players", new_names, httponly=True, samesite='Strict')
        response.set_cookie("gids", new_games, httponly=True, samesite='Strict')
        response.set_cookie("token", create_token(new_names, new_games), httponly=True, samesite='Strict')
    return response
