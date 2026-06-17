import sys
import os
# Point Python to the root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from src.config import MODEL_DIR
from src.utils.gdrive_sync import sync_from_drive

st.set_page_config(page_title="World Cup Betting Engine", page_icon="⚽", layout="wide")

# Check if models exist locally; if not, pull from Google Drive
model_check_path = f"{MODEL_DIR}/rf_worldcup_model_v4.pkl"
if not os.path.exists(model_check_path):
    with st.spinner("Initializing engine and downloading models from Google Drive... This may take a minute."):
        try:
            sync_from_drive()
            st.toast("Models successfully synced from cloud storage!", icon="✅")
        except Exception as e:
            st.error(f"Failed to sync models: {e}. Check your GCP Service Account credentials.")

st.title("⚽ 2026 World Cup Betting Engine")
st.markdown("""
Welcome to the AI Betting Engine. 
Use the sidebar to navigate through:
- **Calendar:** View upcoming fixtures and historical match data.
- **Predictions:** Enter live Betway odds to calculate Expected Value (EV) and Kelly Criterion edges.
- **Model Status:** View the pipeline status and trigger retraining.
""")
