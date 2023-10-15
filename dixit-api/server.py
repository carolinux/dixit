import flask
from flask import Flask, request, jsonify, make_response, render_template
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS, cross_origin
import redis

from cute_ids import generate_cute_id
from models import Game
from datastore import get_game_by_id, get_all_games, add_game, update_game, get_locked_game_by_id, LockingException, release_lock
import utils
import conf
import atexit
import logging

import json
from datetime import datetime
import os

app = Flask(__name__, static_url_path='',
            static_folder='react_build',
            template_folder='react_build')
app.config['SECRET_KEY'] = conf.SECRET_KEY
app.config["DEBUG"] = True
app.config['SOCK_SERVER_OPTIONS'] = {'ping_interval': 25}
socketio = SocketIO(app)
red = redis.StrictRedis('localhost', 6379, charset="utf-8", decode_responses=True)
logger = logging.getLogger(__name__)


## React Routes ##
@atexit.register
def save(gid=None):
    # save the game data :)
    recs = []
    for g in get_all_games(red):
        if gid is None or g.id == gid:
            recs.append(g.to_json_lite())
    data = {'games': recs}
    fn = os.path.join("./game_data/export_{}.json".format(datetime.now().strftime("%Y%m%d_%H%M%S")))
    with open(fn, 'w') as f:
        json.dump(data, f)


@app.route("/")
def home():
    print("one call at {}".format(datetime.now()))
    return render_template("index.html")


@app.route("/create")
def create():
    return render_template("index.html")


@app.route("/join/<gid>")
def join(gid):
    return render_template("index.html")


@app.route("/board/<gid>")
def board(gid):
    return render_template("index.html")


@app.route("/board/<gid>/winners")
def board_winners(gid):
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
                game = Game(uid, creator=player_name)
                added = add_game(red, game)
                if added:
                    break
        else:
            # logic to handle joining an existing game
            uid = game_id
            game = get_game_by_id(red, uid)
            if game is None:
                flask.abort(400, f"Game {uid} not found to join.")
        try:
            existing_joined_games = utils.get_games_from_cookie(request)
            if uid in existing_joined_games:
                # do not rejoin, silently re-direct the user to the board
                return make_response(jsonify({"game": game.id}))
            game.join(player_name)
            update_game(red, game)
            socketio.emit('update', json.dumps({'data': f"Player {player_name} joined game {game.id}"}), room=game.id)
        except Exception as e:
            print(e)
            flask.abort(400, str(e))
        resp = make_response(jsonify({"game": game.id}))
        resp = utils.generate_response_with_jwt_token(request, resp, player_name, game.id)
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
def games_status_api(gid, jwt_data=None):
    game, player = get_authenticated_game_and_player_or_error(gid, jwt_data)
    game_data = game.serialize_for_status_view(player)
    # get the public state
    return jsonify({"game": game_data})


def get_authenticated_game_and_player_or_error(gid, jwt_data, lock=False):
    joined_games = jwt_data['gids'].split(',')
    players = jwt_data['players'].split(',')
    game_to_player = {}
    for game, matching_player in zip(joined_games, players):
        game_to_player[game] = matching_player

    if gid not in joined_games:
        # the game(s) in the cookie (maybe the user has joined multiple games) are ALL different than the one the request is trying to get info for
        error = "Trying to get data for {} when the game the player is in is {}".format(gid, joined_games)
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
    if not game or game.is_abandoned():
        release_lock(red, gid)
        flask.abort(404)
    player = game_to_player[gid]
    if not game.contains_player(player):
        error = "Player {} is not in game {}".format(player, gid)
        release_lock(red, gid)
        flask.abort(403, error)
    return game, player


@app.route('/games/<gid>/start', methods=['PUT'])
@cross_origin()
@utils.authenticate_with_cookie_token
def games_start(gid, jwt_data=None):
    game, player = get_authenticated_game_and_player_or_error(gid, jwt_data, lock=True)
    try:
        game.start()
        update_game(red, game)
        socketio.emit('update', json.dumps({'data': "Game started"}), room=gid)
    except Exception as e:
        print(e)
        flask.abort(400)
    game_data = game.serialize_for_status_view(player)
    return jsonify({"game": game_data})


@app.route('/games/<gid>/set', methods=['PUT'])
@cross_origin()
@utils.authenticate_with_cookie_token
def games_set_card(gid, jwt_data=None):
    game, player = get_authenticated_game_and_player_or_error(gid, jwt_data, lock=True)
    try:
        card = request.json['card']
        phrase = request.json.get('phrase')
        if phrase:
            game.set_narrator_card(player, card, phrase)
        else:
            game.set_decoy_card(player, card)
        update_game(red, game)
        if phrase:
            socketio.emit('update', json.dumps({'data': f"{player} chose their narrator card"}), room=gid)
        else:
            socketio.emit('update', json.dumps({'data': f"{player} chose their decoy card"}), room=gid)
    except Exception as e:
        print(e)
        flask.abort(400)
    game_data = game.serialize_for_status_view(player)
    return jsonify({"game": game_data})


@app.route('/games/<gid>/vote', methods=['PUT'])
@cross_origin()
@utils.authenticate_with_cookie_token
def games_vote_card(gid, jwt_data=None):
    import traceback
    game, player = get_authenticated_game_and_player_or_error(gid, jwt_data, lock=True)
    try:
        card = request.json['vote']  # this is the 'string' of the card
        game.cast_vote(player, card)
        print("after cast vote")
        update_game(red, game)
        socketio.emit('update', json.dumps({'data': f"{player} cast their vote"}), room=gid)
    except Exception as e:
        print(traceback.print_exc())
        flask.abort(400, str(e))
    game_data = game.serialize_for_status_view(player)
    return jsonify({"game": game_data})


@app.route('/games/<gid>/next', methods=['PUT'])
@cross_origin()
@utils.authenticate_with_cookie_token
def games_next_round(gid, jwt_data=None):
    game, player = get_authenticated_game_and_player_or_error(gid, jwt_data, lock=True)
    try:
        game.start_next_round()
        update_game(red, game)
        socketio.emit('update', json.dumps({'data': "Next round started"}), room=gid)
    except Exception as e:
        print(e)
        flask.abort(400, str(e))
    game_data = game.serialize_for_status_view(player)
    return jsonify({"game": game_data})



@app.route('/games/<gid>/abandon', methods=['PUT'])
@cross_origin()
@utils.authenticate_with_cookie_token
def abandon(gid, jwt_data=None):
    game, player = get_authenticated_game_and_player_or_error(gid, jwt_data, lock=True)
    try:
        game.abandon(player)
        update_game(red, game)
        socketio.emit('update', json.dumps({'data': "Game abandoned"}), room=gid)
    except Exception as e:
        print(e)
        flask.abort(400, str(e))
    game_data = game.serialize_for_status_view(player)
    return jsonify({"game": game_data})


@app.route('/games/<gid>/rematch', methods=['PUT'])
@cross_origin()
@utils.authenticate_with_cookie_token
def restart(gid, jwt_data=None):
    game, player = get_authenticated_game_and_player_or_error(gid, jwt_data, lock=True)
    try:
        save(game.id)
        game.start_rematch()
        update_game(red, game)
        socketio.emit('update', json.dumps({'data': "Game restarted"}), room=gid)
    except Exception as e:
        print(e)
        flask.abort(400, str(e))
    game_data = game.serialize_for_status_view(player)
    return jsonify({"game": game_data})




@socketio.on('join')
def join_websocket(data):
    join_room(data['room'])
    emit("update", json.dumps({"data": f"Welcome to game {data['room']}"}))


if __name__ == '__main__':
    socketio.run(app, port=8000, host='0.0.0.0')
    # app.run(port=5000, threaded=False, debug=True) #local
