import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import pandas as pd
import pyodbc
from src.utils.betting import calc_ev, ev_flag
from src.data.fetcher import load_international_results

st.set_page_config(page_title="Predictions & EV", page_icon="🔮", layout="wide")
st.title("🔮 Edge Calculator & Predictions")

TEAM_NAME_MAP = {
    'usa': 'united states',
    'us': 'united states',
    'korea republic': 'south korea',
    'dr congo': 'congo dr',
    'czechia': 'czech republic'
}

def normalize_team(name):
    if pd.isna(name): return ""
    clean = str(name).strip().lower()
    return TEAM_NAME_MAP.get(clean, clean)

@st.cache_resource
def init_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER=tcp:{st.secrets['fabric']['server']},1433;"
        f"DATABASE={st.secrets['fabric']['database']};"
        f"UID={st.secrets['fabric']['username']};"
        f"PWD={st.secrets['fabric']['password']};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        "Authentication=ActiveDirectoryServicePrincipal;"
    )

@st.cache_data(ttl=3600)
def get_gold_predictions():
    conn = init_connection()
    query = """
        SELECT 
            home_team, away_team, prob_home_win, prob_draw, prob_away_win, 
            dc_exp_home, dc_exp_away, predicted_total_goals
        FROM dbo.gold_match_predictions
    """
    return pd.read_sql(query, conn)

try:
    with st.spinner("Fetching predictions from Microsoft Fabric..."):
        df_predictions = get_gold_predictions()
    st.success("✅ Connected to Fabric Lakehouse")
except Exception as e:
    st.error(f"Failed to connect to Microsoft Fabric: {e}")
    st.stop()

try:
    df_calendar = load_international_results()
    wc_games = df_calendar[
        (df_calendar['tournament'] == 'FIFA World Cup') & 
        (df_calendar['date'] >= '2026-06-01')
    ].copy()
except Exception as e:
    st.warning(f"Could not load official calendar fixtures: {e}")
    wc_games = pd.DataFrame()

# --- EVALUATION TOGGLE WITH PAGINATION ---
evaluate_mode = st.toggle("📊 Show Actual Results & Evaluate Model Accuracy")

if evaluate_mode and not wc_games.empty:
    st.subheader("Model Post-Mortem: Predictions vs Reality")
    
    wc_games['join_home'] = wc_games['home_team'].apply(normalize_team)
    wc_games['join_away'] = wc_games['away_team'].apply(normalize_team)
    df_predictions['join_home'] = df_predictions['home_team'].apply(normalize_team)
    df_predictions['join_away'] = df_predictions['away_team'].apply(normalize_team)
    
    # LEFT JOIN: Keeps ONLY World Cup games from the calendar
    eval_df = pd.merge(wc_games, df_predictions, on=['join_home', 'join_away'], how='left')
    
    eval_df['home_score'] = eval_df['home_score'].fillna(-1)
    eval_df['away_score'] = eval_df['away_score'].fillna(-1)
    
    def get_actual(row):
        if row['home_score'] == -1: return 'Pending'
        if row['home_score'] > row['away_score']: return 'Home Win'
        elif row['home_score'] < row['away_score']: return 'Away Win'
        else: return 'Draw'
        
    def get_pred(row):
        if pd.isna(row['prob_home_win']): return 'No Prediction'
        probs = {'Home Win': row['prob_home_win'], 'Draw': row['prob_draw'], 'Away Win': row['prob_away_win']}
        return max(probs, key=probs.get)

    eval_df['Actual Result'] = eval_df.apply(get_actual, axis=1)
    eval_df['Model Pick'] = eval_df.apply(get_pred, axis=1)
    eval_df['Correct?'] = eval_df.apply(lambda r: r['Actual Result'] == r['Model Pick'] if r['Actual Result'] != 'Pending' else None, axis=1)
    
    completed_matches = eval_df[eval_df['Actual Result'] != 'Pending']
    accuracy = completed_matches['Correct?'].mean() * 100 if not completed_matches.empty else 0.0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Matches Predicted", len(eval_df))
    col2.metric("Matches Completed & Scored", len(completed_matches))
    col3.metric("Model Accuracy", f"{accuracy:.1f}%")
    st.divider()

    PAGE_SIZE = 13
    total_matches = len(eval_df)
    total_pages = max(1, (total_matches + PAGE_SIZE - 1) // PAGE_SIZE)
    
    if 'eval_page' not in st.session_state:
        st.session_state.eval_page = 0
        
    col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
    with col_p1:
        if st.button("⬅️ Previous 13") and st.session_state.eval_page > 0:
            st.session_state.eval_page -= 1
            st.rerun()
    with col_p2:
        current_start = st.session_state.eval_page * PAGE_SIZE + 1
        current_end = min((st.session_state.eval_page + 1) * PAGE_SIZE, total_matches)
        st.markdown(f"<h5 style='text-align: center;'>Page {st.session_state.eval_page + 1} of {total_pages} (Matches {current_start} - {current_end})</h5>", unsafe_allow_html=True)
    with col_p3:
        if st.button("Next 13 ➡️") and st.session_state.eval_page < total_pages - 1:
            st.session_state.eval_page += 1
            st.rerun()

    start_idx = st.session_state.eval_page * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    paged_df = eval_df.iloc[start_idx:end_idx].copy()

    clean_df = paged_df.rename(columns={
        'date': 'Date', 'home_team': 'Home', 'away_team': 'Away', 
        'home_score': 'Home Goals', 'away_score': 'Away Goals'
    })
    
    clean_df['Date'] = clean_df['Date'].fillna('TBD')
    clean_df['Home Goals'] = clean_df['Home Goals'].replace(-1, '-')
    clean_df['Away Goals'] = clean_df['Away Goals'].replace(-1, '-')
    
    display_cols = ['Date', 'Home', 'Away', 'Home Goals', 'Away Goals', 'Actual Result', 'Model Pick', 'Correct?']
    clean_df = clean_df[display_cols]
    
    def highlight_correct(row):
        if row['Actual Result'] == 'Pending': return [''] * len(row)
        return ['background-color: #d4edda' if row['Correct?'] else 'background-color: #f8d7da'] * len(row)
        
    st.dataframe(clean_df.style.apply(highlight_correct, axis=1), use_container_width=True, hide_index=True)
    st.stop()

# --- Default Betting Mode ---
if not wc_games.empty:
    default_games = wc_games[['home_team', 'away_team', 'city']].copy()
    default_games.rename(columns={'home_team': 'Home', 'away_team': 'Away', 'city': 'Venue'}, inplace=True)
    default_games['Odds Home'] = 2.00
    default_games['Odds Draw'] = 3.00
    default_games['Odds Away'] = 2.00
else:
    default_games = pd.DataFrame(columns=["Home", "Away", "Venue", "Odds Home", "Odds Draw", "Odds Away"])

edited_df = st.data_editor(default_games, num_rows="dynamic")

if st.button("Calculate Edges"):
    for idx, row in edited_df.iterrows():
        home, away, venue = row.get('Home'), row.get('Away'), row.get('Venue')
        o_h, o_d, o_a = row.get('Odds Home'), row.get('Odds Draw'), row.get('Odds Away')
        
        if pd.isna(home) or pd.isna(away) or not str(home).strip() or not str(away).strip():
            continue
            
        st.markdown(f"### {home} vs {away} 📍 {venue}")
        
        match_data = df_predictions[
            (df_predictions['join_home'] == normalize_team(home)) & 
            (df_predictions['join_away'] == normalize_team(away))
        ]
        
        if match_data.empty:
            st.warning(f"No baseline predictions found in Gold Layer for {home} vs {away}.")
            continue
            
        match = match_data.iloc[0]
        ev_h, edge_h, kelly_h = calc_ev(match['prob_home_win'], o_h)
        ev_d, edge_d, kelly_d = calc_ev(match['prob_draw'], o_d)
        ev_a, edge_a, kelly_a = calc_ev(match['prob_away_win'], o_a)
        
        col1, col2, col3 = st.columns(3)
        col1.metric(f"Home Win ({match['prob_home_win']*100:.1f}%)", f"EV: {ev_h*100:+.1f}%", ev_flag(ev_h, edge_h))
        col2.metric(f"Draw ({match['prob_draw']*100:.1f}%)", f"EV: {ev_d*100:+.1f}%", ev_flag(ev_a, edge_a))
        col3.metric(f"Away Win ({match['prob_away_win']*100:.1f}%)", f"EV: {ev_a*100:+.1f}%", ev_flag(ev_a, edge_a))
        
        lam = match.get('dc_exp_home', 0) + match.get('dc_exp_away', 0)
        st.write(f"**Dixon-Coles λ:** {lam:.2f} | **ML Expected Goals:** {match.get('predicted_total_goals', 0):.2f}")
        st.divider()
