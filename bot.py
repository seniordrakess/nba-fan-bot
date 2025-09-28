import os
import discord
from discord.ext import tasks, commands
from datetime import datetime, timedelta
import requests
import json
from flask import Flask
import threading
import pytz  # For timezone handling

# ----------------------------
# Discord setup
# ----------------------------
TOKEN = os.getenv("DISCORD_TOKEN")  # Discord bot token
CHANNEL_ID = 1385365131508056074    # Replace with your Discord channel ID

if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable not set!")

intents = discord.Intents.default()
intents.message_content = True  # Required to avoid warnings
bot = commands.Bot(command_prefix="!", intents=intents)

STATE_FILE = "games_state.json"

# ----------------------------
# NBA API setup
# ----------------------------
NBA_API_KEY = os.getenv("NBA_API_KEY")  # optional if balldontlie requires key
NBA_API_URL = "https://www.balldontlie.io/api/v1/games"

def get_upcoming_games():
    """Fetch upcoming NBA games for the next 30 days."""
    today = datetime.utcnow()
    end_date = today + timedelta(days=30)
    params = {
        "start_date": today.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "per_page": 100
    }
    headers = {}
    if NBA_API_KEY:
        headers["Authorization"] = f"Bearer {NBA_API_KEY}"

    try:
        response = requests.get(NBA_API_URL, params=params, headers=headers)
        data = response.json()
    except Exception:
        # fallback test data if API fails
        data = {"data": [
            {"date": today.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
             "home_team": {"full_name": "Test Home"},
             "visitor_team": {"full_name": "Test Visitor"},
             "home_team_score": 0,
             "visitor_team_score": 0,
             "status": "Scheduled"}
        ]}
    games_list = []
    for game in data['data']:
        date_utc = datetime.fromisoformat(game['date'][:-1]).replace(tzinfo=pytz.UTC)
        home = game['home_team']['full_name']
        visitor = game['visitor_team']['full_name']
        status = game['status']
        score = f"{game.get('visitor_team_score', 0)}-{game.get('home_team_score',0)}"
        games_list.append({
            "str": f"{date_utc.strftime('%Y-%m-%d %H:%M UTC')} | {visitor} @ {home} | {status} | {score}",
            "date": date_utc,
            "home": home,
            "visitor": visitor,
            "status": status,
            "score": score
        })
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
    now = datetime.utcnow().replace(tzinfo=pytz.UTC)

    for game in games:
        game_id = game['str']
        game_time = game['date']
        status = game['status']

        # Pre-game alert 15 min before tip-off
        if status == "Scheduled" and 0 <= (game_time - now).total_seconds() <= 900:
            if state.get(game_id) != "pre-alert":
                await channel.send(f"⏰ **Game starting soon!** {game_id}")
                state[game_id] = "pre-alert"

        # Post-game alert when finished
        if status == "Final":
            if state.get(game_id) != "final":
                await channel.send(f"🏁 **Game Finished!** {game_id}")
                state[game_id] = "final"

    save_state(state)

# ----------------------------
# Flask app for uptime monitoring
# ----------------------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host="0.0.0.0", port=5000)

# Run Flask in a separate thread
threading.Thread(target=run_flask).start()

# ----------------------------
# Run bot
# ----------------------------
bot.run(TOKEN)
