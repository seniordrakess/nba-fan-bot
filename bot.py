import os
import discord
from discord.ext import tasks, commands
from datetime import datetime, timedelta
import requests
import json
from flask import Flask
import threading

# ----------------------------
# Discord setup
# ----------------------------
TOKEN = os.getenv("DISCORD_TOKEN")  # must be set in Replit secrets
CHANNEL_ID = 1385365131508056074  # replace with your Discord channel ID

if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable not set!")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

STATE_FILE = "games_state.json"

# ----------------------------
# NBA API utilities
# ----------------------------
NBA_API_URL = "https://www.balldontlie.io/api/v1/games"

def get_upcoming_games():
    today = datetime.today()
    end_date = today + timedelta(days=30)
    params = {
        "start_date": today.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "per_page": 100
    }
    response = requests.get(NBA_API_URL, params=params)
    data = response.json()
    games_list = []
    for game in data['data']:
        home = game['home_team']['full_name']
        visitor = game['visitor_team']['full_name']
        date = game['date'][:10]
        status = game['status']
        games_list.append(f"{date} | {visitor} @ {home} | {status}")
    return games_list

# ----------------------------
# State handling
# ----------------------------
def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# ----------------------------
# Discord bot events
# ----------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    check_games.start()

@tasks.loop(minutes=5)
async def check_games():
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("Channel not found. Check CHANNEL_ID and bot permissions.")
        return

    state = load_state()
    games = get_upcoming_games()

    for game_str in games:
        if game_str not in state:
            # Send notification for new upcoming game
            await channel.send(f"📅 **Upcoming NBA Game:** {game_str}")
            state[game_str] = "announced"

    save_state(state)

# ----------------------------
# Flask app for uptime monitoring
# ----------------------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host="0.0.0.0", port=3000)

# Run Flask in a separate thread so it doesn’t block the bot
threading.Thread(target=run_flask).start()

# ----------------------------
# Run bot
# ----------------------------
bot.run(TOKEN)
