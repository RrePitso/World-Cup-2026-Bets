"""
LangChain tool wrappers around the existing prediction/betting pipeline.
These call the real functions in src/inference, src/models, src/data, src/utils —
no logic is duplicated here.
"""
from langchain.tools import tool
from src.inference.predict import predict_match, load_models
from src.models.dixon_coles import smart_goal_lines
from src.data.fetcher import fetch_venue_weather
from src.utils.betting import calc_ev, ev_flag
from src.agent.knowledge import search_team_news as _search_team_news


def build_tools(gemini_api_key: str):
    """Factory so tools can close over the API key needed for the RAG embeddings."""

    @tool
    def get_match_prediction(home_team: str, away_team: str) -> dict:
        """Predict 1X2 outcome probabilities for a match between two national teams."""
        return predict_match(home_team, away_team)

    @tool
    def get_betting_value(our_prob: float, bookmaker_odds: float) -> dict:
        """Calculate EV, edge, and Kelly stake given a model probability and bookmaker decimal odds."""
        ev, edge, kelly = calc_ev(our_prob, bookmaker_odds)
        return {"ev": ev, "edge": edge, "kelly_stake": kelly, "flag": ev_flag(ev, edge)}

    @tool
    def get_goal_lines(home_team: str, away_team: str, venue: str, match_date: str) -> dict:
        """Get weather-adjusted expected goals and smart over/under lines for a match. match_date format: YYYY-MM-DD."""
        weather = fetch_venue_weather(venue, match_date)
        state = load_models()['state']
        mode, lam, exp_h, exp_a, lines = smart_goal_lines(home_team, away_team, weather, state)
        return {
            "predicted_total_goals": lam,
            "expected_home_goals": exp_h,
            "expected_away_goals": exp_a,
            "suggested_lines": lines,
        }

    @tool
    def search_team_news(team: str) -> str:
        """Retrieve recent news/context notes about a specific national team."""
        return _search_team_news(team, gemini_api_key)

    return [get_match_prediction, get_betting_value, get_goal_lines, search_team_news]
