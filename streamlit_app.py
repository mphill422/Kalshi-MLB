import streamlit as st
import statsapi
import pandas as pd
from datetime import datetime
import pytz

st.set_page_config(page_title="Kalshi MLB Model", layout="wide")
st.title("Kalshi MLB Run Total Model")
st.caption("Version 1.1 - " + datetime.today().strftime('%B %d, %Y'))

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
            home_pitcher = game.get('home_probable_pitcher', 'TBD')
            away_pitcher = game.get('away_probable_pitcher', 'TBD')
            game_time = game['game_datetime']
            utc = datetime.strptime(game_time, '%Y-%m-%dT%H:%M:%SZ')
            utc = utc.replace(tzinfo=pytz.utc)
            et = utc.astimezone(pytz.timezone('US/Eastern'))
            time_str = et.strftime('%I:%M %p ET')
            st.markdown("**" + away + " @ " + home + "** - " + time_str)
            st.caption("Away SP: " + away_pitcher + " | Home SP: " + home_pitcher)
            st.divider()

except Exception as e:
    st.error("Error loading schedule: " + str(e))
