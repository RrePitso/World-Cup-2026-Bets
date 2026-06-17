import streamlit as st
import pandas as pd
from src.data.fetcher import fetch_venue_weather
from src.inference.predict import predict_match, predict_ml_goal_distribution, load_models
from src.models.dixon_coles import smart_goal_lines
from src.utils.betting import calc_ev, ev_flag

st.set_page_config(page_title="Predictions & EV", page_icon="🔮")
st.title("🔮 Edge Calculator & Predictions")

# Define default games for UI
default_games = pd.DataFrame([
    {"Home": "Germany", "Away": "Curaçao", "Venue": "Houston", "Odds Home": 1.15, "Odds Draw": 7.00, "Odds Away": 15.00},
    {"Home": "Austria", "Away": "Jordan", "Venue": "Philadelphia", "Odds Home": 1.90, "Odds Draw": 3.40, "Odds Away": 4.00}
])

edited_df = st.data_editor(default_games, num_rows="dynamic")

if st.button("Calculate Edges"):
    # Ensure models are loaded
    state = load_models()['state']
    
    for idx, row in edited_df.iterrows():
        home, away, venue = row['Home'], row['Away'], row['Venue']
        o_h, o_d, o_a = row['Odds Home'], row['Odds Draw'], row['Odds Away']
        
        st.markdown(f"### {home} vs {away} 📍 {venue}")
        
        try:
            weather = fetch_venue_weather(venue, '2026-06-14')
            probs = predict_match(home, away)
            ml_exp_goals, ml_dist = predict_ml_goal_distribution(home, away)
            
            mode, lam, exp_h, exp_a, lines = smart_goal_lines(home, away, weather, state)
            
            ev_h, edge_h, kelly_h = calc_ev(probs.get('home_win',0), o_h)
            ev_d, edge_d, kelly_d = calc_ev(probs.get('draw',0), o_d)
            ev_a, edge_a, kelly_a = calc_ev(probs.get('away_win',0), o_a)
            
            col1, col2, col3 = st.columns(3)
            col1.metric(f"Home Win ({probs.get('home_win',0)*100:.1f}%)", f"EV: {ev_h*100:+.1f}%", ev_flag(ev_h, edge_h))
            col2.metric(f"Draw ({probs.get('draw',0)*100:.1f}%)", f"EV: {ev_d*100:+.1f}%", ev_flag(ev_d, edge_d))
            col3.metric(f"Away Win ({probs.get('away_win',0)*100:.1f}%)", f"EV: {ev_a*100:+.1f}%", ev_flag(ev_a, edge_a))
            
            st.write(f"**Dixon-Coles λ:** {lam:.2f} | **ML Expected Goals:** {ml_exp_goals:.2f}")
            st.divider()
            
        except Exception as e:
            st.error(f"Error processing {home} vs {away}: {e}")
