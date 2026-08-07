import os

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("FPL_API_BASE_URL", "https://fantasy.premierleague.com/api")


class FPLClient:
    def __init__(self):
        self.session = requests.Session()

    def get_bootstrap_static(self) -> dict:
        """Returns teams, players, gameweeks, and game settings in one payload."""
        resp = self.session.get(f"{BASE_URL}/bootstrap-static/")
        resp.raise_for_status()
        return resp.json()

    def get_fixtures(self) -> list[dict]:
        """Returns all fixtures for the season."""
        resp = self.session.get(f"{BASE_URL}/fixtures/")
        resp.raise_for_status()
        return resp.json()

    def get_player_summary(self, player_id: int) -> dict:
        """Returns a specific player's gameweek-by-gameweek history."""
        resp = self.session.get(f"{BASE_URL}/element-summary/{player_id}/")
        resp.raise_for_status()
        return resp.json()