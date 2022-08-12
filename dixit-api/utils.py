import datetime
from functools import wraps
import flask
import jwt
import conf


def authenticate_with_cookie_token(f):
    """Validates that token is correct for game & player, otherwise error"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        req = flask.request
        cookies = req.cookies.to_dict()
        token = cookies.get('token')
        if not token:
            flask.abort(401)
        try:
            data = jwt.decode(token, conf.secret_key, algorithms=["HS256"])
        except Exception as e:  # signature has expired or payload not correctly signed
            print(e)
            flask.abort(403, str(e))
        return f(*args, **kwargs, jwt_data=data)
    return decorated_function


def create_token(player_names, gids, expiration_date):
    """The token contains two parallel lists of player_names, game_ids for the nickname the player has chosen for each game they have participated."""
    return jwt.encode({'players': player_names, 'gids': gids, 'exp': expiration_date},
                       conf.secret_key, algorithm="HS256")


def get_games_from_cookie(request):
    cookies = request.cookies.to_dict()
    token = cookies.get('token')
    if token is None:
        return []
    data = jwt.decode(token, conf.secret_key, algorithms=["HS256"])
    return data.get('gids', [])


def generate_response_with_jwt_token(request, response, player_name, gid):
    """Generate a jwt token which encodes all the games the person is a member of (usually will be only one).

    Note: the players and gids are added just for readability and debuggability. Only the token is checked for authentication.
    """
    cookies = request.cookies.to_dict()
    expiration_date = datetime.datetime.utcnow() + datetime.timedelta(minutes=120)
    if not cookies.get('token'):
        response.set_cookie("players", player_name, httponly=True, samesite='Strict', expires=expiration_date)
        response.set_cookie("gids", gid, httponly=True, samesite='Strict', expires=expiration_date)
        response.set_cookie("token", create_token(player_name, gid, expiration_date=expiration_date), httponly=True, samesite='Strict', expires=expiration_date)
    else:
        token = cookies.get('token')
        data = jwt.decode(token, conf.secret_key, algorithms=["HS256"])
        existing_names = data.get('players')
        existing_games = data.get('gids')
        new_names = existing_names + ',' + player_name
        new_games = existing_games + ',' + gid
        response.set_cookie("players", new_names, httponly=True, samesite='Strict', expires=expiration_date)
        response.set_cookie("gids", new_games, httponly=True, samesite='Strict', expires=expiration_date)
        response.set_cookie("token", create_token(new_names, new_games, expiration_date=expiration_date), httponly=True, samesite='Strict', expires=expiration_date)
    return response
