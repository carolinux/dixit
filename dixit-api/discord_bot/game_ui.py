import os
import discord
from discord.ui import View, Button, Select, Modal, InputText

from models import DECKS


CARD_IMAGE_BASE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "dixit-web", "public", "resources", "pictures", "cards"
)

LABELS = "ABCDEFGHIJKLMNOP"

# Embed colors for each card label — visually distinct
_LABEL_COLORS = [
    0xDC3232,  # A - red
    0x3282DC,  # B - blue
    0x32B432,  # C - green
    0xDCA01E,  # D - yellow/orange
    0xA032C8,  # E - purple
    0x1EBEBE,  # F - teal
]


def card_image_path(image_folder: str, card_number: int) -> str:
    return os.path.join(CARD_IMAGE_BASE, image_folder, f"{card_number}.jpg")


def make_card_embeds(image_folder: str, cards: list[int], label_prefix: str = "Card") -> tuple[list[discord.File], list[discord.Embed]]:
    """Create Discord File + Embed pairs so each card has a labeled header above its image."""
    files = []
    embeds = []
    for i, card in enumerate(cards):
        path = card_image_path(image_folder, card)
        if not os.path.exists(path):
            continue
        label = LABELS[i] if i < len(LABELS) else str(i + 1)
        filename = f"{label_prefix}_{label}.jpg"
        files.append(discord.File(path, filename=filename))
        color = _LABEL_COLORS[i % len(_LABEL_COLORS)]
        embed = discord.Embed(title=f"{label_prefix} {label}", color=color)
        embed.set_image(url=f"attachment://{filename}")
        embeds.append(embed)
    return files, embeds


def build_scores_embed(game, title="Scores") -> discord.Embed:
    sorted_scores = sorted(game.scores.items(), key=lambda x: x[1], reverse=True)
    embed = discord.Embed(title=title, color=discord.Color.gold())
    lines = []
    for i, (player, score) in enumerate(sorted_scores):
        prefix = ""
        if i == 0:
            prefix = "1st "
        elif i == 1:
            prefix = "2nd "
        elif i == 2:
            prefix = "3rd "
        else:
            prefix = f"{i+1}th "
        lines.append(f"{prefix}**{player}**: {score} pts")
    embed.description = "\n".join(lines)
    return embed


def build_round_results_embed(game, image_folder: str = None) -> tuple[discord.Embed, discord.File | None]:
    embed = discord.Embed(
        title=f"Round {len(game.sealedRounds) + 1} Results",
        color=discord.Color.blue()
    )
    phrase = game.currentRound.get("phrase", "")
    embed.add_field(name="Phrase", value=f'"{phrase}"', inline=False)

    summary = game.get_all_cards_summary()
    played_cards = game.get_played_cards() or game.currentRound.get("allCards", [])
    card_to_label = {card: LABELS[i] for i, card in enumerate(played_cards) if i < len(LABELS)}

    # Find narrator card info first
    narrator_card = None
    narrator_player = None
    narrator_votes = []
    for card, info in summary.items():
        if info["isNarrator"]:
            narrator_card = card
            narrator_player = info["player"]
            narrator_votes = info["votes"]
            break

    # Narrator reveal with card image
    narrator_label = card_to_label.get(narrator_card, "?")
    narrator_file = None
    if image_folder and narrator_card is not None:
        path = card_image_path(image_folder, narrator_card)
        if os.path.exists(path):
            narrator_file = discord.File(path, filename="narrator_card.jpg")
            embed.set_image(url="attachment://narrator_card.jpg")

    if narrator_votes:
        embed.add_field(
            name="The narrator's card was...",
            value=f"**Card {narrator_label}** by **{narrator_player}** | Votes: {', '.join(narrator_votes)}",
            inline=False,
        )
    else:
        embed.add_field(
            name="The narrator's card was...",
            value=f"**Card {narrator_label}** by **{narrator_player}** | No votes 😰",
            inline=False,
        )

    # Decoy cards
    lines = []
    for card, info in summary.items():
        if info["isNarrator"]:
            continue
        label = card_to_label.get(card, "?")
        player = info["player"]
        votes = info["votes"]
        if votes:
            vote_str = f"Votes: {', '.join(votes)} 🫠"
        else:
            vote_str = "-"
        lines.append(f"Card {label} - played by **{player}** | {vote_str}")

    if lines:
        embed.add_field(name="Decoy Cards", value="\n".join(lines), inline=False)

    round_scores = game.currentRound.get("scores", {})
    if round_scores:
        score_lines = [f"**{p}**: +{s}" for p, s in round_scores.items() if s > 0]
        if score_lines:
            embed.add_field(name="Round Scores", value="\n".join(score_lines), inline=False)

    sorted_total = sorted(game.scores.items(), key=lambda x: x[1], reverse=True)
    total_lines = [f"**{p}**: {s}" for p, s in sorted_total]
    embed.add_field(name="Total Scores", value="\n".join(total_lines), inline=False)

    return embed, narrator_file


def build_winners_embed(game) -> discord.Embed:
    embed = discord.Embed(title="Game Over!", color=discord.Color.gold())
    winners = game.winners.get("winners", [])
    medals = ["1st", "2nd", "3rd"]
    lines = []
    for i, w in enumerate(winners):
        medal = medals[i] if i < len(medals) else f"{i+1}th"
        lines.append(f"{medal}: **{w['player']}** — {w['score']} pts")
    embed.description = "\n".join(lines)

    tricksters = game.winners.get("tricksters")
    if tricksters:
        names = ", ".join(tricksters["tricksters"])
        embed.add_field(
            name="Best Trickster",
            value=f"{names} ({tricksters['score']} decoy votes received)",
            inline=False
        )
    return embed


# --- Modals ---

class PhraseModal(Modal):
    def __init__(self, bot_ref, game_id: str, player_name: str, card: int):
        super().__init__(title="Enter your phrase")
        self.bot_ref = bot_ref
        self.game_id = game_id
        self.player_name = player_name
        self.card = card
        self.phrase_input = InputText(
            label="Phrase",
            placeholder="Enter a phrase or clue for your card...",
            style=discord.InputTextStyle.short,
            max_length=200,
        )
        self.add_item(self.phrase_input)

    async def callback(self, interaction: discord.Interaction):
        phrase = self.phrase_input.value.strip()
        if not phrase:
            await interaction.response.send_message("Phrase cannot be empty!", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        await self.bot_ref.handle_narrator_card(
            self.game_id, self.player_name, self.card, phrase, interaction
        )


# --- Card selection views (shown as ephemeral responses) ---

class NarratorCardSelectView(View):
    def __init__(self, bot_ref, game_id: str, player_name: str, cards: list[int]):
        super().__init__(timeout=600)
        self.bot_ref = bot_ref
        self.game_id = game_id
        self.player_name = player_name

        options = []
        for i, card in enumerate(cards):
            label = LABELS[i] if i < len(LABELS) else str(i + 1)
            options.append(discord.SelectOption(label=f"Card {label}", value=str(card)))
        select = Select(
            placeholder="Pick a card to play as narrator...",
            options=options,
            custom_id=f"narrator_select_{game_id}_{player_name}",
        )
        select.callback = self.on_select
        self.add_item(select)

    async def on_select(self, interaction: discord.Interaction):
        card = int(interaction.data["values"][0])
        modal = PhraseModal(self.bot_ref, self.game_id, self.player_name, card)
        await interaction.response.send_modal(modal)


class DecoyCardSelectView(View):
    def __init__(self, bot_ref, game_id: str, player_name: str, cards: list[int]):
        super().__init__(timeout=600)
        self.bot_ref = bot_ref
        self.game_id = game_id
        self.player_name = player_name

        options = []
        for i, card in enumerate(cards):
            label = LABELS[i] if i < len(LABELS) else str(i + 1)
            options.append(discord.SelectOption(label=f"Card {label}", value=str(card)))
        select = Select(
            placeholder="Pick a decoy card to play...",
            options=options,
            custom_id=f"decoy_select_{game_id}_{player_name}",
        )
        select.callback = self.on_select
        self.add_item(select)

    async def on_select(self, interaction: discord.Interaction):
        card = int(interaction.data["values"][0])
        await interaction.response.defer(ephemeral=True)
        await self.bot_ref.handle_decoy_card(
            self.game_id, self.player_name, card, interaction
        )


# --- Thread-based action buttons ---

class PickCardButton(View):
    """Posted in thread — clicking shows your hand ephemerally."""
    def __init__(self, bot_ref, game_id: str, is_narrator: bool):
        super().__init__(timeout=None)
        self.bot_ref = bot_ref
        self.game_id = game_id
        self.is_narrator = is_narrator

        label = "Pick Your Card (Narrator)" if is_narrator else "Pick Your Decoy Card"
        style = discord.ButtonStyle.primary if is_narrator else discord.ButtonStyle.success
        btn = Button(
            label=label,
            style=style,
            custom_id=f"pick_{'narrator' if is_narrator else 'decoy'}_{game_id}",
        )
        btn.callback = self.on_click
        self.add_item(btn)

    async def on_click(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        discord_user_id = str(interaction.user.id)
        await self.bot_ref.handle_pick_card_click(
            self.game_id, discord_user_id, self.is_narrator, interaction
        )


class VoteView(View):
    """Vote buttons posted in thread. Each player clicks to vote."""
    def __init__(self, bot_ref, game_id: str, played_cards: list[int]):
        super().__init__(timeout=None)
        self.bot_ref = bot_ref
        self.game_id = game_id

        for i, card in enumerate(played_cards):
            label = LABELS[i] if i < len(LABELS) else str(i + 1)
            button = Button(
                label=f"Vote {label}",
                style=discord.ButtonStyle.primary,
                custom_id=f"vote_{game_id}_{card}",
            )
            button.callback = self._make_vote_callback(card)
            self.add_item(button)

    def _make_vote_callback(self, card: int):
        async def callback(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            discord_user_id = str(interaction.user.id)
            player_name = self.bot_ref.get_player_name(self.game_id, discord_user_id)
            if not player_name:
                await interaction.followup.send("You're not in this game!", ephemeral=True)
                return
            await self.bot_ref.handle_vote(self.game_id, player_name, card, interaction)
        return callback


class LolView(View):
    """Lol select posted in thread."""
    def __init__(self, bot_ref, game_id: str, played_cards: list[int]):
        super().__init__(timeout=None)
        self.bot_ref = bot_ref
        self.game_id = game_id

        options = []
        for i, card in enumerate(played_cards):
            label = LABELS[i] if i < len(LABELS) else str(i + 1)
            options.append(discord.SelectOption(label=f"Lol Card {label}", value=str(card)))

        if options:
            select = Select(
                placeholder="(Optional) Pick a card to Lol...",
                options=options,
                custom_id=f"lol_{game_id}",
            )
            select.callback = self.on_lol
            self.add_item(select)

    async def on_lol(self, interaction: discord.Interaction):
        card = int(interaction.data["values"][0])
        await interaction.response.defer(ephemeral=True)
        discord_user_id = str(interaction.user.id)
        player_name = self.bot_ref.get_player_name(self.game_id, discord_user_id)
        if not player_name:
            await interaction.followup.send("You're not in this game!", ephemeral=True)
            return
        await self.bot_ref.handle_lol(self.game_id, player_name, card, interaction)


# --- Lobby views ---

class JoinGameView(View):
    def __init__(self, bot_ref, game_id: str):
        super().__init__(timeout=None)
        self.bot_ref = bot_ref
        self.game_id = game_id

        join_btn = Button(
            label="Join Game",
            style=discord.ButtonStyle.success,
            custom_id=f"join_{game_id}",
        )
        join_btn.callback = self.on_join
        self.add_item(join_btn)

        ai_btn = Button(
            label="Add AI Player",
            emoji="🤖",
            style=discord.ButtonStyle.secondary,
            custom_id=f"addai_{game_id}",
        )
        ai_btn.callback = self.on_add_ai
        self.add_item(ai_btn)

        start_btn = Button(
            label="Start Game",
            style=discord.ButtonStyle.primary,
            custom_id=f"start_{game_id}",
        )
        start_btn.callback = self.on_start
        self.add_item(start_btn)

    async def on_join(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.bot_ref.handle_join(self.game_id, interaction)

    async def on_add_ai(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.bot_ref.handle_add_ai(self.game_id, interaction)

    async def on_start(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.bot_ref.handle_start(self.game_id, interaction)


class NextRoundView(View):
    def __init__(self, bot_ref, game_id: str):
        super().__init__(timeout=None)
        self.bot_ref = bot_ref
        self.game_id = game_id

        btn = Button(
            label="Next Round",
            style=discord.ButtonStyle.primary,
            custom_id=f"next_{game_id}",
        )
        btn.callback = self.on_next
        self.add_item(btn)

    async def on_next(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.bot_ref.handle_next_round(self.game_id, interaction)
