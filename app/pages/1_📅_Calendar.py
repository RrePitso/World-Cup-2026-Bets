import sys
import os
# Point Python to the root directory (up two levels from /pages)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import pandas as pd
from src.data.fetcher import load_international_results

st.set_page_config(page_title="Calendar", page_icon="📅")
st.title("📅 Match Calendar")

@st.cache_data(ttl=3600)
def get_data():
    return load_international_results()

df = get_data()

upcoming = df[df['home_score'].isna()].copy()
past = df.dropna(subset=['home_score']).copy()

st.subheader("Upcoming Matches (Scores = NaN)")
st.dataframe(upcoming.tail(50))

st.subheader("Recently Concluded Matches")
st.dataframe(past.tail(50).sort_values('date', ascending=False))
