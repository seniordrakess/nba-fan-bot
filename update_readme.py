from nba_api_utils import get_upcoming_games

games = get_upcoming_games()
with open("README.md", "w") as f:
    f.write("# NBA Upcoming Games\n\n")
    for game in games:
        f.write(f"- {game}\n")

