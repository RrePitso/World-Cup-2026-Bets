import streamlit as st

st.set_page_config(page_title="World Cup Betting Engine", page_icon="⚽", layout="wide")

st.title("⚽ 2026 World Cup Betting Engine")
st.markdown("""
Welcome to the AI Betting Engine. 
Use the sidebar to navigate through:
- **Calendar:** View upcoming fixtures and historical match data.
- **Predictions:** Enter live Betway odds to calculate Expected Value (EV) and Kelly Criterion edges.
- **Model Status:** View the pipeline status and trigger retraining.
""")
