import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Calendar", page_icon="📅", layout="wide")
st.title("📅 Match Calendar")

@st.cache_data(ttl=3600)
def get_calendar_data():
    url = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
    df = pd.read_csv(url)
    df['date'] = pd.to_datetime(df['date'])
    
    # Filter exclusively for 2026 FIFA World Cup matches
    df_wc = df[df['tournament'] == 'FIFA World Cup'].copy()
    df_wc = df_wc[df_wc['date'].dt.year == 2026].sort_values('date')
    return df_wc.reset_index(drop=True)

try:
    df = get_calendar_data()
    
    if df.empty:
        st.info("No 2026 World Cup matches found.")
    else:
        display_cols = ['date', 'home_team', 'home_score', '-', 'away_score', 'away_team', 'city']
        df['-'] = 'vs'
        df_display = df[display_cols]

        # Split into past (has scores) and upcoming (NaN scores)
        past = df_display.dropna(subset=['home_score']).copy()
        upcoming = df_display[df_display['home_score'].isna()].copy()

        st.subheader("Last 5 Concluded Matches")
        st.dataframe(past.tail(5).sort_values('date', ascending=False), use_container_width=True, hide_index=True)

        st.subheader("Next 5 Upcoming Matches")
        st.dataframe(upcoming.head(5), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Failed to load data: {e}")
