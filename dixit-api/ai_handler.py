"""
AI Handler for Dixit game.

Processes AI player turns based on the current game state.
"""

import json
import random
import time
from pathlib import Path

from models import Game, WAITING_FOR_NARRATOR, WAITING_FOR_PLAYERS, WAITING_FOR_VOTES, ROUND_REVEALED
from datastore import get_locked_game_by_id, update_game, release_lock, LockingException
import claude_service


def process_ai_turns(redis_client, socketio, gid: str):
    """
    Process all pending AI actions for the current game state.

    This function should be called after any game state transition.
    It will handle AI turns sequentially with delays to feel natural.

    Args:
        redis_client: Redis client for game persistence
        socketio: SocketIO instance for real-time updates
        gid: Game ID
    """
    # Add a small delay before AI acts (feels more natural)
    time.sleep(random.uniform(1.5, 3.0))

    # Re-fetch the game state (it may have changed)
    try:
        game = get_locked_game_by_id(redis_client, gid)
    except LockingException:
        print(f"Could not acquire lock for AI turn in game {gid}")
        return

    if game is None or game.is_abandoned():
        release_lock(redis_client, gid)
        return

    try:
        _process_ai_turns_internal(game, redis_client, socketio, gid)
    except Exception as e:
        print(f"Error processing AI turns: {e}")
        import traceback
        traceback.print_exc()
        release_lock(redis_client, gid)


def _process_ai_turns_internal(game: Game, redis_client, socketio, gid: str):
    """Internal implementation of AI turn processing."""

    # Check if narrator is AI and needs to play
    if game.currentState == WAITING_FOR_NARRATOR:
        narrator = game.get_narrator()
        if game.is_ai_player(narrator):
            _handle_ai_narrator(game, redis_client, socketio, gid)
            # After narrator plays, recursively check for more AI turns
            process_ai_turns(redis_client, socketio, gid)
            return

    # Check if any AI non-narrators need to play decoys
    elif game.currentState == WAITING_FOR_PLAYERS:
        for player in game.get_non_narrators():
            if game.is_ai_player(player) and not game.has_set_card(player):
                _handle_ai_decoy(game, player, redis_client, socketio, gid)
                # After playing, recursively check for more AI turns
                process_ai_turns(redis_client, socketio, gid)
                return

    # Check if any AI non-narrators need to vote
    elif game.currentState == WAITING_FOR_VOTES:
        for player in game.get_non_narrators():
            if game.is_ai_player(player) and not game.has_voted(player):
                _handle_ai_vote(game, player, redis_client, socketio, gid)
                # After voting, recursively check for more AI turns
                process_ai_turns(redis_client, socketio, gid)
                return

    # No AI action needed, release lock
    release_lock(redis_client, gid)


def _handle_ai_narrator(game: Game, redis_client, socketio, gid: str):
    """AI selects a card and generates a clue from pre-generated data."""
    narrator = game.get_narrator()
    hand = game.currentRound['allocations'][narrator]

    # Select a random card from hand
    card = random.choice(hand)

    # Get a clue from pre-generated data
    phrase = claude_service.generate_narrator_clue(card)

    # Play the card
    game.set_narrator_card(narrator, card, phrase)
    update_game(redis_client, game)

    socketio.emit('update', json.dumps({
        'data': f"{narrator} chose their narrator card"
    }), room=gid)

    print(f"AI {narrator} played narrator card {card} with phrase: {phrase}")


def _handle_ai_decoy(game: Game, player: str, redis_client, socketio, gid: str):
    """AI selects decoy card based on phrase matching."""
    hand = game.currentRound['allocations'][player]
    phrase = game.currentRound['phrase']

    # Get descriptions for cards in hand
    hand_descriptions = {c: claude_service.get_card_description(c) for c in hand}

    # Select best matching card using keyword matching
    try:
        card = claude_service.select_best_card(phrase, hand_descriptions)
        # Validate the card is in hand
        if card not in hand:
            card = random.choice(hand)
    except Exception as e:
        print(f"Error in AI decoy selection: {e}")
        card = random.choice(hand)

    # Play the card
    game.set_decoy_card(player, card)
    update_game(redis_client, game)

    socketio.emit('update', json.dumps({
        'data': f"{player} chose their decoy card"
    }), room=gid)

    print(f"AI {player} played decoy card {card} for phrase: {phrase}")


def _handle_ai_vote(game: Game, player: str, redis_client, socketio, gid: str):
    """AI votes for card it thinks is narrator's."""
    played_cards = game.currentRound['allCards']
    own_decoy = game.currentRound['decoys'][player]
    phrase = game.currentRound['phrase']

    # Exclude own card from voting options
    votable_cards = [c for c in played_cards if c != own_decoy]

    # Get descriptions for votable cards
    card_descriptions = {c: claude_service.get_card_description(c) for c in votable_cards}

    # Vote using keyword matching
    try:
        voted_card = claude_service.vote_for_card(phrase, card_descriptions)
        # Validate the card is votable
        if voted_card not in votable_cards:
            voted_card = random.choice(votable_cards)
    except Exception as e:
        print(f"Error in AI voting: {e}")
        voted_card = random.choice(votable_cards)

    # Cast the vote
    game.cast_vote(player, voted_card)
    update_game(redis_client, game)

    socketio.emit('update', json.dumps({
        'data': f"{player} cast their vote"
    }), room=gid)

    print(f"AI {player} voted for card {voted_card} (phrase: {phrase})")


# Note: Card descriptions and clues are loaded by claude_service module
