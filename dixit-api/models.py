from dataclasses import dataclass, asdict
import random
import json
from typing import List
from uuid import uuid4
from copy import copy
import dacite

WAITING_TO_START = "waiting_to_start"
WAITING_FOR_NARRATOR = "waiting_for_narrator"
WAITING_FOR_PLAYERS = "waiting_for_players"
WAITING_FOR_VOTES = "waiting_for_votes"
ROUND_REVEALED = "round_revealed"
GAME_ENDED = "game_ended"
GAME_ABANDONED = "game_abandoned"
MIN_PLAYERS = 2  # for testing - in reality two players breaks the winner podium if it goes to the game end state
MAX_PLAYERS = 12
INITIAL_CARD_ALLOCATION = 6
WIN_SCORE = 36
MAX_CARD = 175
INITIAL_LOLPOINTS = 3


@dataclass
class Deck:
    name: str
    max_card: int
    image_folder: str
    excluded_cards: set

    def get_cards(self) -> List[int]:
        all_cards = list(range(1, self.max_card + 1))
        return [c for c in all_cards if c not in self.excluded_cards]


# Deck definitions
DECKS = {
    "full": Deck("full", MAX_CARD, "medusa", set()),
    "kids": Deck("kids", MAX_CARD, "medusa", {3, 15, 30, 41, 66, 89, 100, 125, 134}),
    "classic": Deck("classic", 70, "original", set()),
}


@dataclass
class LolPoints:
    playerToRem: dict

    def add_player(self, player):
        self.playerToRem[player] = INITIAL_LOLPOINTS

    def remove_player(self, player):
        del self.playerToRem[player]

    def cast_vote(self, voter, votee) -> bool:
        if self.playerToRem[voter] <= 0:
            print("Player doesn't have any lolpoints left to give")
            return False
        if voter == votee:
            print("Cannot vote for self")
            return False

        self.playerToRem[voter]-=1
        return True


LOBBY_PENDING = "pending"
LOBBY_APPROVED = "approved"
LOBBY_DENIED = "denied"


@dataclass
class Game:
    id: str
    currentRound: dict
    sealedRounds: list
    players: list
    winners: dict
    scores: dict
    narratorIdx: int
    cards: list
    discards: list
    currentState: str
    creator: str
    stats: dict
    lolPoints: LolPoints
    ai_players: list
    lobby: list  # list of {name: str, status: 'pending'|'approved'|'denied'}
    deck_name: str
    unranked_players: list  # players who don't receive scores

    @staticmethod
    def from_json(json_str: str) -> 'Game':
        d = json.loads(json_str)
        return Game(**d)

    def to_json(self) -> str:
        d = asdict(self)
        return json.dumps(d)

    def __init__(self, id=None, currentRound=None, sealedRounds=None, players=None, winners=None, scores=None, narratorIdx=None, cards=None, discards=None, currentState=None, creator=None, stats=None, lolPoints=None, ai_players=None, lobby=None, deck_name=None, unranked_players=None):
        if id is not None:
            self.id = id
        else:
            self.id = uuid4()
        if currentRound is not None:
            self.currentRound = currentRound
        else:
            self.currentRound = {}
        if sealedRounds is not None:
            self.sealedRounds = sealedRounds
        else:
            self.sealedRounds = []
        if players is not None:
            self.players = players
        else:
            self.players = []
        if winners is not None:
            self.winners = winners
        else:
            self.winners = {}
        if scores is not None:
            self.scores = scores
        else:
            self.scores = {}
        if narratorIdx is not None:
            self.narratorIdx = narratorIdx
        else:
            self.narratorIdx = None
        if deck_name is not None:
            self.deck_name = deck_name
        else:
            self.deck_name = "full"
        if cards is not None:
            self.cards = cards
        else:
            self.cards = self.init_cards()
        if discards is not None:
            self.discards = discards
        else:
            self.discards = []
        if currentState is not None:
            self.currentState = currentState
        else:
            self.currentState = WAITING_TO_START
        if creator is not None:
            self.creator = creator
        else:
            self.creator = None
        if stats is not None:
            self.stats = stats
        else:
            self.stats = {}
        if lolPoints is not None:
            self.lolPoints = dacite.from_dict(LolPoints, lolPoints)
        else:
            self.lolPoints = LolPoints({})
            for player in self.players:
                self.lolPoints.add_player(player)
        if ai_players is not None:
            self.ai_players = ai_players
        else:
            self.ai_players = []
        if lobby is not None:
            self.lobby = lobby
        else:
            self.lobby = []
        if unranked_players is not None:
            self.unranked_players = unranked_players
        else:
            self.unranked_players = []

    def start_rematch(self) -> None:
        """Reset game to allow rematch."""
        self.__init__(id=self.id, players=self.players, creator=self.creator, ai_players=self.ai_players, deck_name=self.deck_name, unranked_players=self.unranked_players)

    def init_cards(self):
        deck = DECKS.get(self.deck_name, DECKS["full"])
        return deck.get_cards()

    def create_playing_order(self):
        random.shuffle(self.cards)
        random.shuffle(self.players)

    def is_started(self):
        return self.currentState != WAITING_TO_START

    def allocate_cards(self, single_player=None):
        if single_player is None:
            self.currentRound['allocations'] = {}
            if len(self.sealedRounds) > 0:
                prevRound = self.sealedRounds[-1]
                self.currentRound['allocations'] = copy(prevRound['allocations'])
        allocations = self.currentRound['allocations']
        for player in self.players:
            if player not in allocations:
                allocations[player] = []
            if single_player is not None and player != single_player:
                continue

            while len(allocations[player]) < INITIAL_CARD_ALLOCATION:
                if len(self.cards) == 0:
                    self.cards = self.discards
                    self.discards = []
                    random.shuffle(self.cards)
                card = self.cards.pop()
                allocations[player].append(card)

    def serialize_for_list_view(self, joinable_for_player=None):

        return {'id': self.id, 'players': len(self.players), 'state': self.currentState,
                    'playerString': ','.join(self.players), 'join_action': self.get_joinability(joinable_for_player)}

    def get_joinability(self, player):

        if player in self.players:
            return 'rejoin' # and the player state is up to date with game state... i suppose
        elif len(self.players) < MAX_PLAYERS and not self.is_started() and not self.is_abandoned():
            return 'join'
        else:
            return "game_already_started"

    def contains_player(self, player):
        return player in self.players

    def get_player_info(self):
        return [{"name": p, 'isNarrator': self.is_narrator(p), 'hasVoted': self.has_voted(p),
                 'hasSetCard': self.has_set_card(p), 'score': self.get_score(p),
                 'roundScore': self.get_round_score(p), 'isAI': self.is_ai_player(p),
                 'isUnranked': self.is_unranked(p)} for p in self.players]

    def get_score(self, player):
        if not self.is_started() or self.is_abandoned():
            return 0
        else:
            return self.scores[player]

    def get_round_score(self, player):
        if not self.is_started() or self.is_abandoned():
            return 0
        else:
            return self.currentRound['scores'].get(player, 0)

    def has_set_card(self, player):
        if not self.is_started() or self.is_abandoned():
            return False
        if self.is_narrator(player):
            return self.currentRound.get("narratorCard") is not None
        else:
            return self.currentRound.get("decoys", {}).get(player) is not None

    def has_voted(self, player):
        if not self.is_started() or self.is_abandoned():
            return False
        if self.is_narrator(player):
            return False
        else:
            return self.currentRound.get("votes", {}).get(player) is not None

    def serialize_for_status_view(self, player):
        data = self.serialize_for_list_view()
        data['player'] = player
        data['cardStatuses'] = self.get_card_statuses(player)
        data['winners'] = self.winners
        data['playerList'] = self.get_player_info()
        data['roundInfo'] = self.get_round_info(player)
        data['isNarrator'] = self.is_narrator(player)
        data['isCreator'] = self.is_creator(player)
        data['lolPoints'] = self.lolPoints.playerToRem.get(player, 0)
        # Include lobby info for creator
        if self.is_creator(player):
            data['lobby'] = self.get_pending_lobby()
        else:
            data['lobby'] = []
        # Include deck info for card images
        deck = DECKS.get(self.deck_name, DECKS["full"])
        data['imageFolder'] = deck.image_folder
        return data

    def is_creator(self, player):
        return player == self.creator

    def is_ai_player(self, player: str) -> bool:
        return player in self.ai_players

    def is_unranked(self, player: str) -> bool:
        return player in self.unranked_players

    def add_unranked_player(self, player: str) -> None:
        """Mark a player as unranked (they won't receive scores)."""
        if player not in self.unranked_players:
            self.unranked_players.append(player)

    def add_ai_player(self, name: str = None) -> str:
        """Add an AI player to the game. Returns the AI player's name."""
        from cute_ids import generate_cute_id

        if self.is_started():
            raise Exception("Cannot add AI player to a game that has already started.")
        if len(self.players) >= MAX_PLAYERS:
            raise Exception("Game is full. Cannot add more players.")

        # Generate unique AI name using cute_ids if not provided
        if name is None:
            for _ in range(10):
                name = generate_cute_id()
                if name not in self.players:
                    break
            else:
                name = f"ai-{len(self.ai_players) + 1}"

        if name in self.players:
            raise Exception(f"Player with name {name} already in game.")

        self.players.append(name)
        self.ai_players.append(name)
        return name

    def get_card_statuses(self, player):
        if self.currentState == WAITING_FOR_PLAYERS:
            return {'myPlayed': self.get_played_card(player), 'myVoted': '', 'summary': {}}
        if self.currentState == WAITING_FOR_VOTES:
            return {'myPlayed': self.get_played_card(player), 'myVoted': self.get_voted_card(player), 'myLolled': self.get_lolled_card(player), 'summary': {}}
        elif self.currentState == ROUND_REVEALED:
            return {'myPlayed': self.get_played_card(player), 'myVoted': self.get_voted_card(player), 'summary': self.get_all_cards_summary()}
        return {}

    def get_all_cards_summary(self):
        """for end of round"""
        result = {}
        for card in self.get_played_cards():
            if card == self.get_narrator_card():
                player = self.get_narrator()
                narrator = True
            else:
                player = self.get_player_that_played_card(card)
                narrator = False
            votes = self.get_players_that_voted_for_card(card)
            lols = self.get_players_that_lolled_for_card(card)
            result[card] = {'player': player, 'isNarrator': narrator, 'votes': votes, 'lols': lols}
        return result

    def get_player_that_played_card(self, card):
        for player, played_card in self.currentRound['decoys'].items():
            if card == played_card:
                return player

    def get_players_that_voted_for_card(self, card):
        res = []
        for player, voted_card in self.currentRound['votes'].items():
            if voted_card == card:
                res.append(player)
        return res

    def get_players_that_lolled_for_card(self, card):
        res = []
        for player, voted_card in self.currentRound['lols'].items():
            if voted_card == card:
                res.append(player)
        return res

    def get_played_card(self, player):
        if not self.is_narrator(player):
            return self.currentRound.get('decoys', {}).get(player, '')
        else:
            return self.currentRound.get('narratorCard', '')

    def get_voted_card(self, player):
        if not self.is_narrator(player):
            return self.currentRound.get('votes', {}).get(player, '')
        return ''

    def get_lolled_card(self, player):
        return self.currentRound.get('lols', {}).get(player, '')

    def get_narrator(self):
        if self.narratorIdx is not None:
            return self.players[self.narratorIdx]

    def get_round_info(self, player):
        if not self.is_started() or self.is_abandoned():
            return {'idx': None, 'narrator': None, 'hand': [], 'playedCards': []}
        idx = len(self.sealedRounds) + 1
        phrase = self.currentRound.get('phrase', '')
        hand = self.get_hand(player)
        played_cards = self.get_played_cards()
        return {'idx': idx, 'narrator': self.get_narrator(), 'phrase': phrase, 'hand': hand, 'playedCards': played_cards}

    def get_hand(self, player):
        allocations = self.currentRound.get('allocations', {}).get(player, [])
        if self.currentState == WAITING_FOR_VOTES:
            return ['back'] * len(allocations) # hide the hand while voting to reduce confusion
        else:
            return allocations

    def is_narrator(self, player):
        return self.get_narrator() == player

    def get_played_cards(self):
        if self.currentState == WAITING_FOR_PLAYERS:
            # do not reveal the cards to the frontend
            return (1 + len(self.currentRound['decoys'])) * ['back']
        if self.currentState in (WAITING_FOR_VOTES, ROUND_REVEALED, GAME_ENDED):
            return self.currentRound['allCards']
        return []

    def num(self):
        return len(self.players)

    def get_non_narrators(self):
        return [p for p in self.players if not self.is_narrator(p)]

    def get_narrator_card(self):
        return self.currentRound.get('narratorCard')

    def abandon(self, player_name):
        if self.is_creator(player_name):
            self.currentState = GAME_ABANDONED
        else:
            raise Exception("Cannot abandon game if not the creator!")

    def is_abandoned(self):
        return self.currentState == GAME_ABANDONED

    def join(self, player_name):
        if self.is_abandoned():
            raise Exception("Cannot join game that is abandoned.")

        # Check if player is already in the game
        if player_name in self.players:
            raise Exception("Player with name {} already in game {}.".format(player_name, self.id))

        if self.is_started():
            print(f"{player_name} is trying to join game {self.id} that is in state {self.currentState}")
            if self.currentState not in (WAITING_FOR_NARRATOR, ROUND_REVEALED):
                raise Exception("Cannot join game that is already started, unless at the beginning of a round.")
            self.players.append(player_name)
            self.lolPoints.add_player(player_name)
            self.scores[player_name] = 0
            self.stats['tricksters'][player_name] = 0
            self.allocate_cards(player_name)
            return
        if not player_name:
            raise Exception("Player name cannot be empty")

        if len(self.players) >= MAX_PLAYERS:
            raise Exception("Game {} is full".format(self.id))
        self.players.append(player_name)

    def request_join(self, player_name: str) -> None:
        """Request to join an in-progress game. Player goes into lobby."""
        if self.is_abandoned():
            raise Exception("Cannot request to join abandoned game.")
        if self.has_ended():
            raise Exception("Cannot request to join ended game.")
        if not player_name:
            raise Exception("Player name cannot be empty")
        if player_name in self.players:
            raise Exception("Player {} is already in the game.".format(player_name))
        # Check if already in lobby
        for entry in self.lobby:
            if entry['name'] == player_name:
                if entry['status'] == LOBBY_DENIED:
                    raise Exception("Your request to join was denied.")
                # Already in lobby, just return
                return
        if len(self.players) + len([e for e in self.lobby if e['status'] == LOBBY_APPROVED]) >= MAX_PLAYERS:
            raise Exception("Game is full.")
        self.lobby.append({'name': player_name, 'status': LOBBY_PENDING})

    def approve_join(self, approver: str, player_name: str) -> None:
        """Approve a player's request to join. Only creator can do this."""
        if not self.is_creator(approver):
            raise Exception("Only the game creator can approve join requests.")
        for entry in self.lobby:
            if entry['name'] == player_name:
                if entry['status'] == LOBBY_PENDING:
                    entry['status'] = LOBBY_APPROVED
                    return
                else:
                    raise Exception("Player {} is not pending approval.".format(player_name))
        raise Exception("Player {} is not in the lobby.".format(player_name))

    def deny_join(self, denier: str, player_name: str) -> None:
        """Deny a player's request to join. Only creator can do this."""
        if not self.is_creator(denier):
            raise Exception("Only the game creator can deny join requests.")
        for entry in self.lobby:
            if entry['name'] == player_name:
                entry['status'] = LOBBY_DENIED
                return
        raise Exception("Player {} is not in the lobby.".format(player_name))

    def get_lobby_status(self, player_name: str) -> dict:
        """Get lobby status for a specific player."""
        # Check if player is already in game
        if player_name in self.players:
            return {'status': 'joined', 'gameState': self.currentState}
        # Check lobby
        for entry in self.lobby:
            if entry['name'] == player_name:
                return {'status': entry['status'], 'gameState': self.currentState}
        return {'status': 'not_found', 'gameState': self.currentState}

    def get_pending_lobby(self) -> list:
        """Get list of players waiting for approval."""
        return [entry for entry in self.lobby if entry['status'] == LOBBY_PENDING]

    def get_approved_lobby(self) -> list:
        """Get list of approved players waiting to join."""
        return [entry for entry in self.lobby if entry['status'] == LOBBY_APPROVED]

    def process_lobby(self) -> list:
        """Add approved lobby players to the game. Called at start of next round.
        Returns list of players that were added."""
        added_players = []
        for entry in self.lobby[:]:  # iterate over copy
            if entry['status'] == LOBBY_APPROVED:
                player_name = entry['name']
                if len(self.players) < MAX_PLAYERS:
                    self.players.append(player_name)
                    self.lolPoints.add_player(player_name)
                    self.scores[player_name] = 0
                    self.stats['tricksters'][player_name] = 0
                    added_players.append(player_name)
                    # Mark as joined instead of removing, so we can verify later
                    entry['status'] = 'joined'
        return added_players

    def was_added_from_lobby(self, player_name: str) -> bool:
        """Check if a player was added to the game via the lobby system."""
        for entry in self.lobby:
            if entry['name'] == player_name and entry['status'] == 'joined':
                return True
        return False

    def clear_lobby_entry(self, player_name: str) -> None:
        """Remove a player's lobby entry after they've gotten their cookie."""
        self.lobby = [e for e in self.lobby if e['name'] != player_name]

    def remove_player(self, remover: str, player: str) -> None:

        if not self.is_creator(remover):
            raise Exception("Only creator can remove players from game.")

        if self.is_creator(player):
            raise Exception("Cannot remove creator from game. Abandon game instead.")

        if self.is_abandoned():
            raise Exception("Cannot remove player from abandoned game.")

        if self.currentState == GAME_ENDED:
            raise Exception("Cannot remove player from ended game.")

        if player not in self.players:
            raise Exception("Player {} not in game {}.".format(player, self.id))

        if not self.is_started():
            self.players.remove(player)
            if player in self.ai_players:
                self.ai_players.remove(player)
            return

        if len(self.players) == MIN_PLAYERS:
            raise Exception("Cannot remove player from game with only {} players.".format(MIN_PLAYERS))

        idx = self.players.index(player)
        narrator_idx = self.narratorIdx
        self.players.remove(player)
        if player in self.scores:
            del self.scores[player]
        if player in self.stats['tricksters']:
            del self.stats['tricksters'][player]

        self.lolPoints.remove_player(player)

        print(f"idx: {idx}, narrator_idx: {narrator_idx}, num: {self.num()}")

        if self.currentState == ROUND_REVEALED:
            # start next
            if narrator_idx < idx:
                self.advance_narrator()
            if narrator_idx == idx and idx == self.num():
                self.advance_narrator()
            print(f"idx: {idx}, new narrator_idx: {self.narratorIdx}, num: {self.num()}")
            self.start_next_round(do_state_check=True, do_end_check=True, advance_narrator=False)
        else:
            # restart current
            if narrator_idx > idx:
                self.narratorIdx -= 1
            if narrator_idx == idx and idx == self.num():
                self.advance_narrator()
            print(f"idx: {idx}, new narrator_idx: {self.narratorIdx}, num: {self.num()}")
            self.start_next_round(do_state_check=False, do_end_check=False, advance_narrator=False)

    def start(self):
        if self.is_started():
            raise Exception("Could not start game already in progress")
        elif len(self.players) < MIN_PLAYERS or len(self.players) > MAX_PLAYERS:
            raise Exception("Need to have between {} and {} players".format(MIN_PLAYERS, MAX_PLAYERS))
        else:
            self.create_playing_order()
            self.advance_narrator(first=True)
            self.scores = {p: 0 for p in self.players}
            self.stats['tricksters'] = {p: 0 for p in self.players}
            for p in self.players:
                self.lolPoints.add_player(p)
            self.currentRound = {}
            self.currentRound['decoys'] = {}
            self.currentRound['votes'] = {}
            self.currentRound['scores'] = {}
            self.currentRound['narratorCard'] = None
            self.currentRound['phrase'] = None
            self.currentRound['allCards'] = []
            self.currentRound['lols'] = {}
            self.allocate_cards()
            self.currentState = WAITING_FOR_NARRATOR

    def set_narrator_card(self, player, card, phrase):
        if not self.is_narrator(player):
            raise Exception("Trying to set card without being narrator player: {}, narrator: {}".format(player, self.get_narrator()))
        if self.currentState != WAITING_FOR_NARRATOR:
            raise Exception("Trying to set card at an invalid point in the game")
        if card not in self.currentRound['allocations'].get(player, []):
            raise Exception("Trying to play a card that the narrator doesn't actually own.")
        self.currentRound['phrase'] = phrase
        self.currentRound['narratorCard'] = card
        self.currentRound['allocations'][player].remove(card)
        self.currentRound['allCards'] = [self.currentRound['narratorCard']]
        self.currentState = WAITING_FOR_PLAYERS

    def set_decoy_card(self, player, card):
        if self.is_narrator(player):
            raise Exception("Trying to set decoy card while being narrator")
        if self.currentState != WAITING_FOR_PLAYERS:
            raise Exception("Trying to set card at an invalid point in the game")
        if card not in self.currentRound['allocations'].get(player, []):
            raise Exception("Trying to play a card that the player doesn't actually own.")

        self.currentRound['decoys'][player] = card
        self.currentRound['allocations'][player].remove(card)
        self.currentRound['allCards'] = [self.currentRound['narratorCard']] + list(self.currentRound['decoys'].values())
        if len(self.currentRound['decoys']) == len(self.players) - 1:
            random.shuffle(self.currentRound['allCards'])
            self.currentState = WAITING_FOR_VOTES

    def set_scores(self):
        scores = {}
        votes = self.currentRound['votes']
        votes_to_card = {}
        card_to_player = {}
        for player, card in votes.items():
            if card not in votes_to_card:
                votes_to_card[card] = 0
            votes_to_card[card] += 1

        # for the extra pointz
        for player, card in self.currentRound['decoys'].items():
            card_to_player[card] = player
        # include narrator's card
        card_to_player[self.get_narrator_card()] = self.get_narrator()

        correct_votes = votes_to_card.get(self.get_narrator_card(), 0)
        if 0 < correct_votes < self.num() - 1:
            scores[self.get_narrator()] = 3
            for p in self.get_non_narrators():
                if votes[p] == self.get_narrator_card():
                    scores[p] = 3
        else:
            scores[self.get_narrator()] = 0
            for p in self.get_non_narrators():
                scores[p] = 2

        for card, num_votes in votes_to_card.items():
            if card == self.get_narrator_card():
                continue
            trickster = card_to_player[card]
            if trickster not in scores:
                scores[trickster] = 0
            scores[trickster] += num_votes
            self.stats['tricksters'][trickster] += num_votes

        for p in self.players:
            if not self.is_unranked(p):
                self.scores[p] += scores.get(p, 0)

        for voter, card in self.currentRound['lols'].items():
            votee = card_to_player[card]
            if self.lolPoints.cast_vote(voter, votee):
                if not self.is_unranked(votee):
                    self.scores[votee]+=1
                if votee not in scores:
                    scores[votee] = 0
                scores[votee]+=1
        self.currentRound['scores'] = scores

    def cast_vote(self, player, card):
        if self.is_narrator(player):
            raise Exception("Trying to vote card while being narrator")
        if self.currentState != WAITING_FOR_VOTES:
            raise Exception("Trying to set card at an invalid point in the game")
        if card == self.currentRound['decoys'][player]:
            raise Exception("Trying to vote for own card, which is not allowed")
        self.currentRound['votes'][player] = card

        if len(self.currentRound['votes']) == len(self.players) - 1:
            self.set_scores()
            self.currentState = ROUND_REVEALED


    def cast_lol(self, player, card):
        if self.currentState != WAITING_FOR_VOTES:
            raise Exception("Trying to lol at an invalid point in the game")
        if (not self.is_narrator(player) and card == self.currentRound['decoys'][player]) or (self.is_narrator(player) and self.currentRound.get("narratorCard") == card):
            raise Exception("Trying to lol for own card, which is not allowed")
        self.currentRound['lols'][player] = card

    def advance_narrator(self, first=False):
        if first:
            self.narratorIdx = 0
            return

        self.narratorIdx += 1
        if self.narratorIdx >= self.num():
            self.narratorIdx = 0

    def start_next_round(self, do_state_check=True, do_end_check=True, advance_narrator=True):
        if do_state_check and self.currentState != ROUND_REVEALED:
            raise Exception("Illegal state {}. Cannot transition to next round.".format(self.currentState))

        self.sealedRounds.append(self.currentRound)

        if do_end_check:
            did_end = self.end()
            if did_end:
                return

        # Process approved lobby players before starting next round
        added_from_lobby = self.process_lobby()

        if advance_narrator:
            self.advance_narrator()

        self.currentRound = {}
        self.currentRound['allCards'] = []
        self.currentRound['decoys'] = {}
        self.currentRound['votes'] = {}
        self.currentRound['lols'] = {}
        self.currentRound['scores'] = {}

        self.update_discard_pile(self.sealedRounds[-1])
        self.allocate_cards()
        self.currentState = WAITING_FOR_NARRATOR

        return added_from_lobby
    def update_discard_pile(self, round):
        self.discards.extend(round['allCards'])

    def end(self):
        if self.currentState != ROUND_REVEALED:
            raise Exception("Cannot end")
        end = False
        high_score = 0
        for player, score in self.scores.items():
            if score >= WIN_SCORE:
                high_score = max(score, high_score)
                end = True

        if not end:
            return False

        tie_count = 0
        for player, score in self.scores.items():
            if score == high_score:
                tie_count +=1

        if tie_count > 1:
            end = False  # won't end the game when two people have the same highest score, will play more rounds until we have one clear winner

        if not end:
            return False

        medals = ['gold', 'silver', 'bronze']

        sorted_scores = sorted(self.scores.items(), key=lambda x: x[1])

        self.winners['winners'] = []
        for _ in medals:
            if sorted_scores:
                player, score = sorted_scores.pop()
                self.winners['winners'].append({'player': player, 'score': score})
        self.winners['tricksters'] = self.get_tricksters()
        # self.winners['tricksters'] = {"tricksters": ["player1", "player3"], "score": 42}
        # self.winners['winners'] = [{'player':'first', 'score':42},{'player':'2dna1', 'score':40}, {'player':'send2', 'score':40}]
        self.currentState = GAME_ENDED
        return True

    def to_json_lite(self):
        """Basic record of the game."""
        return {self.id: {'rounds': self.sealedRounds, 'players': self.players, 'scores': self.scores}}

    def has_ended(self):
        return self.currentState == GAME_ENDED

    def get_tricksters(self) -> dict:
        """
        Return None if nobody tricked anyone, otherwise
        a dictionary
        {"tricksters": ["player1", "player3"], "score": 42}
        if player1 and player3 tied for the highest trickster score
        """
        max_score = 0
        for player, score in self.stats['tricksters'].items():
            max_score = max(max_score, score)
        if max_score == 0:
            return None
        res = {'tricksters': [], 'score': max_score}
        for player, score in self.stats['tricksters'].items():
            if score == max_score:
                res['tricksters'].append(player)
        return res


