from dataclasses import dataclass, asdict
import random
import json
from uuid import uuid4
from copy import copy

WAITING_TO_START = "waiting_to_start"
WAITING_FOR_NARRATOR = "waiting_for_narrator"
WAITING_FOR_PLAYERS = "waiting_for_players"
WAITING_FOR_VOTES = "waiting_for_votes"
ROUND_REVEALED = "round_revealed"
GAME_ENDED = "game_ended"
MIN_PLAYERS = 2  # for testing..
MAX_PLAYERS = 6
INITIAL_CARD_ALLOCATION = 6
SUBSEQUENT_CARD_ALLOCATION = 1
WIN_SCORE = 36
MAX_CARD = 110


@dataclass
class Game:
    id: str
    currentRound: dict
    sealedRounds: list
    players: list
    winners: list
    scores: dict
    narratorIdx: int
    cards: list
    currentState: str

    @staticmethod
    def from_json(json_str: str) -> 'Game':
        d = json.loads(json_str)
        return Game(**d)

    def to_json(self) -> str:
        d = asdict(self)
        return json.dumps(d)

    def __init__(self, id=None, currentRound=None, sealedRounds=None, players=None, winners=None, scores=None, narratorIdx=None, cards=None, currentState=None):
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
            self.winners = []
        if scores is not None:
            self.scores = scores
        else:
            self.scores = {}
        if narratorIdx is not None:
            self.narratorIdx = narratorIdx
        else:
            self.narratorIdx = None
        if cards is not None:
            self.cards = cards
        else:
            self.cards = self.init_cards()
        if currentState is not None:
            self.currentState = currentState
        else:
            self.currentState = WAITING_TO_START

    def init_cards(self):
        return list(range(1, MAX_CARD + 1)) # <- for the medusa deck change... allow to choose deck?

    def create_playing_order(self):
        random.shuffle(self.cards)
        #random.shuffle(self.players)# first one to join starts

    def is_started(self):
        return self.currentState != WAITING_TO_START

    def allocate_cards(self, card_allocation=SUBSEQUENT_CARD_ALLOCATION):
        self.currentRound['allocations'] = {}
        if len(self.sealedRounds) > 0:
            prevRound = self.sealedRounds[-1]
            self.currentRound['allocations'] = copy(prevRound['allocations'])
        allocations = self.currentRound['allocations']
        for _ in range(card_allocation):
            for player in self.players:
                if len(self.cards) == 0:
                    # we ran out of new cards -- wrap around and reshuffle
                    self.cards = self.init_cards() # FIXME: this allows the player to get a card that is in another player's deck as their card (duplicates!). Although this has never visibly happened! Need to keep a usedcards data structure.
                    random.shuffle(self.cards)
                card = self.cards.pop()
                if player not in allocations:
                    allocations[player] = []
                allocations[player].append(card)

    def serialize_for_list_view(self, joinable_for_player=None):

        return {'id': self.id, 'players': len(self.players), 'state': self.currentState,
                    'playerString': ','.join(self.players), 'join_action': self.get_joinability(joinable_for_player)}

    def get_joinability(self, player):

        if player in self.players:
            return 'rejoin' # and the player state is up to date with game state... i suppose
        elif len(self.players) < MAX_PLAYERS and not self.is_started():
            return 'join'
        else:
            return "game_already_started"

    def contains_player(self, player):
        return player in self.players

    def get_player_info(self):
        return [{"name": p, 'isNarrator': self.is_narrator(p), 'hasVoted': self.has_voted(p),
                 'hasSetCard': self.has_set_card(p), 'score': self.get_score(p),
                 'roundScore': self.get_round_score(p)} for p in self.players]

    def get_score(self, player):
        if not self.is_started():
            return 0
        else:
            return self.scores[player]

    def get_round_score(self, player):
        if not self.is_started():
            return 0
        else:
            return self.currentRound['scores'].get(player, 0)

    def has_set_card(self, player):
        if not self.is_started():
            return False
        if self.is_narrator(player):
            return self.currentRound.get("narratorCard") is not None
        else:
            return self.currentRound.get("decoys", {}).get(player) is not None

    def has_voted(self, player):
        if not self.is_started():
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
        return data

    def get_card_statuses(self, player):
        if self.currentState == WAITING_FOR_PLAYERS:
            return {'myPlayed': self.get_played_card(player), 'myVoted': '', 'summary': {}}
        if self.currentState == WAITING_FOR_VOTES:
            return {'myPlayed': self.get_played_card(player), 'myVoted': self.get_voted_card(player), 'summary': {}}
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
            result[card] = {'player': player, 'isNarrator': narrator, 'votes': votes}
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

    def get_played_card(self, player):
        if not self.is_narrator(player):
            return self.currentRound.get('decoys', {}).get(player, '')
        else:
            return self.currentRound.get('narratorCard', '')

    def get_voted_card(self, player):
        if not self.is_narrator(player):
            return self.currentRound.get('votes', {}).get(player, '')
        return ''

    def get_narrator(self):
        if self.narratorIdx is not None:
            return self.players[self.narratorIdx]

    def get_round_info(self, player):
        if not self.is_started():
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
        if self.currentState in (WAITING_FOR_VOTES, ROUND_REVEALED):
            return self.currentRound['allCards']
        return []

    def num(self):
        return len(self.players)

    def get_non_narrators(self):
        return [p for p in self.players if not self.is_narrator(p)]

    def get_narrator_card(self):
        return self.currentRound.get('narratorCard')

    def join(self, player_name):
        if player_name in self.players:
            raise Exception("Player with name {} already in game {}.".format(player_name, self.id))
        if not player_name:
            raise Exception("Player name cannot be empty")

        if len(self.players) >= MAX_PLAYERS:
            raise Exception("Game {} is full".format(self.id))
        self.players.append(player_name)

    def start(self):
        if self.is_started():
            raise Exception("Could not start game already in progress")
        elif len(self.players) < MIN_PLAYERS or len(self.players) > MAX_PLAYERS:
            raise Exception("Need to have between {} and {} players".format(MIN_PLAYERS, MAX_PLAYERS))
        else:
            #self.sealedStates.append(self.currentState)
            self.create_playing_order()
            self.advance_narrator()
            self.scores = {p:0 for p in self.players}

            self.currentRound = {}
            self.currentRound['decoys'] = {}
            self.currentRound['votes'] = {}
            self.currentRound['scores'] = {}
            self.allocate_cards(INITIAL_CARD_ALLOCATION)
            self.currentState = WAITING_FOR_NARRATOR

    def set_narrator_card(self, player, card, phrase):
        if not self.is_narrator(player):
            raise Exception("Trying to set card without being narrator {}, {}".format(player, self.get_narrator()))
        if self.currentState != WAITING_FOR_NARRATOR:
            raise Exception("Trying to set card at an invalid point in the game")
        self.currentRound['phrase'] = phrase
        self.currentRound['narratorCard'] = card
        self.currentRound['allocations'][player].remove(card)
        self.currentState = WAITING_FOR_PLAYERS

    def set_decoy_card(self, player, card):
        if self.is_narrator(player):
            raise Exception("Trying to set decoy card while being narrator")
        if self.currentState != WAITING_FOR_PLAYERS:
            raise Exception("Trying to set card at an invalid point in the game")

        self.currentRound['decoys'][player] = card
        self.currentRound['allocations'][player].remove(card) # FIXME: here will crash if somebody maliciously sends a random card
        if len(self.currentRound['decoys']) == len(self.players) -1:
            self.currentRound['allCards'] = [self.currentRound['narratorCard']] + list(self.currentRound['decoys'].values())
            random.shuffle(self.currentRound['allCards']);
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

        for card, votes in votes_to_card.items():
            if card == self.get_narrator_card():
                continue
            trickster = card_to_player[card]
            if trickster not in scores:
                scores[trickster] = 0
            scores[trickster] += votes

        for p in self.players:
            self.scores[p] += scores.get(p, 0)
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

    def advance_narrator(self):
        if len(self.sealedRounds) == 0:
            self.narratorIdx = 0
            return
        self.narratorIdx+=1
        if self.narratorIdx == self.num():
            self.narratorIdx = 0

    def start_next_round(self):
        if self.currentState != ROUND_REVEALED:
            raise Exception("Illegal state {}. Cannot transition to next round.".format(self.currentState))
        self.sealedRounds.append(self.currentRound)

        did_end = self.end()
        if did_end:
            return

        self.advance_narrator()

        self.currentRound = {}
        self.currentRound['decoys'] = {}
        self.currentRound['votes'] = {}
        self.currentRound['scores'] = {}
        self.allocate_cards(SUBSEQUENT_CARD_ALLOCATION)
        self.currentState = WAITING_FOR_NARRATOR

    def end(self):
        if self.currentState != ROUND_REVEALED:
            raise Exception("Cannot end")
        end = False
        for player, score in self.scores.items():
            if score >= WIN_SCORE:
                end = True
        if not end:
            return False

        medals = ['gold', 'silver', 'bronze']

        sorted_scores = sorted(self.scores.items(), key=lambda x: x[1])

        for _ in medals:
            if sorted_scores:
                player, score = sorted_scores.pop()
                self.winners.append({'player': player, 'score': score})
        self.currentState = GAME_ENDED
        return True

    def to_json_lite(self):
        """Basic record of the game."""
        print(self.sealedRounds)
        return {self.id: {'rounds': self.sealedRounds, 'players': self.players, 'scores': self.scores}}

    def has_ended(self):
        return self.currentState == GAME_ENDED
