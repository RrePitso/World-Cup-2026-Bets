"""
LangChain tool wrappers around the existing prediction/betting pipeline.
These call the real functions in src/inference, src/models, src/data, src/utils —
no logic is duplicated here.
"""
import streamlit as st
import pandas as pd
import pyodbc
from langchain.tools import tool
from src.inference.predict import predict_match
from src.models.dixon_coles import smart_goal_lines
from src.data.fetcher import fetch_venue_weather
from src.utils.betting import calc_ev, ev_flag
from src.agent.knowledge import search_team_news as _search_team_news

def _get_fabric_prediction(home_team: str, away_team: str) -> dict:
    """Fallback / primary retriever from Microsoft Fabric Gold Layer."""
    try:
        conn = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER=tcp:{st.secrets['fabric']['server']},1433;"
            f"DATABASE={st.secrets['fabric']['database']};"
            f"UID={st.secrets['fabric']['username']};"
            f"PWD={st.secrets['fabric']['password']};"
            "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
            "Authentication=ActiveDirectoryServicePrincipal;"
        )
        query = """
            SELECT TOP 1 
                prob_home_win, prob_draw, prob_away_win, 
                dc_exp_home, dc_exp_away, predicted_total_goals
            FROM dbo.gold_match_predictions
            WHERE (LOWER(home_team) LIKE ? AND LOWER(away_team) LIKE ?)
               OR (LOWER(home_team) LIKE ? AND LOWER(away_team) LIKE ?)
        """
        h_clean = f"%{home_team.strip().lower()}%"
        a_clean = f"%{away_team.strip().lower()}%"
        
        df = pd.read_sql(query, conn, params=(h_clean, a_clean, a_clean, h_clean))
        conn.close()
        
        if not df.empty:
            row = df.iloc[0]
            return {
                "home": float(row['prob_home_win']),
                "draw": float(row['prob_draw']),
                "away": float(row['prob_away_win'])
            }
    except Exception:
        pass
    return None

def build_tools(gemini_api_key: str):
    """Factory so tools can close over the API key needed for the RAG embeddings."""

    @tool
    def get_match_prediction(home_team: str, away_team: str) -> dict:
        """Predict 1X2 outcome probabilities for a match between two national teams."""
        try:
            # First try local model prediction
            result = predict_match(home_team, away_team)
            if isinstance(result, dict) and any(result.values()):
                return {str(k): float(v) for k, v in result.items()}
        except Exception:
            pass
        
        # Fallback to Microsoft Fabric Gold Layer if local models fail
        fabric_result = _get_fabric_prediction(home_team, away_team)
        if fabric_result:
            return fabric_result
            
        return {"error": "Model and Fabric predictions unavailable", "home": 0.0, "draw": 0.0, "away": 0.0}

    @tool
    def get_betting_value(our_prob: float, bookmaker_odds: float) -> dict:
        """Calculate EV, edge, and Kelly stake given a model probability and bookmaker decimal odds."""
        try:
            ev, edge, kelly = calc_ev(float(our_prob), float(bookmaker_odds))
            return {
                "ev": float(ev),
                "edge": float(edge),
                "kelly_stake": float(kelly),
                "flag": str(ev_flag(ev, edge))
            }
        except Exception as e:
            return {"error": str(e), "ev": 0.0, "edge": 0.0, "kelly_stake": 0.0, "flag": "error"}

    @tool
    def get_goal_lines(home_team: str, away_team: str, venue: str, match_date: str) -> dict:
        """Get weather-adjusted expected goals and smart over/under lines for a match. match_date format: YYYY-MM-DD."""
        try:
            weather = fetch_venue_weather(venue, match_date)
            # Safe model state loader fallback if model files are missing
            try:
                from src.inference.predict import load_models
                state = load_models().get('state')
            except Exception:
                state = None
            mode, lam, exp_h, exp_a, lines = smart_goal_lines(home_team, away_team, weather, state)
            return {
                "predicted_total_goals": float(lam),
                "expected_home_goals": float(exp_h),
                "expected_away_goals": float(exp_a),
                "suggested_lines": lines if isinstance(lines, dict) else {}
            }
        except Exception as e:
            return {"error": str(e), "predicted_total_goals": 0.0, "expected_home_goals": 0.0, "expected_away_goals": 0.0, "suggested_lines": {}}

    @tool
    def search_team_news(team: str) -> str:
        """Retrieve recent news/context notes about a specific national team."""
        try:
            return _search_team_news(team, gemini_api_key)
        except Exception as e:
            return f"Could not retrieve news for {team}: {str(e)}"

    return [get_match_prediction, get_betting_value, get_goal_lines, search_team_news]
