import joblib
from scipy.stats import poisson
from src.config import MODEL_DIR, host_teams
from src.features.engineering import build_feature_row

# Lazy load models to avoid circular imports / memory bloat
_models = {}

def load_models():
    if not _models:
        _models['model'] = joblib.load(f"{MODEL_DIR}/rf_worldcup_model_v4.pkl")
        _models['goals_reg_model'] = joblib.load(f"{MODEL_DIR}/goals_regressor_v4.pkl")
        _models['le'] = joblib.load(f"{MODEL_DIR}/team_encoder_v4.pkl")
        _models['le_result'] = joblib.load(f"{MODEL_DIR}/result_encoder_v4.pkl")
        _models['conf_encoder'] = joblib.load(f"{MODEL_DIR}/conf_encoder_v4.pkl")
        _models['state'] = joblib.load(f"{MODEL_DIR}/state_v4.pkl")
        _models['features_list'] = joblib.load(f"{MODEL_DIR}/features_list_v4.pkl")
    return _models

def predict_match(home_team, away_team, neutral=None, matchday=1, tournament_weight=3.0):
    m = load_models()
    if neutral is None:
        neutral = 0 if home_team in host_teams else 1
    
    X = build_feature_row(
        home_team, away_team, neutral, tournament_weight, matchday, 
        m['state'], m['le'], m['conf_encoder'], m['features_list']
    )
    probs = m['model'].predict_proba(X)[0]
    return {cls: round(prob, 3) for cls, prob in zip(m['le_result'].classes_, probs)}

def predict_ml_goal_distribution(home_team, away_team, neutral=None, matchday=1, tournament_weight=3.0):
    m = load_models()
    if neutral is None:
        neutral = 0 if home_team in host_teams else 1
        
    X = build_feature_row(
        home_team, away_team, neutral, tournament_weight, matchday, 
        m['state'], m['le'], m['conf_encoder'], m['features_list']
    )

    expected_goals_ml = m['goals_reg_model'].predict(X)[0]

    prob_0_1 = poisson.pmf(0, expected_goals_ml) + poisson.pmf(1, expected_goals_ml)
    prob_2   = poisson.pmf(2, expected_goals_ml)
    prob_3   = poisson.pmf(3, expected_goals_ml)
    prob_4_plus = 1 - (prob_0_1 + prob_2 + prob_3)

    return expected_goals_ml, {
        '0-1': round(prob_0_1, 3),
        '2': round(prob_2, 3),
        '3': round(prob_3, 3),
        '4+': round(prob_4_plus, 3)
    }
