import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import pandas as pd
import pyodbc
import itertools
from src.data.fetcher import load_international_results

st.set_page_config(page_title="Tournament Simulator", page_icon="🏆", layout="wide")
st.title("🏆 Monte Carlo Bracket Simulator")

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

@st.cache_data(ttl=3600)
def get_calendar_data():
    try:
        url = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
        df = pd.read_csv(url)
        df['date'] = pd.to_datetime(df['date'])
        df_wc = df[df['tournament'] == 'FIFA World Cup'].copy()
        df_wc = df_wc[df_wc['date'].dt.year == 2026].sort_values('date')
        return df_wc.reset_index(drop=True)
    except Exception as e:
        return pd.DataFrame()

try:
    df_predictions = get_gold_predictions()
    st.success("✅ Connected to Fabric Lakehouse")
except Exception as e:
    st.error(f"Failed to connect to Microsoft Fabric: {e}")
    st.stop()

wc_games = get_calendar_data()
if wc_games.empty:
    st.warning("⚠️ Could not load official calendar fixtures. Reality checks will be disabled.")

# --- OFFICIAL 2026 GROUPS ---
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

# --- REALITY CHECK HELPER ---
def get_actual_result_string(t1, t2, df_cal):
    if df_cal.empty:
        return "Reality: Data unavailable"
    
    t1_clean = normalize_team(t1)
    t2_clean = normalize_team(t2)
    
    match = df_cal[
        ((df_cal['home_team'].apply(normalize_team) == t1_clean) & (df_cal['away_team'].apply(normalize_team) == t2_clean)) |
        ((df_cal['home_team'].apply(normalize_team) == t2_clean) & (df_cal['away_team'].apply(normalize_team) == t1_clean))
    ]
    
    if not match.empty:
        m = match.iloc[0]
        if pd.notna(m.get('home_score')):
            return f"**Reality:** {m['home_team']} **{int(m['home_score'])} - {int(m['away_score'])}** {m['away_team']}"
        else:
            return "**Reality:** Match Pending"
    return "Reality: *Teams did not play each other*"

if st.button("Simulate Tournament"):
    group_standings = []

    # --- SIMULATE GROUPS (WITH BIDIRECTIONAL LOOKUP FIX) ---
    for group, teams in MOCK_GROUPS.items():
        points = {team: 0 for team in teams}
        
        for home, away in itertools.combinations(teams, 2):
            h_clean = str(home).strip().lower()
            a_clean = str(away).strip().lower()
            
            match_data = df_predictions[
                ((df_predictions['home_team'].str.strip().str.lower() == h_clean) & 
                 (df_predictions['away_team'].str.strip().str.lower() == a_clean)) |
                ((df_predictions['home_team'].str.strip().str.lower() == a_clean) & 
                 (df_predictions['away_team'].str.strip().str.lower() == h_clean))
            ]
            
            if not match_data.empty:
                m = match_data.iloc[0]
                db_home = str(m['home_team']).strip().lower()
                
                # Dynamically swap probabilities if the database order is reversed
                if db_home == h_clean:
                    p_home = m['prob_home_win']
                    p_away = m['prob_away_win']
                else:
                    p_home = m['prob_away_win']
                    p_away = m['prob_home_win']
                    
                probs = {'home': p_home, 'draw': m['prob_draw'], 'away': p_away}
                outcome = max(probs, key=probs.get)
                
                if outcome == 'home': points[home] += 3
                elif outcome == 'away': points[away] += 3
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
    
    # --- KNOCKOUT BRACKET ENGINE (WITH BIDIRECTIONAL LOOKUP FIX) ---
    if len(qualified) == 32:
        st.subheader("3. Knockout Bracket Simulation")
        
        seeded_teams = qualified.sort_values(by='Points', ascending=False)['Team'].tolist()
        
        current_matchups = []
        for i in range(16):
            current_matchups.append((seeded_teams[i], seeded_teams[31-i]))
            
        def simulate_knockout_match(home, away):
            h_clean = str(home).strip().lower()
            a_clean = str(away).strip().lower()
            
            match_data = df_predictions[
                ((df_predictions['home_team'].str.strip().str.lower() == h_clean) & 
                 (df_predictions['away_team'].str.strip().str.lower() == a_clean)) |
                ((df_predictions['home_team'].str.strip().str.lower() == a_clean) & 
                 (df_predictions['away_team'].str.strip().str.lower() == h_clean))
            ]
            
            if not match_data.empty:
                m = match_data.iloc[0]
                db_home = str(m['home_team']).strip().lower()
                
                # Dynamically swap probabilities if the database order is reversed
                if db_home == h_clean:
                    p_home = m['prob_home_win']
                    p_away = m['prob_away_win']
                else:
                    p_home = m['prob_away_win']
                    p_away = m['prob_home_win']
                    
                if p_home > p_away: return home
                else: return away
                
            return home
            
        def play_round(matchups, round_name):
            st.markdown(f"#### {round_name}")
            winners = []
            
            col1, col2 = st.columns(2)
            for idx, (t1, t2) in enumerate(matchups):
                winner = simulate_knockout_match(t1, t2)
                winners.append(winner)
                
                reality_str = get_actual_result_string(t1, t2, wc_games)
                
                display_col = col1 if idx % 2 == 0 else col2
                display_col.info(f"**{t1}** vs **{t2}**  \n🏆 **{winner}** advances  \n\n*( {reality_str} )*")
                
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
        final_t1, final_t2 = final[0][0], final[0][1]
        champion = simulate_knockout_match(final_t1, final_t2)
        
        reality_final = get_actual_result_string(final_t1, final_t2, wc_games)
        
        st.success(f"## {final_t1} vs {final_t2}  \n# 🏆 WORLD CHAMPION: {champion}  \n\n*( {reality_final} )*")
    else:
        st.warning(f"Waiting for full 48-team group configuration. Currently have {len(qualified)} qualified teams.")
