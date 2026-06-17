import os
import joblib
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, mean_absolute_error, classification_report
from sklearn.calibration import CalibratedClassifierCV
from src.config import MODEL_DIR, confederation_map
from src.data.fetcher import load_international_results
from src.data.preprocessor import build_training_data

def train_pipeline():
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    print("Loading data...")
    df_intl = load_international_results()
    
    print("Preprocessing & building features...")
    df_model, state_dicts = build_training_data(df_intl)
    
    # Save State
    joblib.dump(state_dicts, f"{MODEL_DIR}/state_v4.pkl")
    
    le = LabelEncoder()
    all_teams = pd.concat([df_model['home_team'], df_model['away_team']]).unique()
    le.fit(all_teams)
    df_model['home_team_encoded'] = le.transform(df_model['home_team'])
    df_model['away_team_encoded'] = le.transform(df_model['away_team'])
    
    conf_encoder = LabelEncoder()
    conf_encoder.fit(list(set(confederation_map.values())) + ['OTHER'])
    df_model['home_conf'] = conf_encoder.transform(df_model['home_conf'])
    df_model['away_conf'] = conf_encoder.transform(df_model['away_conf'])
    
    le_result = LabelEncoder()
    df_model['result_encoded'] = le_result.fit_transform(df_model['result'])

    features = [
        'home_team_encoded', 'away_team_encoded', 'home_elo', 'away_elo', 'elo_diff',
        'home_form', 'away_form', 'home_avg_gd', 'away_avg_gd', 'gd_diff',
        'home_avg_scored', 'away_avg_scored', 'home_avg_conceded', 'away_avg_conceded',
        'h2h_home_winrate', 'home_conf', 'away_conf', 'home_gdp_ratio', 'away_gdp_ratio', 'gdp_diff',
        'home_pop_ratio', 'away_pop_ratio', 'home_temp_score', 'away_temp_score', 'temp_diff',
        'home_squad_ratio', 'away_squad_ratio', 'squad_ratio_diff', 'matchday', 'neutral', 'tournament_weight'
    ]
    joblib.dump(features, f"{MODEL_DIR}/features_list_v4.pkl")

    df_model = df_model.sort_values('date').reset_index(drop=True)
    split_idx  = int(len(df_model) * 0.85)
    train      = df_model.iloc[:split_idx]
    test       = df_model.iloc[split_idx:]
    
    X_train, y_train = train[features], train['result_encoded']
    X_test,  y_test  = test[features],  test['result_encoded']
    y_train_goals = train['over_2_5']
    y_test_goals  = test['over_2_5']
    y_train_goals_reg = train['total_goals']
    y_test_goals_reg  = test['total_goals']

    joblib.dump(le, f"{MODEL_DIR}/team_encoder_v4.pkl")
    joblib.dump(le_result, f"{MODEL_DIR}/result_encoder_v4.pkl")
    joblib.dump(conf_encoder, f"{MODEL_DIR}/conf_encoder_v4.pkl")

    print("Training models...")
    rf_base = RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_leaf=5, class_weight='balanced_subsample', random_state=42, n_jobs=-1)
    model = CalibratedClassifierCV(rf_base, method='sigmoid', cv=5)
    model.fit(X_train, y_train)

    goals_reg_base = RandomForestRegressor(n_estimators=300, max_depth=12, min_samples_leaf=5, random_state=42, n_jobs=-1)
    goals_reg_base.fit(X_train, y_train_goals_reg)
    
    goals_base = GradientBoostingClassifier(n_estimators=200, max_depth=4, random_state=42)
    goals_model = CalibratedClassifierCV(goals_base, method='sigmoid', cv=5)
    goals_model.fit(X_train, y_train_goals)

    y_pred_reg = goals_reg_base.predict(X_test)
    print("\n===== GOAL REGRESSOR MODEL (Continuous) =====")
    print("Mean Absolute Error (Goals):", round(mean_absolute_error(y_test_goals_reg, y_pred_reg), 4))

    y_pred = model.predict(X_test)
    print("\n===== RESULT MODEL =====")
    print("Accuracy:", round(accuracy_score(y_test, y_pred), 4))

    joblib.dump(model, f"{MODEL_DIR}/rf_worldcup_model_v4.pkl")
    joblib.dump(goals_model, f"{MODEL_DIR}/goals_model_v4.pkl")
    joblib.dump(goals_reg_base, f"{MODEL_DIR}/goals_regressor_v4.pkl")
    print("✅ Models saved!")

if __name__ == "__main__":
    train_pipeline()
