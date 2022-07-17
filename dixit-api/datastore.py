"""Functionality that queries the Redis data store."""
import time
import uuid
from models import Game


class LockingException(Exception):
    pass


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


def acquire_lock(cli, lock_name, timeout=5):
    identifier = str(uuid.uuid4())
    end = time.time() + timeout
    while time.time() < end:
        if cli.setnx('lock:' + lock_name, identifier):
            # setting a lock with a short TTL, so that even if the client goes bust and doesn't unlock,
            # the lock is released
            cli.set('lock:' + lock_name, identifier, ex=2)
            return identifier
        time.sleep(.001)
    return False


def release_lock(cli, lock_name):
    cli.delete('lock:' + lock_name)


def get_locked_game_by_id(cli, gid):
    lock_acquired = acquire_lock(cli, gid)
    if lock_acquired is False:
        raise LockingException()
    game_json = cli.hget("games", gid)
    return Game.from_json(game_json)


def add_game(cli, g: Game) -> bool:
    """Add game with id if the game id doesn't already exist."""
    return cli.hsetnx("games", g.id, g.to_json())


def update_game(cli, g: Game):
    cli.hset("games", g.id, g.to_json())
    release_lock(cli, g.id)

