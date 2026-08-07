import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import streamlit as st
import pandas as pd
import pyodbc

st.set_page_config(page_title="Tournament Simulator", page_icon="🏆", layout="wide")
st.title("🏆 Monte Carlo Bracket Simulator")

# --- Database Connection ---
@st.cache_resource
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
    return pd.read_sql("SELECT * FROM dbo.gold_match_predictions", conn)

try:
    df_predictions = get_gold_predictions()
    st.success("✅ Connected to Fabric Lakehouse")
except Exception as e:
    st.error(f"Failed to connect to Microsoft Fabric: {e}")
    st.stop()

st.subheader("1. Group Stage Engine")

if st.button("Simulate Group Stage"):
    # This is where we will build the point calculator
    # 1. Map all 48 teams into their 12 Groups (A-L)
    # 2. Iterate through every group match in df_predictions
    # 3. Add 3 points for prob_win > others, 1 point for draw
    # 4. Resolve tiebreakers using the Dixon-Coles expected goals
    
    st.info("Simulation engine initialized. Next step: Writing the grouping logic!")
    
    # Placeholder for the data structure we need to feed the bracket
    knockout_teams = {
        "Round_of_32": [] # Will hold the 32 qualified teams based on points
    }
    st.write(knockout_teams)
