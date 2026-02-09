"""
AI Handler for Dixit game.

Processes AI player turns based on the current game state.
The core logic is in do_one_ai_action() which is shared between
the web server (sync/gevent) and Discord bot (async).
"""

import json
import random
import time
from pathlib import Path

from models import Game, WAITING_FOR_NARRATOR, WAITING_FOR_PLAYERS, WAITING_FOR_VOTES, ROUND_REVEALED
from datastore import get_locked_game_by_id, update_game, release_lock, LockingException
import claude_service


def do_one_ai_action(redis_client, gid: str) -> dict | None:
    """
    Lock the game, execute one AI action if needed, update game.

    Returns a dict describing what happened, or None if no action was needed.
    The dict has keys:
        - 'action': 'narrator' | 'decoy' | 'vote'
        - 'player': the AI player name
        - 'card': the card played/voted
        - 'phrase': (narrator only) the clue phrase
        - 'game_state': the game state after the action
    """
    try:
        game = get_locked_game_by_id(redis_client, gid)
    except LockingException:
        print(f"Could not acquire lock for AI turn in game {gid}")
        return None

    if game is None or game.is_abandoned():
        release_lock(redis_client, gid)
        return None

    result = _execute_ai_action(game, redis_client, gid)
    if result is None:
        release_lock(redis_client, gid)
    return result


def _execute_ai_action(game: Game, redis_client, gid: str) -> dict | None:
    """Check game state and execute one AI action. Returns result or None."""

    if game.currentState == WAITING_FOR_NARRATOR:
        narrator = game.get_narrator()
        if game.is_ai_player(narrator):
            hand = game.currentRound['allocations'][narrator]
            card = random.choice(hand)
            phrase = claude_service.generate_narrator_clue(card)
            game.set_narrator_card(narrator, card, phrase)
            update_game(redis_client, game)
            print(f"AI {narrator} played narrator card {card} with phrase: {phrase}")
            return {
                'action': 'narrator',
                'player': narrator,
                'card': card,
                'phrase': phrase,
                'game_state': game.currentState,
            }

    elif game.currentState == WAITING_FOR_PLAYERS:
        for player in game.get_non_narrators():
            if game.is_ai_player(player) and not game.has_set_card(player):
                hand = game.currentRound['allocations'][player]
                phrase = game.currentRound['phrase']
                hand_descriptions = {c: claude_service.get_card_description(c) for c in hand}
                try:
                    card = claude_service.select_best_card(phrase, hand_descriptions)
                    if card not in hand:
                        card = random.choice(hand)
                except Exception as e:
                    print(f"Error in AI decoy selection: {e}")
                    card = random.choice(hand)
                game.set_decoy_card(player, card)
                update_game(redis_client, game)
                print(f"AI {player} played decoy card {card} for phrase: {phrase}")
                return {
                    'action': 'decoy',
                    'player': player,
                    'card': card,
                    'game_state': game.currentState,
                }

    elif game.currentState == WAITING_FOR_VOTES:
        for player in game.get_non_narrators():
            if game.is_ai_player(player) and not game.has_voted(player):
                played_cards = game.currentRound['allCards']
                own_decoy = game.currentRound['decoys'][player]
                phrase = game.currentRound['phrase']
                votable_cards = [c for c in played_cards if c != own_decoy]
                card_descriptions = {c: claude_service.get_card_description(c) for c in votable_cards}
                try:
                    voted_card = claude_service.vote_for_card(phrase, card_descriptions)
                    if voted_card not in votable_cards:
                        voted_card = random.choice(votable_cards)
                except Exception as e:
                    print(f"Error in AI voting: {e}")
                    voted_card = random.choice(votable_cards)
                game.cast_vote(player, voted_card)
                update_game(redis_client, game)
                print(f"AI {player} voted for card {voted_card} (phrase: {phrase})")
                return {
                    'action': 'vote',
                    'player': player,
                    'card': voted_card,
                    'game_state': game.currentState,
                }

    return None


# --- Web server (sync/gevent) entry point ---

def process_ai_turns(redis_client, socketio, gid: str):
    """
    Process all pending AI actions for the current game state.
    Uses time.sleep (gevent-patched) and socketio for notifications.
    """
    time.sleep(random.uniform(1.5, 3.0))

    result = do_one_ai_action(redis_client, gid)
    if result is None:
        return

    # Notify web clients
    action = result['action']
    player = result['player']
    if action == 'narrator':
        msg = f"{player} chose their narrator card"
    elif action == 'decoy':
        msg = f"{player} chose their decoy card"
    elif action == 'vote':
        msg = f"{player} cast their vote"
    else:
        msg = f"{player} took an action"

    socketio.emit('update', json.dumps({'data': msg}), room=gid)

    # Recursively process more AI turns
    process_ai_turns(redis_client, socketio, gid)


# Note: Card descriptions and clues are loaded by claude_service module
