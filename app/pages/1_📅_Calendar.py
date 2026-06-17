import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Calendar", page_icon="📅", layout="wide")
st.title("📅 Match Calendar")

@st.cache_data(ttl=3600)
def get_worldcup_schedule():
    # Pull directly from the requested jfjelstul dataset
    url = "https://raw.githubusercontent.com/jfjelstul/worldcup/master/data-csv/matches.csv"
    df_wc = pd.read_csv(url)
    
    # Filter strictly for 2026 matches
    df_wc['match_date'] = pd.to_datetime(df_wc['match_date'])
    df_2026 = df_wc[df_wc['match_date'].dt.year == 2026].copy()
    
    # Sort sequentially
    df_2026 = df_2026.sort_values('match_date').reset_index(drop=True)
    return df_2026

try:
    df = get_worldcup_schedule()
    
    if df.empty:
        st.info("Waiting for the upstream jfjelstul repository to push 2026 matches.")
    else:
        # Columns to display nicely
        display_cols = ['match_date', 'stage_name', 'home_team_name', 'home_team_score', '-', 'away_team_score', 'away_team_name', 'score']
        
        # Insert a dummy column for visual separation in the dataframe
        df['-'] = 'vs'
        df_display = df[display_cols]

        upcoming = df_display[df_display['home_team_score'].isna()].copy()
        past = df_display.dropna(subset=['home_team_score']).copy()

        st.subheader("Upcoming Matches (Scores = NaN)")
        st.dataframe(upcoming, use_container_width=True, hide_index=True)

        st.subheader("Recently Concluded Matches")
        st.dataframe(past.sort_values('match_date', ascending=False), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Failed to load data from repository: {e}")
