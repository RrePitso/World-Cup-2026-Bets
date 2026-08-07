import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import pandas as pd
import pyodbc
import itertools

st.set_page_config(page_title="Tournament Simulator", page_icon="🏆", layout="wide")
st.title("🏆 Monte Carlo Bracket Simulator")

# --- Database Connection ---
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
# Expand this dictionary to include all 48 teams
# --- MOCK 2026 GROUPS (48 Teams, 12 Groups of 4) ---
MOCK_GROUPS = {
    'A': ['Mexico', 'South Africa', 'South Korea', 'Czech Republic'],
    'B': ['Switzerland', 'Canada', 'Bosnia and Herzegovina', 'Qatar'],
    'C': ['Brazil', 'Morocco', 'Scotland', 'Haiti'],
    'D': ['United States', 'Australia', 'Paraguay', 'Türkiye'],
    'E': ['Germany', 'Ivory Coast', 'Ecuador', 'Curaçao'],
    'F': ['Netherlands', 'Japan', 'Sweden', 'Tunisia'],
    'G': ['Belgium', 'Egypt', 'Iran', 'New Zealand'],
    'H': ['Spain', 'Cabo Verde', 'Uruguay', 'Saudi Arabia'],
    'I': ['France', 'Norway', 'Senegal', 'Iraq'],
    'J': ['Argentina', 'Austria', 'Algeria', 'Jordan'],
    'K': ['Colombia', 'Portugal', 'DR Congo', 'Uzbekistan'],
    'L': ['England', 'Croatia', 'Ghana', 'Panama']
}

st.subheader("1. Group Stage Standings")

if st.button("Simulate Tournament"):
    group_standings = []

    # --- SIMULATE GROUPS ---
    for group, teams in MOCK_GROUPS.items():
        points = {team: 0 for team in teams}
        
        for home, away in itertools.combinations(teams, 2):
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

    # --- EXTRACT QUALIFIERS ---
    st.subheader("2. Knockout Stage Qualifiers")
    
    top_2 = df_standings[df_standings['Rank'] <= 2]
    third_place = df_standings[df_standings['Rank'] == 3].sort_values(by='Points', ascending=False).head(8)
    
    qualified = pd.concat([top_2, third_place])
    st.write(f"**Total Qualified Teams:** {len(qualified)} (Top 2 from each group + 8 best 3rd-place teams)")
    
    # --- KNOCKOUT BRACKET ENGINE ---
    if len(qualified) == 32:
        st.subheader("3. Knockout Bracket Simulation")
        
        # Seed teams 1 through 32 based on group stage points
        seeded_teams = qualified.sort_values(by='Points', ascending=False)['Team'].tolist()
        
        # Build initial Round of 32 matchups (Seed 1 vs 32, Seed 2 vs 31...)
        current_matchups = []
        for i in range(16):
            current_matchups.append((seeded_teams[i], seeded_teams[31-i]))
            
        def simulate_knockout_match(home, away):
            match_data = df_predictions[
                (df_predictions['home_team'].str.strip().str.lower() == str(home).strip().lower()) & 
                (df_predictions['away_team'].str.strip().str.lower() == str(away).strip().lower())
            ]
            if not match_data.empty:
                m = match_data.iloc[0]
                # In knockouts, draws are resolved by extra time/penalties. 
                # We force a winner by strictly comparing home vs away win probabilities.
                if m['prob_home_win'] > m['prob_away_win']:
                    return home
                else:
                    return away
            return home # Fallback if prediction is missing
            
        def play_round(matchups, round_name):
            st.markdown(f"#### {round_name}")
            winners = []
            
            # Use columns to create a clean, split visual layout
            col1, col2 = st.columns(2)
            for idx, (t1, t2) in enumerate(matchups):
                winner = simulate_knockout_match(t1, t2)
                winners.append(winner)
                
                display_col = col1 if idx % 2 == 0 else col2
                display_col.info(f"**{t1}** vs **{t2}**  \n🏆 **{winner}** advances")
                
            # Pair the winners up for the next round
            next_matchups = [(winners[i], winners[i+1]) for i in range(0, len(winners), 2)]
            return next_matchups
            
        r16 = play_round(current_matchups, "Round of 32")
        st.divider()
        qf = play_round(r16, "Round of 16")
        st.divider()
        sf = play_round(qf, "Quarterfinals")
        st.divider()
        final = play_round(sf, "Semifinals")
        st.divider()
        
        st.markdown("### 🌍 World Cup Final")
        champion = simulate_knockout_match(final[0][0], final[0][1])
        st.success(f"## {final[0][0]} vs {final[0][1]}  \n# 🏆 WORLD CHAMPION: {champion}")
    else:
        st.warning(f"Waiting for full 48-team group configuration. Currently have {len(qualified)} qualified teams.")
