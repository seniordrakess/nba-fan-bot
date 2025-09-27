import os
import discord
from discord.ext import tasks, commands
from nba_api_utils import get_upcoming_games
import json

# Discord bot token from GitHub Secret
TOKEN = os.getenv("DISCORD_TOKEN")

# Your Discord channel ID (safe to hardcode)
CHANNEL_ID = 1385365131508056074  # replace with your channel ID

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

STATE_FILE = "games_state.json"

# Load previous game state to avoid duplicate notifications
def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    check_games.start()

# This task runs every 5 minutes to check upcoming games
@tasks.loop(minutes=5)
async def check_games():
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("Channel not found. Make sure the bot is in the server and CHANNEL_ID is correct.")
        return

    state = load_state()
    games = get_upcoming_games()

    for game_str in games:
        if game_str not in state:
            # New upcoming game detected, send notification
            await channel.send(f"📅 **Upcoming NBA Game:** {game_str}")
            state[game_str] = "announced"

    save_state(state)

# Run the bot
bot.run(TOKEN)
