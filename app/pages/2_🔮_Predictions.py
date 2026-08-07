import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import pandas as pd
import pyodbc
from src.utils.betting import calc_ev, ev_flag

st.set_page_config(page_title="Predictions & EV", page_icon="🔮", layout="wide")
st.title("🔮 Edge Calculator & Predictions")

# --- 1. Database Connection to Fabric ---
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
            home_team, 
            away_team, 
            prob_home_win, 
            prob_draw, 
            prob_away_win, 
            dc_exp_home, 
            dc_exp_away, 
            predicted_total_goals
        FROM dbo.gold_match_predictions
    """
    return pd.read_sql(query, conn)

# --- 2. Fetch Gold Data ---
try:
    with st.spinner("Fetching pre-tournament predictions from Microsoft Fabric Gold Layer..."):
        df_predictions = get_gold_predictions()
    st.success("✅ Connected to Fabric Lakehouse (Pre-Tournament Data Freeze Active)")
except Exception as e:
    st.error(f"Failed to connect to Microsoft Fabric: {e}")
    st.stop()

# --- 3. UI Odds & EV Calculation ---
# Dynamically populate the table using the Fabric dataset instead of hardcoded default games
if not df_predictions.empty:
    default_games = df_predictions[['home_team', 'away_team']].copy()
    default_games.rename(columns={'home_team': 'Home', 'away_team': 'Away'}, inplace=True)
    default_games['Venue'] = "TBD" # Placeholder for user to edit
    default_games['Odds Home'] = 2.00 # Placeholder baseline odds
    default_games['Odds Draw'] = 3.00
    default_games['Odds Away'] = 2.00
else:
    default_games = pd.DataFrame(columns=["Home", "Away", "Venue", "Odds Home", "Odds Draw", "Odds Away"])

edited_df = st.data_editor(default_games, num_rows="dynamic")

if st.button("Calculate Edges"):
    for idx, row in edited_df.iterrows():
        home, away, venue = row.get('Home'), row.get('Away'), row.get('Venue')
        o_h, o_d, o_a = row.get('Odds Home'), row.get('Odds Draw'), row.get('Odds Away')
        
        # ERROR FIX: Skip empty rows to prevent the NoneType 'strip' error
        if pd.isna(home) or pd.isna(away) or not str(home).strip() or not str(away).strip():
            continue
            
        st.markdown(f"### {home} vs {away} 📍 {venue}")
        
        # Look up match using strict case-insensitive team matching
        match_data = df_predictions[
            (df_predictions['home_team'].str.strip().str.lower() == str(home).strip().lower()) & 
            (df_predictions['away_team'].str.strip().str.lower() == str(away).strip().lower())
        ]
        
        if match_data.empty:
            st.warning(f"No baseline predictions found in Gold Layer for {home} vs {away}.")
            continue
            
        match = match_data.iloc[0]
        
        # Calculate EV using pure pre-match probabilities
        ev_h, edge_h, kelly_h = calc_ev(match['prob_home_win'], o_h)
        ev_d, edge_d, kelly_d = calc_ev(match['prob_draw'], o_d)
        ev_a, edge_a, kelly_a = calc_ev(match['prob_away_win'], o_a)
        
        col1, col2, col3 = st.columns(3)
        col1.metric(f"Home Win ({match['prob_home_win']*100:.1f}%)", f"EV: {ev_h*100:+.1f}%", ev_flag(ev_h, edge_h))
        col2.metric(f"Draw ({match['prob_draw']*100:.1f}%)", f"EV: {ev_d*100:+.1f}%", ev_flag(ev_d, edge_d))
        col3.metric(f"Away Win ({match['prob_away_win']*100:.1f}%)", f"EV: {ev_a*100:+.1f}%", ev_flag(ev_a, edge_a))
        
        lam = match.get('dc_exp_home', 0) + match.get('dc_exp_away', 0)
        st.write(f"**Dixon-Coles λ:** {lam:.2f} | **ML Expected Goals:** {match.get('predicted_total_goals', 0):.2f}")
        st.divider()
