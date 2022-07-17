"""Functionality that queries the Redis data store."""
from models import Game


def get_all_games(cli):
    games = cli.hgetall("games")
    res = []
    for k, v in games.items():
        res.append(Game.from_json(v))
    return res


def get_game_by_id(cli, gid):
    game_json = cli.hget("games", gid)
    #print(f"Game json for {gid}: {game_json}, type={type(game_json)}")
    if game_json is None:
        #print(f"game with id {gid} not found")
        return None
    return Game.from_json(game_json)


def get_locked_game_by_id(cli, gid):
    game_json = cli.hget("games", gid)
    return Game.from_json(game_json)


def add_game(cli, g: Game):
    cli.hset("games", g.id, g.to_json())


def update_game(cli, g: Game):
    cli.hset("games", g.id, g.to_json())
