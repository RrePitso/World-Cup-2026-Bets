from scipy.stats import poisson
from src.config import host_teams
from src.data.preprocessor import team_form_stats

def predict_goals_dc(home_team, away_team, weather, state_dicts):
    _, _, h_scored, h_conceded = team_form_stats(home_team, state_dicts['team_history'])
    _, _, a_scored, a_conceded = team_form_stats(away_team, state_dicts['team_history'])

    home_attack  = h_scored
    home_defence = h_conceded
    away_attack  = a_scored
    away_defence = a_conceded

    home_adv = 1.1 if home_team not in host_teams else 1.0

    exp_home = home_attack * away_defence * home_adv
    exp_away = away_attack * home_defence

    if weather:
        heat_stress = max(0, (weather['temp_c'] - 25) / 40)
        wind_factor = max(0, (weather['wind_kmh'] - 30) / 100)
        rain_factor = min(0.1, weather['precip_mm'] / 100)
        penalty     = 1 - (heat_stress * 0.08 + wind_factor * 0.05 + rain_factor)
        exp_home *= penalty
        exp_away *= penalty

    exp_home = max(round(exp_home, 2), 0.3)
    exp_away = max(round(exp_away, 2), 0.3)
    return exp_home, exp_away

def predict_over_line(exp_h, exp_a, line):
    lam       = exp_h + exp_a
    threshold = int(line)
    p_under   = poisson.cdf(threshold, lam)
    return round(1 - p_under, 3), round(p_under, 3)

def smart_goal_lines(home_team, away_team, weather, state_dicts):
    exp_h, exp_a = predict_goals_dc(home_team, away_team, weather, state_dicts)
    lam  = exp_h + exp_a
    mode = max(1, int(lam))

    low_line,  high_line  = mode - 0.5, mode + 0.5
    lo, lu = predict_over_line(exp_h, exp_a, low_line)
    ho, hu = predict_over_line(exp_h, exp_a, high_line)

    return mode, lam, exp_h, exp_a, [
        {'line': low_line,  'over': lo, 'under': lu},
        {'line': high_line, 'over': ho, 'under': hu},
    ]
