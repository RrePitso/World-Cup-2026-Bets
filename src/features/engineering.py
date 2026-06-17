import pandas as pd
from src.config import gdp_per_capita, world_avg_gdp, population, world_population, temperature, squad_strength, world_avg_squad, confederation_map

def get_gdp_ratio(team):   return gdp_per_capita.get(team, world_avg_gdp) / world_avg_gdp
def get_pop_ratio(team):   return population.get(team, 50) / world_population
def get_temp_score(team):  return 1 / (1 + abs(temperature.get(team, 14) - 14))
def get_squad_ratio(team): return squad_strength.get(team, world_avg_squad) / world_avg_squad

def build_feature_row(home_team, away_team, neutral, tournament_weight, matchday, state_dicts, le, conf_encoder, features_list):
    from src.data.preprocessor import team_form_stats
    
    elo_ratings = state_dicts['elo_ratings']
    team_history = state_dicts['team_history']
    h2h_wins = state_dicts['h2h_wins']
    h2h_total = state_dicts['h2h_total']

    home_enc = le.transform([home_team])[0] if home_team in le.classes_ else 0
    away_enc = le.transform([away_team])[0] if away_team in le.classes_ else 0

    h_elo = elo_ratings.get(home_team, 1000.0)
    a_elo = elo_ratings.get(away_team, 1000.0)
    h_form, h_gd, h_scored, h_conceded = team_form_stats(home_team, team_history)
    a_form, a_gd, a_scored, a_conceded = team_form_stats(away_team, team_history)
    
    h2h_t    = h2h_total.get(home_team, {}).get(away_team, 0)
    h2h_w    = h2h_wins.get(home_team, {}).get(away_team, 0)
    h2h_rate = (h2h_w / h2h_t) if h2h_t > 0 else 0.5

    row = {
        'home_team_encoded': home_enc, 'away_team_encoded': away_enc,
        'home_elo': h_elo, 'away_elo': a_elo, 'elo_diff': h_elo - a_elo,
        'home_form': h_form, 'away_form': a_form,
        'home_avg_gd': h_gd, 'away_avg_gd': a_gd, 'gd_diff': h_gd - a_gd,
        'home_avg_scored': h_scored, 'away_avg_scored': a_scored,
        'home_avg_conceded': h_conceded, 'away_avg_conceded': a_conceded,
        'h2h_home_winrate': h2h_rate,
        'home_conf': conf_encoder.transform([confederation_map.get(home_team, 'OTHER')])[0],
        'away_conf': conf_encoder.transform([confederation_map.get(away_team, 'OTHER')])[0],
        'home_gdp_ratio': get_gdp_ratio(home_team), 'away_gdp_ratio': get_gdp_ratio(away_team),
        'gdp_diff':       get_gdp_ratio(home_team)  - get_gdp_ratio(away_team),
        'home_pop_ratio': get_pop_ratio(home_team),  'away_pop_ratio': get_pop_ratio(away_team),
        'home_temp_score':get_temp_score(home_team), 'away_temp_score':get_temp_score(away_team),
        'temp_diff':      get_temp_score(home_team)  - get_temp_score(away_team),
        'home_squad_ratio': get_squad_ratio(home_team),
        'away_squad_ratio': get_squad_ratio(away_team),
        'squad_ratio_diff': get_squad_ratio(home_team) - get_squad_ratio(away_team),
        'matchday':           matchday,
        'neutral':            neutral,
        'tournament_weight':  tournament_weight,
    }
    return pd.DataFrame([row], columns=features_list)
