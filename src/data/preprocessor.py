import pandas as pd
from collections import defaultdict, deque
from src.config import K, TRAIN_START, confederation_map
from src.features.engineering import get_gdp_ratio, get_pop_ratio, get_temp_score, get_squad_ratio

def team_form_stats(team, team_history):
    hist = team_history[team]
    if len(hist) == 0:
        return 0.5, 0.0, 1.2, 1.2
    wsum = sum(h['weight'] for h in hist)
    wwin = sum(h['weight'] for h in hist if h['won'])
    form         = wwin / wsum if wsum > 0 else 0.5
    avg_gd       = sum(h['gd']       for h in hist) / len(hist)
    avg_scored   = sum(h['scored']   for h in hist) / len(hist)
    avg_conceded = sum(h['conceded'] for h in hist) / len(hist)
    return form, avg_gd, avg_scored, avg_conceded

def build_training_data(df_intl):
    elo_ratings  = defaultdict(lambda: 1000.0)
    team_history = defaultdict(lambda: deque(maxlen=10))
    h2h_wins     = defaultdict(lambda: defaultdict(int))
    h2h_total    = defaultdict(lambda: defaultdict(int))
    
    rows = []
    
    for _, r in df_intl.iterrows():
        home, away, w = r['home_team'], r['away_team'], r['weight']
        hs, aw = r['home_score'], r['away_score']
        date = r['date']
        
        if pd.isna(hs) or pd.isna(aw):
            continue

        home_elo, away_elo = elo_ratings[home], elo_ratings[away]
        home_form, home_gd, home_scored_avg, home_conceded_avg = team_form_stats(home, team_history)
        away_form, away_gd, away_scored_avg, away_conceded_avg = team_form_stats(away, team_history)
        h2h_t            = h2h_total[home][away]
        h2h_home_winrate = (h2h_wins[home][away] / h2h_t) if h2h_t > 0 else 0.5

        if date >= TRAIN_START:
            total_goals = hs + aw
            rows.append({
                'date': date, 'home_team': home, 'away_team': away,
                'home_elo': home_elo, 'away_elo': away_elo, 'elo_diff': home_elo - away_elo,
                'home_form': home_form, 'away_form': away_form,
                'home_avg_gd': home_gd, 'away_avg_gd': away_gd, 'gd_diff': home_gd - away_gd,
                'home_avg_scored': home_scored_avg, 'away_avg_scored': away_scored_avg,
                'home_avg_conceded': home_conceded_avg, 'away_avg_conceded': away_conceded_avg,
                'h2h_home_winrate': h2h_home_winrate,
                'home_conf': confederation_map.get(home, 'OTHER'),
                'away_conf': confederation_map.get(away, 'OTHER'),
                'home_gdp_ratio':  get_gdp_ratio(home),  'away_gdp_ratio': get_gdp_ratio(away),
                'gdp_diff':        get_gdp_ratio(home)  - get_gdp_ratio(away),
                'home_pop_ratio':  get_pop_ratio(home),  'away_pop_ratio': get_pop_ratio(away),
                'home_temp_score': get_temp_score(home), 'away_temp_score': get_temp_score(away),
                'temp_diff':       get_temp_score(home)  - get_temp_score(away),
                'home_squad_ratio': get_squad_ratio(home),
                'away_squad_ratio': get_squad_ratio(away),
                'squad_ratio_diff': get_squad_ratio(home) - get_squad_ratio(away),
                'neutral':            int(bool(r['neutral'])) if not pd.isna(r['neutral']) else 0,
                'tournament_weight':  w,
                'matchday':           1,
                'result':       'home_win' if hs > aw else ('away_win' if hs < aw else 'draw'),
                'total_goals':  total_goals,
                'over_2_5':     int(total_goals > 2.5),
            })

        expected_home = 1 / (1 + 10 ** ((away_elo - home_elo) / 400))
        actual_home   = 1 if hs > aw else (0.5 if hs == aw else 0)
        elo_ratings[home] += K * w * (actual_home - expected_home)
        elo_ratings[away] += K * w * ((1 - actual_home) - (1 - expected_home))

        home_won, away_won = hs > aw, aw > hs
        team_history[home].append({'weight': w, 'won': home_won, 'gd': hs - aw, 'scored': hs, 'conceded': aw})
        team_history[away].append({'weight': w, 'won': away_won, 'gd': aw - hs, 'scored': aw, 'conceded': hs})
        if home_won:  h2h_wins[home][away] += 1
        elif away_won: h2h_wins[away][home] += 1
        h2h_total[home][away] += 1
        h2h_total[away][home] += 1
        
    state_dicts = {
        'elo_ratings': dict(elo_ratings),
        'team_history': dict(team_history),
        'h2h_wins': dict(h2h_wins),
        'h2h_total': dict(h2h_total)
    }

    return pd.DataFrame(rows), state_dicts
