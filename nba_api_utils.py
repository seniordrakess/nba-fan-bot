from datetime import datetime, timedelta
import requests

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

