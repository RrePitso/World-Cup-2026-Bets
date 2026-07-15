import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
from src.agent.agent import get_agent_executor

st.set_page_config(page_title="Match Intel Agent", page_icon="🤖")
st.title("🤖 Match Intel Agent")
st.caption("Ask a natural-language question — the agent reasons over predictions, odds, and team news.")

# Resolve API key the same way gdrive_sync resolves credentials: secrets first, then env var
gemini_api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))

if not gemini_api_key:
    st.error("GEMINI_API_KEY not found. Add it to .streamlit/secrets.toml or as an environment variable.")
    st.stop()

if "agent_executor" not in st.session_state:
    st.session_state.agent_executor = get_agent_executor(gemini_api_key)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("e.g. Should I trust a value bet on Germany to beat Japan at 1.90 odds?")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Reasoning..."):
            try:
                result = st.session_state.agent_executor.invoke({"input": user_input})
                answer = result["output"]
            except Exception as e:
                answer = f"Error: {e}"
            st.markdown(answer)

    st.session_state.chat_history.append({"role": "assistant", "content": answer})
