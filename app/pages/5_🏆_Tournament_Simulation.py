import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import pandas as pd
import pyodbc
import itertools

st.set_page_config(page_title="Tournament Simulator", page_icon="🏆", layout="wide")
st.title("🏆 Monte Carlo Bracket Simulator")

# Removed @st.cache_resource here as well
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
    df = pd.read_sql("SELECT * FROM dbo.gold_match_predictions", conn)
    conn.close()
    return df

try:
    df_predictions = get_gold_predictions()
    st.success("✅ Connected to Fabric Lakehouse")
except Exception as e:
    st.error(f"Failed to connect to Microsoft Fabric: {e}")
    st.stop()

# --- MOCK 2026 GROUPS (48 Teams, 12 Groups of 4) ---
MOCK_GROUPS = {
    'A': ['Mexico', 'South Africa', 'Germany', 'Curaçao'],
    'B': ['Canada', 'Bosnia and Herzegovina', 'Austria', 'Jordan'],
    'C': ['United States', 'Paraguay', 'Spain', 'Scotland'],
    'D': ['Mali', 'Gambia', 'Ivory Coast', 'Comoros'],
    # You can populate the remaining 8 groups (E through L) here
}

st.subheader("1. Group Stage Engine (Point Calculation)")

if st.button("Simulate Group Stage"):
    group_standings = []

    for group, teams in MOCK_GROUPS.items():
        points = {team: 0 for team in teams}
        
        for home, away in itertools.combinations(teams, 2):
            # Reverted to your strict string matching logic here as well
            match_data = df_predictions[
                (df_predictions['home_team'].str.strip().str.lower() == str(home).strip().lower()) & 
                (df_predictions['away_team'].str.strip().str.lower() == str(away).strip().lower())
            ]
            
            if not match_data.empty:
                match = match_data.iloc[0]
                probs = {'home': match['prob_home_win'], 'draw': match['prob_draw'], 'away': match['prob_away_win']}
                outcome = max(probs, key=probs.get)
                
                if outcome == 'home':
                    points[home] += 3
                elif outcome == 'away':
                    points[away] += 3
                else:
                    points[home] += 1
                    points[away] += 1
        
        sorted_group = sorted(points.items(), key=lambda x: x[1], reverse=True)
        for rank, (team, pts) in enumerate(sorted_group):
            group_standings.append({"Group": group, "Rank": rank + 1, "Team": team, "Points": pts})

    df_standings = pd.DataFrame(group_standings)
    st.dataframe(df_standings, use_container_width=True)

    st.info("The engine has calculated group stage points! Next step: Extract the Top 2 from each group + the 8 best 3rd-place teams to build the Round of 32 bracket.")
