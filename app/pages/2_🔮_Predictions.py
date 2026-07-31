import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import pandas as pd
import pyodbc
from src.utils.betting import calc_ev, ev_flag

st.set_page_config(page_title="Predictions & EV", page_icon="🔮")
st.title("🔮 Edge Calculator & Predictions")

# --- 1. Database Connection to Fabric ---
@st.cache_resource
def init_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={st.secrets['fabric']['server']};"
        f"DATABASE={st.secrets['fabric']['database']};"
        f"UID={st.secrets['fabric']['username']};"
        f"PWD={st.secrets['fabric']['password']};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        "Authentication=ActiveDirectoryPassword;"
    )

@st.cache_data(ttl=3600)
def get_gold_predictions():
    conn = init_connection()
    query = "SELECT * FROM gold_match_predictions"
    return pd.read_sql(query, conn)

# --- 2. Fetch Gold Data ---
try:
    with st.spinner("Fetching predictions from Microsoft Fabric Gold Layer..."):
        df_predictions = get_gold_predictions()
    st.success("✅ Connected to Fabric Lakehouse!")
except Exception as e:
    st.error(f"Failed to connect to Microsoft Fabric: {e}")
    st.stop()

# --- 3. UI Odds & EV Calculation ---
default_games = pd.DataFrame([
    {"Home": "Germany", "Away": "Curaçao", "Venue": "Houston", "Odds Home": 1.15, "Odds Draw": 7.00, "Odds Away": 15.00},
    {"Home": "Austria", "Away": "Jordan", "Venue": "Philadelphia", "Odds Home": 1.90, "Odds Draw": 3.40, "Odds Away": 4.00}
])

edited_df = st.data_editor(default_games, num_rows="dynamic")

if st.button("Calculate Edges"):
    for idx, row in edited_df.iterrows():
        home, away, venue = row['Home'], row['Away'], row['Venue']
        o_h, o_d, o_a = row['Odds Home'], row['Odds Draw'], row['Odds Away']
        
        st.markdown(f"### {home} vs {away} 📍 {venue}")
        
        # Look up match in Gold Delta Table
        match_data = df_predictions[
            (df_predictions['home_team'].str.lower() == home.lower()) & 
            (df_predictions['away_team'].str.lower() == away.lower())
        ]
        
        if match_data.empty:
            st.warning(f"No Gold layer predictions found for {home} vs {away}.")
            continue
            
        match = match_data.iloc[0]
        
        # Calculate EV using stored probabilities
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
