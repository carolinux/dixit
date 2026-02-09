import asyncio
import random
from dataclasses import dataclass, field

import discord
from discord.ext import commands
import redis

from models import (
    Game, DECKS, WAITING_FOR_PLAYERS, WAITING_FOR_VOTES,
    ROUND_REVEALED,
)
from datastore import (
    get_game_by_id, get_locked_game_by_id, add_game,
    update_game, release_lock, LockingException,
)
from cute_ids import generate_cute_id
from ai_handler import do_one_ai_action
from discord_bot.config import DISCORD_TOKEN, ENABLE_LOL, MAX_DISCORD_PLAYERS
from discord_bot.game_ui import (
    JoinGameView, NarratorCardSelectView, DecoyCardSelectView,
    PickCardButton, VoteView, LolView, NextRoundView,
    build_round_results_embed, build_winners_embed, build_scores_embed,
    make_card_embeds, LABELS,
)


@dataclass
class DiscordGameState:
    game_id: str
    thread_id: int
    creator_discord_id: str
    # discord_user_id -> in-game player name
    player_map: dict[str, str] = field(default_factory=dict)
    image_folder: str = "medusa-compressed"


async def _silent_send(channel, content=None, **kwargs):
    """Send a message without triggering notification sounds."""
    return await channel.send(content, silent=True, **kwargs)


class DixitBot:
    def __init__(self):
        intents = discord.Intents.default()
        self.bot = commands.Bot(intents=intents)
        self.red = redis.StrictRedis(
            "localhost", 6379, charset="utf-8", decode_responses=True
        )
        # game_id -> DiscordGameState
        self.games: dict[str, DiscordGameState] = {}
        # thread_id -> game_id (reverse lookup)
        self.thread_to_game: dict[int, str] = {}

        self._register_commands()
        self._register_events()

    def _register_events(self):
        @self.bot.event
        async def on_ready():
            print(f"Dixit bot logged in as {self.bot.user}")

    def _register_commands(self):
        dixit_group = self.bot.create_group("dixit", "Dixit game commands")

        @dixit_group.command(name="create", description="Create a new Dixit game")
        async def cmd_create(
            ctx: discord.ApplicationContext,
            deck: discord.Option(
                str,
                "Choose a deck",
                choices=["full", "classic", "kids"],
                default="full",
            ),
        ):
            await ctx.defer()
            if isinstance(ctx.channel, discord.Thread):
                await ctx.respond("Can't create a game inside a thread! Use a regular channel.")
                return
            discord_user_id = str(ctx.author.id)
            player_name = ctx.author.display_name

            game_id = generate_cute_id()
            for _ in range(10):
                if get_game_by_id(self.red, game_id) is None:
                    break
                game_id = generate_cute_id()

            game = Game(id=game_id, creator=player_name, deck_name=deck)
            game.join(player_name)
            if not add_game(self.red, game):
                await ctx.respond("Failed to create game — ID collision. Try again.")
                return

            deck_obj = DECKS.get(deck, DECKS["full"])

            thread = await ctx.channel.create_thread(
                name=f"Dixit: {game_id}",
                type=discord.ChannelType.public_thread,
            )

            state = DiscordGameState(
                game_id=game_id,
                thread_id=thread.id,
                creator_discord_id=discord_user_id,
                player_map={discord_user_id: player_name},
                image_folder=deck_obj.image_folder,
            )
            self.games[game_id] = state
            self.thread_to_game[thread.id] = game_id

            view = JoinGameView(self, game_id)
            await _silent_send(thread,
                f"**Dixit Game: {game_id}**\n"
                f"Deck: {deck}\n"
                f"Created by: **{player_name}**\n\n"
                f"Players: {player_name}\n\n"
                f"Click **Join Game** to join, then **Start Game** when ready!",
                view=view,
            )
            await ctx.respond(f"Game **{game_id}** created! Head to the thread: {thread.mention}")

        @dixit_group.command(name="status", description="Show current game status")
        async def cmd_status(ctx: discord.ApplicationContext):
            await ctx.defer(ephemeral=True)
            game_id = self._game_id_from_thread(ctx.channel_id)
            if not game_id:
                await ctx.respond("This isn't a game thread!", ephemeral=True)
                return

            game = get_game_by_id(self.red, game_id)
            if not game:
                await ctx.respond("Game not found!", ephemeral=True)
                return

            embed = discord.Embed(title=f"Dixit: {game_id}", color=discord.Color.blue())
            embed.add_field(name="State", value=game.currentState, inline=True)
            embed.add_field(name="Players", value=", ".join(game.players), inline=True)
            if game.is_started() and not game.is_abandoned():
                embed.add_field(name="Narrator", value=game.get_narrator() or "N/A", inline=True)
                embed.add_field(name="Round", value=str(len(game.sealedRounds) + 1), inline=True)
                phrase = game.currentRound.get("phrase", "")
                if phrase:
                    embed.add_field(name="Phrase", value=f'"{phrase}"', inline=False)
                scores_embed = build_scores_embed(game)
                await ctx.respond(embeds=[embed, scores_embed], ephemeral=True)
            else:
                await ctx.respond(embed=embed, ephemeral=True)

        @dixit_group.command(name="abandon", description="Abandon the game (creator only)")
        async def cmd_abandon(ctx: discord.ApplicationContext):
            await ctx.defer()
            game_id = self._game_id_from_thread(ctx.channel_id)
            if not game_id:
                await ctx.respond("This isn't a game thread!")
                return
            state = self.games.get(game_id)
            if not state:
                await ctx.respond("Game state not found!")
                return
            discord_user_id = str(ctx.author.id)
            if discord_user_id != state.creator_discord_id:
                await ctx.respond("Only the game creator can abandon the game!")
                return
            try:
                game = get_locked_game_by_id(self.red, game_id)
                player_name = state.player_map.get(discord_user_id)
                game.abandon(player_name)
                update_game(self.red, game)
                await ctx.respond("Game has been abandoned.")
            except LockingException:
                await ctx.respond("Game is busy, try again in a moment.")
            except Exception as e:
                release_lock(self.red, game_id)
                await ctx.respond(f"Error: {e}")

        @dixit_group.command(name="hand", description="View your current hand")
        async def cmd_hand(ctx: discord.ApplicationContext):
            await ctx.defer(ephemeral=True)
            game_id = self._game_id_from_thread(ctx.channel_id)
            if not game_id:
                await ctx.respond("This isn't a game thread!", ephemeral=True)
                return
            state = self.games.get(game_id)
            if not state:
                await ctx.respond("Game state not found!", ephemeral=True)
                return
            discord_user_id = str(ctx.author.id)
            player_name = state.player_map.get(discord_user_id)
            if not player_name:
                await ctx.respond("You're not in this game!", ephemeral=True)
                return
            game = get_game_by_id(self.red, game_id)
            if not game or not game.is_started():
                await ctx.respond("Game hasn't started yet!", ephemeral=True)
                return
            hand = game.currentRound.get("allocations", {}).get(player_name, [])
            if not hand:
                await ctx.respond("You don't have any cards!", ephemeral=True)
                return
            files, embeds = make_card_embeds(state.image_folder, hand)
            await ctx.respond(
                "Your hand:",
                files=files,
                embeds=embeds,
                ephemeral=True,
            )

        @dixit_group.command(name="add-ai", description="Add an AI player (before game starts)")
        async def cmd_add_ai(
            ctx: discord.ApplicationContext,
            name: discord.Option(str, "AI player name (optional)", required=False, default=None),
        ):
            await ctx.defer(ephemeral=True)
            game_id = self._game_id_from_thread(ctx.channel_id)
            if not game_id:
                await ctx.respond("This isn't a game thread!", ephemeral=True)
                return
            state = self.games.get(game_id)
            if not state:
                await ctx.respond("Game state not found!", ephemeral=True)
                return
            discord_user_id = str(ctx.author.id)
            if discord_user_id != state.creator_discord_id:
                await ctx.respond("Only the creator can add AI players!", ephemeral=True)
                return
            game_check = get_game_by_id(self.red, game_id)
            if game_check and len(game_check.players) >= MAX_DISCORD_PLAYERS:
                await ctx.respond(f"Game is full! (max {MAX_DISCORD_PLAYERS} players in Discord)", ephemeral=True)
                return
            try:
                game = get_locked_game_by_id(self.red, game_id)
            except LockingException:
                await ctx.respond("Game is busy, try again.", ephemeral=True)
                return
            try:
                ai_name = game.add_ai_player(name)
                update_game(self.red, game)
            except Exception as e:
                release_lock(self.red, game_id)
                await ctx.respond(f"Error: {e}", ephemeral=True)
                return
            thread = await self._get_thread(game_id)
            if thread:
                players_str = ", ".join(game.players)
                await _silent_send(thread,f"AI player **{ai_name}** joined! Players: {players_str}")
            await ctx.respond(f"Added AI player **{ai_name}**!", ephemeral=True)

    # --- Helper methods ---

    def _game_id_from_thread(self, channel_id: int) -> str | None:
        return self.thread_to_game.get(channel_id)

    def get_player_name(self, game_id: str, discord_user_id: str) -> str | None:
        state = self.games.get(game_id)
        if state:
            return state.player_map.get(discord_user_id)
        return None

    def _get_discord_user_id(self, game_id: str, player_name: str) -> str | None:
        state = self.games.get(game_id)
        if not state:
            return None
        for uid, name in state.player_map.items():
            if name == player_name:
                return uid
        return None

    async def _get_thread(self, game_id: str) -> discord.Thread | None:
        state = self.games.get(game_id)
        if not state:
            return None
        try:
            return await self.bot.fetch_channel(state.thread_id)
        except Exception:
            return None

    # --- AI turn processing ---

    async def _process_ai_turns(self, game_id: str):
        """Process all pending AI actions, with delays to feel natural."""
        await asyncio.sleep(random.uniform(1.5, 3.0))

        result = do_one_ai_action(self.red, game_id)
        if result is None:
            return

        thread = await self._get_thread(game_id)
        action = result['action']
        player = result['player']
        game_state = result['game_state']

        if action == 'narrator':
            phrase = result['phrase']
            if thread:
                await _silent_send(thread,
                    f"The narrator has spoken! The phrase is: **\"{phrase}\"**\n"
                    f"Non-narrators: pick your decoy cards!"
                )
            await self._prompt_decoy_players(game_id)

        elif action == 'decoy':
            if game_state == WAITING_FOR_VOTES:
                await self._start_voting(game_id)
            elif thread:
                game = get_game_by_id(self.red, game_id)
                if game:
                    remaining = [p for p in game.get_non_narrators() if not game.has_set_card(p)]
                    if remaining:
                        await _silent_send(thread,
                            f"**{player}** has played their card. "
                            f"Waiting for: {', '.join(remaining)}"
                        )

        elif action == 'vote':
            if game_state == ROUND_REVEALED:
                await self._show_round_results(game_id)
            elif thread:
                game = get_game_by_id(self.red, game_id)
                if game:
                    remaining = [p for p in game.get_non_narrators() if not game.has_voted(p)]
                    if remaining:
                        await _silent_send(thread,
                            f"**{player}** has voted. Waiting for: {', '.join(remaining)}"
                        )

        # Recursively process more AI turns
        await self._process_ai_turns(game_id)

    # --- Button/interaction handlers ---

    async def handle_join(self, game_id: str, interaction: discord.Interaction):
        discord_user_id = str(interaction.user.id)
        player_name = interaction.user.display_name
        state = self.games.get(game_id)
        if not state:
            await interaction.followup.send("Game not found!", ephemeral=True)
            return
        if discord_user_id in state.player_map:
            await interaction.followup.send("You're already in this game!", ephemeral=True)
            return
        if len(state.player_map) >= MAX_DISCORD_PLAYERS:
            await interaction.followup.send(f"Game is full! (max {MAX_DISCORD_PLAYERS} players in Discord)", ephemeral=True)
            return
        try:
            game = get_locked_game_by_id(self.red, game_id)
        except LockingException:
            await interaction.followup.send("Game is busy, try again.", ephemeral=True)
            return
        try:
            original_name = player_name
            counter = 2
            while player_name in game.players:
                player_name = f"{original_name}_{counter}"
                counter += 1
            game.join(player_name)
            update_game(self.red, game)
        except Exception as e:
            release_lock(self.red, game_id)
            await interaction.followup.send(f"Couldn't join: {e}", ephemeral=True)
            return
        state.player_map[discord_user_id] = player_name
        thread = await self._get_thread(game_id)
        if thread:
            players_str = ", ".join(game.players)
            await _silent_send(thread,f"**{player_name}** joined! Players: {players_str}")
        await interaction.followup.send(f"You joined as **{player_name}**!", ephemeral=True)

    async def handle_add_ai(self, game_id: str, interaction: discord.Interaction):
        discord_user_id = str(interaction.user.id)
        state = self.games.get(game_id)
        if not state:
            await interaction.followup.send("Game not found!", ephemeral=True)
            return
        if discord_user_id != state.creator_discord_id:
            await interaction.followup.send("Only the creator can add AI players!", ephemeral=True)
            return
        game_check = get_game_by_id(self.red, game_id)
        if game_check and len(game_check.players) >= MAX_DISCORD_PLAYERS:
            await interaction.followup.send(f"Game is full! (max {MAX_DISCORD_PLAYERS} players in Discord)", ephemeral=True)
            return
        try:
            game = get_locked_game_by_id(self.red, game_id)
        except LockingException:
            await interaction.followup.send("Game is busy, try again.", ephemeral=True)
            return
        try:
            ai_name = game.add_ai_player()
            update_game(self.red, game)
        except Exception as e:
            release_lock(self.red, game_id)
            await interaction.followup.send(f"Error: {e}", ephemeral=True)
            return
        thread = await self._get_thread(game_id)
        if thread:
            players_str = ", ".join(game.players)
            await _silent_send(thread,f"AI player **{ai_name}** joined! Players: {players_str}")
        await interaction.followup.send(f"Added AI player **{ai_name}**!", ephemeral=True)

    async def handle_start(self, game_id: str, interaction: discord.Interaction):
        discord_user_id = str(interaction.user.id)
        state = self.games.get(game_id)
        if not state:
            await interaction.followup.send("Game not found!", ephemeral=True)
            return
        if discord_user_id != state.creator_discord_id:
            await interaction.followup.send("Only the creator can start the game!", ephemeral=True)
            return
        try:
            game = get_locked_game_by_id(self.red, game_id)
        except LockingException:
            await interaction.followup.send("Game is busy, try again.", ephemeral=True)
            return
        try:
            game.start()
            update_game(self.red, game)
        except Exception as e:
            release_lock(self.red, game_id)
            await interaction.followup.send(f"Couldn't start: {e}", ephemeral=True)
            return
        thread = await self._get_thread(game_id)
        if thread:
            await _silent_send(thread,"**Game started!** Let the storytelling begin...")
        await interaction.followup.send("Game started!", ephemeral=True)
        await self._prompt_narrator(game_id)
        await self._process_ai_turns(game_id)

    # --- Game phase prompts (all in-thread) ---

    async def _prompt_narrator(self, game_id: str):
        game = get_game_by_id(self.red, game_id)
        if not game:
            return
        state = self.games.get(game_id)
        if not state:
            return

        narrator = game.get_narrator()
        narrator_discord_id = self._get_discord_user_id(game_id, narrator)
        round_num = len(game.sealedRounds) + 1

        thread = await self._get_thread(game_id)
        if not thread:
            return

        # If narrator is AI, don't post the button
        if game.is_ai_player(narrator):
            await _silent_send(thread,f"**Round {round_num}**: **{narrator}** (AI) is the narrator...")
            return

        mention = f"<@{narrator_discord_id}>" if narrator_discord_id else narrator
        view = PickCardButton(self, game_id, is_narrator=True)
        await _silent_send(thread,
            f"**Round {round_num}**: {mention} is the narrator!\n"
            f"Click the button below to see your hand and pick a card.",
            view=view,
        )

    async def handle_pick_card_click(
        self, game_id: str, discord_user_id: str, is_narrator: bool,
        interaction: discord.Interaction,
    ):
        """Handle click on Pick Card button — show hand ephemerally."""
        state = self.games.get(game_id)
        if not state:
            await interaction.followup.send("Game not found!", ephemeral=True)
            return

        player_name = state.player_map.get(discord_user_id)
        if not player_name:
            await interaction.followup.send("You're not in this game!", ephemeral=True)
            return

        game = get_game_by_id(self.red, game_id)
        if not game:
            await interaction.followup.send("Game not found!", ephemeral=True)
            return

        # Validate the player should be picking
        if is_narrator:
            if not game.is_narrator(player_name):
                await interaction.followup.send("You're not the narrator!", ephemeral=True)
                return
            if game.has_set_card(player_name):
                await interaction.followup.send("You already played your card!", ephemeral=True)
                return
        else:
            if game.is_narrator(player_name):
                await interaction.followup.send("You're the narrator — you already played!", ephemeral=True)
                return
            if game.has_set_card(player_name):
                await interaction.followup.send("You already played your decoy!", ephemeral=True)
                return

        hand = game.currentRound.get("allocations", {}).get(player_name, [])
        if not hand:
            await interaction.followup.send("You don't have any cards!", ephemeral=True)
            return

        files, embeds = make_card_embeds(state.image_folder, hand)

        if is_narrator:
            view = NarratorCardSelectView(self, game_id, player_name, hand)
            await interaction.followup.send(
                "**Your hand** — Pick a card, then you'll enter a phrase.",
                files=files,
                embeds=embeds,
                view=view,
                ephemeral=True,
            )
        else:
            phrase = game.currentRound.get("phrase", "")
            view = DecoyCardSelectView(self, game_id, player_name, hand)
            await interaction.followup.send(
                f"**Phrase: \"{phrase}\"** — Pick a decoy card!",
                files=files,
                embeds=embeds,
                view=view,
                ephemeral=True,
            )

    async def handle_narrator_card(
        self, game_id: str, player_name: str, card: int, phrase: str,
        interaction: discord.Interaction,
    ):
        try:
            game = get_locked_game_by_id(self.red, game_id)
        except LockingException:
            await interaction.followup.send("Game is busy, try again.", ephemeral=True)
            return
        try:
            game.set_narrator_card(player_name, card, phrase)
            update_game(self.red, game)
        except Exception as e:
            release_lock(self.red, game_id)
            await interaction.followup.send(f"Error: {e}", ephemeral=True)
            return

        await interaction.followup.send(f"You played your card with phrase: \"{phrase}\"", ephemeral=True)

        thread = await self._get_thread(game_id)
        if thread:
            await _silent_send(thread,
                f"The narrator has spoken! The phrase is: **\"{phrase}\"**\n"
                f"Non-narrators: pick your decoy cards!"
            )

        await self._prompt_decoy_players(game_id)
        await self._process_ai_turns(game_id)

    async def _prompt_decoy_players(self, game_id: str):
        game = get_game_by_id(self.red, game_id)
        if not game or game.currentState != WAITING_FOR_PLAYERS:
            return

        # Check if any human players need to pick
        state = self.games.get(game_id)
        if not state:
            return

        human_remaining = []
        for player_name in game.get_non_narrators():
            if not game.is_ai_player(player_name) and not game.has_set_card(player_name):
                human_remaining.append(player_name)

        if not human_remaining:
            return  # All remaining are AI, handled by _process_ai_turns

        thread = await self._get_thread(game_id)
        if thread:
            view = PickCardButton(self, game_id, is_narrator=False)
            mentions = []
            for p in human_remaining:
                uid = self._get_discord_user_id(game_id, p)
                mentions.append(f"<@{uid}>" if uid else p)
            await _silent_send(thread,
                f"{', '.join(mentions)} — click below to see your hand and pick a decoy card!",
                view=view,
            )

    async def handle_decoy_card(
        self, game_id: str, player_name: str, card: int,
        interaction: discord.Interaction,
    ):
        try:
            game = get_locked_game_by_id(self.red, game_id)
        except LockingException:
            await interaction.followup.send("Game is busy, try again.", ephemeral=True)
            return
        try:
            game.set_decoy_card(player_name, card)
            update_game(self.red, game)
        except Exception as e:
            release_lock(self.red, game_id)
            await interaction.followup.send(f"Error: {e}", ephemeral=True)
            return

        await interaction.followup.send("You played your decoy card!", ephemeral=True)

        thread = await self._get_thread(game_id)
        if thread:
            remaining = [p for p in game.get_non_narrators() if not game.has_set_card(p)]
            if remaining:
                await _silent_send(thread,
                    f"**{player_name}** has played their card. "
                    f"Waiting for: {', '.join(remaining)}"
                )

        if game.currentState == WAITING_FOR_VOTES:
            await self._start_voting(game_id)
        else:
            await self._process_ai_turns(game_id)

    async def _start_voting(self, game_id: str):
        game = get_game_by_id(self.red, game_id)
        if not game or game.currentState != WAITING_FOR_VOTES:
            return
        state = self.games.get(game_id)
        if not state:
            return
        thread = await self._get_thread(game_id)
        if not thread:
            return

        played_cards = game.get_played_cards()
        phrase = game.currentRound.get("phrase", "")

        # Send cards to thread with labeled embeds
        files, embeds = make_card_embeds(state.image_folder, played_cards)

        await _silent_send(thread,
            f"**Time to vote!**\n"
            f"Phrase: **\"{phrase}\"**\n"
            f"Click a button to vote for the card you think is the narrator's!\n"
            f"(You cannot vote for your own card)",
            files=files,
            embeds=embeds,
        )

        vote_view = VoteView(self, game_id, played_cards)
        await _silent_send(thread,"Vote:", view=vote_view)
        if ENABLE_LOL:
            lol_view = LolView(self, game_id, played_cards)
            await _silent_send(thread,
                "(Optional) Give a Lol to a card you appreciate!",
                view=lol_view,
            )

        # AI players vote
        await self._process_ai_turns(game_id)

    async def handle_vote(
        self, game_id: str, player_name: str, card: int,
        interaction: discord.Interaction,
    ):
        # Check narrator before acquiring lock
        game_check = get_game_by_id(self.red, game_id)
        if game_check and game_check.is_narrator(player_name):
            await interaction.followup.send("The narrator cannot vote!", ephemeral=True)
            return

        try:
            game = get_locked_game_by_id(self.red, game_id)
        except LockingException:
            await interaction.followup.send("Game is busy, try again.", ephemeral=True)
            return
        try:
            game.cast_vote(player_name, card)
            update_game(self.red, game)
        except Exception as e:
            release_lock(self.red, game_id)
            await interaction.followup.send(f"Error: {e}", ephemeral=True)
            return

        await interaction.followup.send("Your vote has been recorded!", ephemeral=True)

        thread = await self._get_thread(game_id)
        if thread:
            remaining = [p for p in game.get_non_narrators() if not game.has_voted(p)]
            if remaining:
                await _silent_send(thread,
                    f"**{player_name}** has voted. Waiting for: {', '.join(remaining)}"
                )

        if game.currentState == ROUND_REVEALED:
            await self._show_round_results(game_id)
        else:
            await self._process_ai_turns(game_id)

    async def handle_lol(
        self, game_id: str, player_name: str, card: int,
        interaction: discord.Interaction,
    ):
        try:
            game = get_locked_game_by_id(self.red, game_id)
        except LockingException:
            await interaction.followup.send("Game is busy, try again.", ephemeral=True)
            return
        try:
            game.cast_lol(player_name, card)
            update_game(self.red, game)
        except Exception as e:
            release_lock(self.red, game_id)
            await interaction.followup.send(f"Error: {e}", ephemeral=True)
            return
        await interaction.followup.send("Lol recorded!", ephemeral=True)

    async def _show_round_results(self, game_id: str):
        game = get_game_by_id(self.red, game_id)
        if not game:
            return
        thread = await self._get_thread(game_id)
        if not thread:
            return

        state = self.games.get(game_id)
        image_folder = state.image_folder if state else None
        results_embed, narrator_file = build_round_results_embed(game, image_folder)

        send_kwargs = {"embed": results_embed}
        if narrator_file:
            send_kwargs["file"] = narrator_file

        if game.has_ended():
            winners_embed = build_winners_embed(game)
            send_kwargs["embeds"] = [results_embed, winners_embed]
            del send_kwargs["embed"]
            await _silent_send(thread,**send_kwargs)
            await _silent_send(thread,"**Game over!** Thanks for playing!")
        else:
            view = NextRoundView(self, game_id)
            send_kwargs["view"] = view
            await _silent_send(thread,**send_kwargs)

    async def handle_next_round(self, game_id: str, interaction: discord.Interaction):
        try:
            game = get_locked_game_by_id(self.red, game_id)
        except LockingException:
            await interaction.followup.send("Game is busy, try again.")
            return
        try:
            added = game.start_next_round()
            update_game(self.red, game)
        except Exception as e:
            release_lock(self.red, game_id)
            await interaction.followup.send(f"Error: {e}")
            return

        # start_next_round may have ended the game
        if game.has_ended():
            await self._show_round_results(game_id)
            return

        thread = await self._get_thread(game_id)
        if thread and added:
            for p in added:
                await _silent_send(thread,f"**{p}** joined from the lobby!")

        await self._prompt_narrator(game_id)
        await self._process_ai_turns(game_id)


def run_bot():
    dixit = DixitBot()
    dixit.bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    run_bot()
