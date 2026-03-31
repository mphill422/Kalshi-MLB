import streamlit as st
import statsapi
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Kalshi MLB Model", layout="wide")
st.title("⚾ Kalshi MLB Run Total Model")
st.caption(f"Version 1.0 — {datetime.today().strftime('%B %d, %Y')}")

st.subheader("Today's Games")

try:
    today = datetime.today().strftime('%Y-%m-%d')
    schedule = statsapi.schedule(date=today)
    
    if not schedule:
        st.warning("No games scheduled today.")
    else:
        for game in schedule:
            home = game['home_name']
            away = game['away_name']
            time = game['game_datetime']
            st.markdown(f"**{away} @ {home}** — {time}")
            
except Exception as e:
    st.error(f"Error loading schedule: {e}")
