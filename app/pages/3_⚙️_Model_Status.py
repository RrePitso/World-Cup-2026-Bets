import streamlit as st
import os
from src.config import MODEL_DIR
import subprocess

st.set_page_config(page_title="Model Status", page_icon="⚙️")
st.title("⚙️ Pipeline Status")

model_path = f"{MODEL_DIR}/rf_worldcup_model_v4.pkl"

if os.path.exists(model_path):
    mod_time = os.path.getmtime(model_path)
    from datetime import datetime
    st.success(f"Models are active. Last local train: {datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')}")
else:
    st.warning("Models not found locally. Need to sync or retrain.")

if st.button("Force Local Retrain Now"):
    with st.spinner("Training models... Check terminal for output."):
        result = subprocess.run(["python", "src/models/train.py"], capture_output=True, text=True)
        st.code(result.stdout)
        if result.stderr:
            st.error(result.stderr)
