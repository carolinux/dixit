import flask
from flask import Flask, request, jsonify, make_response, render_template
# from flask_socketio import SocketIO, emit
from flask_cors import CORS, cross_origin
import redis

from cute_ids import generate_cute_id
from models import Game
from datastore import get_game_by_id, get_all_games, add_game, update_game, get_locked_game_by_id, LockingException
import utils
import conf
import atexit

import json
from datetime import datetime
import os

app = Flask(__name__, static_url_path='',
            static_folder='react_build',
            template_folder='react_build')
app.config['SECRET_KEY'] = conf.secret_key
app.config["DEBUG"] = True
cors = CORS(app)
# origins=["http://127.0.0.1:3000"], headers=['Content-Type'], expose_headers=['Access-Control-Allow-Origin'], supports_credentials=True
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['CORS_SUPPORTS_CREDENTIALS'] = True
app.config['CORS_SUPPORTS_CREDENTIALS'] = True
app.config['CORS_ORIGINS'] = ["http://127.0.0.1:3000"]
app.config['CORS_EXPOSE_HEADERS'] = ['Access-Control-Allow-Origin']

red = redis.StrictRedis('localhost', 6379, charset="utf-8", decode_responses=True)


## React Routes ##
@atexit.register
def shutdown():
    # save the game data :)
    recs = []
    for  g in get_all_games(red):
        recs.append(g.to_json_lite())
    data = {'games': recs}
    fn = os.path.join("./game_data/export_{}.json".format(datetime.now().strftime("%Y%m%d_%H%M%S")))
    with open(fn, 'w') as f:
        json.dump(data, f)


@app.route("/")
def home():
    print("one call at {}".format(datetime.now()))
    return render_template("index.html")


@app.route("/login/<gid>")
def login(gid):
    return render_template("index.html")


@app.route("/board/<gid>")
def board(gid):
    return render_template("index.html")


@app.route("/board/<gid>/winners")
def board_winners():
    return render_template("index.html")

## End of React Routes ##



@app.route('/games', methods=['POST', 'GET'])
@cross_origin()
def games_api():
    if request.method == 'POST':
        player_name = request.json['player']
        game_id = request.json["game"]
        if game_id == "new":
            while True:
                uid = generate_cute_id()
                break  # FIXME need to generate an id that doesn't already exist in redis
                #if uid not in games:
                #    break
            game = Game(uid)
            add_game(red, game)
        else:
            uid = game_id
            game = get_game_by_id(red, uid)

        try:
            game.join(player_name)
            update_game(red, game)
        except Exception as e:
            print(e)
            flask.abort(400, str(e))
        resp = make_response(jsonify({"game": game.id}))
        resp.set_cookie("player", player_name, httponly=True, samesite='Strict')
        resp.set_cookie("gid", game.id, httponly=True, samesite='Strict')
        resp.set_cookie("token", utils.create_token(player_name, game.id), httponly=True, samesite='Strict')
        return resp

    else:
        if request.args.get('joinable_for_player'):
            player = request.args.get('joinable_for_player')
        else:
            player = None
        games = get_all_games(red)
        return jsonify({"games": [g.serialize_for_list_view(joinable_for_player=player) for g in games]})


@app.after_request
def creds(response):
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Origin'] = "http://127.0.0.1:3000"
    return response


@app.route('/games/<gid>', methods=['GET'])
@cross_origin()
@utils.authenticate_with_cookie_token
def games_status_api(gid):
    if request.method == "GET":
        ### verify that game exists and current request is allowed to get its general state and their personal data ###
        game, player = get_authenticated_game_and_player_or_error(gid, request)
        ### end verify ###
        game_data = game.serialize_for_status_view(player)
        # get the public state
        return jsonify({"game": game_data})


def get_authenticated_game_and_player_or_error(gid, request, lock=False):
    intended_game = request.cookies.to_dict()['gid']
    player = request.cookies.to_dict()['player']
    if intended_game != gid:
        # the game in the cookie is different than the one the request is trying to get info for
        error = "Trying to get data for {} when the game the player is in is {}".format(gid, intended_game)
        print(error)
        flask.abort(403, error)
    if lock:
        try:
            game = get_locked_game_by_id(red, gid)
        except LockingException:
            print(f"Could not acquire lock for {gid}")
            flask.abort(400, error)
    else:
        game = get_game_by_id(red, gid)
    if not game:
        flask.abort(404)
    if not game.contains_player(player):
        error = "Player {} is not in game {}".format(player, gid)
        print(error)
        flask.abort(403, error)
    return game, player


def get_authenticated_game_and_player_or_error_for_resume(request):
    intended_game = request.cookies.to_dict()['gid']
    player = request.cookies.to_dict()['player']
    game = get_game_by_id(red, intended_game)
    if not game:
        flask.abort(404)
    if game.has_ended():
        error = "Game {} has ended. Deleting cookie.".format(game.id)
        print(error)
        resp = make_response(error, 403)
        resp.set_cookie("player", '', httponly=True, samesite='Strict', expires=0)
        resp.set_cookie("gid", '', httponly=True, samesite='Strict', expires=0)
        resp.set_cookie("token", '', httponly=True, samesite='Strict', expires=0)
        flask.abort(resp)
    if not game.contains_player(player):
        error = "Player {} is not in game {}".format(player, intended_game)
        print(error)
        flask.abort(403, error)
    return game, player


@app.route('/games/<gid>/start', methods=['PUT'])
@cross_origin()
@utils.authenticate_with_cookie_token
def games_start(gid):
    game, player = get_authenticated_game_and_player_or_error(gid, request, lock=True)
    try:
        game.start()
        update_game(red, game)
    except Exception as e:
        print(e)
        flask.abort(400)
    game_data = game.serialize_for_status_view(player)
    return jsonify({"game": game_data})


@app.route('/games/<gid>/set', methods=['PUT'])
@cross_origin()
@utils.authenticate_with_cookie_token
def games_set_card(gid):
    game, player = get_authenticated_game_and_player_or_error(gid, request, lock=True)
    try:
        card = request.json['card']
        phrase = request.json.get('phrase')
        if phrase:
            game.set_narrator_card(player, card, phrase)
        else:
            game.set_decoy_card(player, card)
        update_game(red, game)
    except Exception as e:
        print(e)
        flask.abort(400)
    game_data = game.serialize_for_status_view(player)
    return jsonify({"game": game_data})


@app.route('/games/<gid>/vote', methods=['PUT'])
@cross_origin()
@utils.authenticate_with_cookie_token
def games_vote_card(gid):
    import traceback
    print('before getting game')
    game, player = get_authenticated_game_and_player_or_error(gid, request, lock=True)
    print("after getting game")
    try:
        card = request.json['vote']  # this is the 'string' of the card
        game.cast_vote(player, card)
        print("after cast vote")
        update_game(red, game)
    except Exception as e:
        print(traceback.print_exc())
        flask.abort(400, str(e))
    game_data = game.serialize_for_status_view(player)
    return jsonify({"game": game_data})


@app.route('/games/<gid>/next', methods=['PUT'])
@cross_origin()
@utils.authenticate_with_cookie_token
def games_next_round(gid):
    game, player = get_authenticated_game_and_player_or_error(gid, request, lock=True)
    try:
        game.start_next_round()
        update_game(red, game)
    except Exception as e:
        print(e)
        flask.abort(400, str(e))
    game_data = game.serialize_for_status_view(player)
    return jsonify({"game": game_data})


@app.route('/games/resume', methods=['GET'])
@cross_origin()
@utils.authenticate_with_cookie_token
def games_resume_from_cookie():
    game, player = get_authenticated_game_and_player_or_error_for_resume(request)
    return jsonify({"game": game.id, 'player': player})


if __name__ == '__main__':
    app.run(port=5000, threaded=False, debug=False, host="0.0.0.0")
    # app.run(port=5000, threaded=False, debug=True) #local
