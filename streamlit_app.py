import streamlit as st
import statsapi
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Kalshi MLB Model", layout="wide")
st.title("Kalshi MLB Run Total Model")
st.caption("Version 1.6 - " + datetime.today().strftime('%B %d, %Y'))

BANKROLL = 500
EDGE_THRESHOLD = 0.05
KELLY_FRACTION = 0.5
MAX_BET_PCT = 0.05
LEAGUE_AVG_ERA = 4.20

TEAM_RUNS_2025 = {
    "New York Yankees": 4.8,
    "Los Angeles Dodgers": 5.1,
    "Atlanta Braves": 5.2,
    "Houston Astros": 4.6,
    "Philadelphia Phillies": 4.9,
    "Baltimore Orioles": 4.7,
    "Minnesota Twins": 4.5,
    "Texas Rangers": 4.4,
    "Seattle Mariners": 4.3,
    "Boston Red Sox": 4.6,
    "San Diego Padres": 4.4,
    "Cleveland Guardians": 4.3,
    "Milwaukee Brewers": 4.2,
    "Chicago Cubs": 4.4,
    "San Francisco Giants": 4.1,
    "Detroit Tigers": 4.2,
    "Kansas City Royals": 4.3,
    "Pittsburgh Pirates": 4.0,
    "Toronto Blue Jays": 4.5,
    "New York Mets": 4.6,
    "St. Louis Cardinals": 4.2,
    "Arizona Diamondbacks": 4.7,
    "Tampa Bay Rays": 4.3,
    "Cincinnati Reds": 4.4,
    "Washington Nationals": 3.9,
    "Colorado Rockies": 4.5,
    "Oakland Athletics": 3.8,
    "Athletics": 3.8,
    "Miami Marlins": 3.7,
    "Chicago White Sox": 3.6,
    "Los Angeles Angels": 3.9,
}

PITCHER_ERA_2025 = {
    "Chris Sale": 3.10,
    "Paul Skenes": 2.10,
    "Zack Wheeler": 3.00,
    "Gerrit Cole": 3.40,
    "Spencer Strider": 3.20,
    "Luis Castillo": 3.50,
    "Dylan Cease": 3.30,
    "Corbin Burnes": 3.20,
    "Max Fried": 3.10,
    "Shane Bieber": 3.60,
    "Kevin Gausman": 3.40,
    "Logan Webb": 3.20,
    "Sandy Alcantara": 3.50,
    "Freddy Peralta": 3.40,
    "Yu Darvish": 3.80,
    "Luis Severino": 4.20,
    "Andrew Abbott": 4.00,
    "Cade Cavalli": 4.50,
    "Trevor Rogers": 4.30,
    "Cristopher Sanchez": 4.10,
}

def get_team_rpg(team_name):
    for key in TEAM_RUNS_2025:
        if key.lower() in team_name.lower() or team_name.lower() in key.lower():
            return TEAM_RUNS_2025[key]
    return 4.2

def get_pitcher_era(pitcher_name):
    if not pitcher_name or pitcher_name == 'TBD':
        return LEAGUE_AVG_ERA
    for key in PITCHER_ERA_2025:
        if key.lower() in pitcher_name.lower() or pitcher_name.lower() in key.lower():
            return PITCHER_ERA_2025[key]
    return LEAGUE_AVG_ERA

def era_adjustment(pitcher_era):
    diff = pitcher_era - LEAGUE_AVG_ERA
    return round(diff * 0.5, 2)

def calc_kelly(edge):
    kelly = (edge / 1.0) * KELLY_FRACTION
    bet_pct = min(kelly, MAX_BET_PCT)
    bet_amt = round(BANKROLL * bet_pct, 2)
    return round(bet_pct * 100, 1), bet_amt

try:
    today = datetime.today().strftime('%Y-%m-%d')
    schedule = statsapi.schedule(date=today)

    if not schedule:
        st.warning("No games scheduled today.")
    else:
        for game in schedule:
            try:
                home = game['home_name']
                away = game['away_name']
                home_pitcher = game.get('home_probable_pitcher', 'TBD')
                away_pitcher = game.get('away_probable_pitcher', 'TBD')
                game_time = game['game_datetime']
                utc = datetime.strptime(game_time, '%Y-%m-%dT%H:%M:%SZ')
                et = utc - timedelta(hours=4)
                time_str = et.strftime('%I:%M %p ET')
                game_id = str(game['game_id'])

                with st.expander("**" + away + " @ " + home + "** - " + time_str):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Away:** " + away)
                        st.caption("SP: " + away_pitcher)
                    with col2:
                        st.markdown("**Home:** " + home)
                        st.caption("SP: " + home_pitcher)

                    away_rpg = get_team_rpg(away)
                    home_rpg = get_team_rpg(home)
                    base_total = round(away_rpg + home_rpg, 1)

                    away_era = get_pitcher_era(away_pitcher)
                    home_era = get_pitcher_era(home_pitcher)

                    away_adj = era_adjustment(away_era)
                    home_adj = era_adjustment(home_era)

                    model_total = round(base_total + away_adj + home_adj, 1)

                    st.markdown("---")
                    col3, col4, col5 = st.columns(3)
                    with col3:
                        st.metric("Base Total", base_total)
                    with col4:
                        st.metric("Away ERA", away_era)
                    with col5:
                        st.metric("Home ERA", home_era)

                    st.metric("Model Run Total Estimate", model_total)

                    kalshi_line = st.number_input("Enter Kalshi Line", min_value=0.0, max_value=20.0, value=8.5, step=0.5, key="line_" + game_id)
                    kalshi_over_price = st.number_input("Kalshi Over Price (cents)", min_value=1, max_value=99, value=50, step=1, key="price_" + game_id)
                    your_prob = st.slider("Your Over Probability %", 0, 100, 50, key="prob_" + game_id)

                    kalshi_implied = kalshi_over_price / 100
                    your_implied = your_prob / 100
                    edge = your_implied - kalshi_implied

                    if edge >= EDGE_THRESHOLD:
                        bet_pct, bet_amt = calc_kelly(edge)
                        st.success("BET OVER - Edge: " + str(round(edge*100,1)) + "% | Bet: $" + str(bet_amt))
                    elif edge <= -EDGE_THRESHOLD:
                        bet_pct, bet_amt = calc_kelly(abs(edge))
                        st.success("BET UNDER - Edge: " + str(round(abs(edge)*100,1)) + "% | Bet: $" + str(bet_amt))
                    else:
                        st.info("No edge. Current edge: " + str(round(edge*100,1)) + "%")

            except Exception as game_error:
                st.warning("Could not load game: " + str(game_error))
                continue

except Exception as e:
    st.error("Error: " + str(e))
