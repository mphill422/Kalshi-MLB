import streamlit as st
import statsapi
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Kalshi MLB Model", layout="wide")
st.title("Kalshi MLB Run Total Model")
st.caption("Version 1.8 - " + datetime.today().strftime('%B %d, %Y'))

BANKROLL = 500
EDGE_THRESHOLD = 0.05
KELLY_FRACTION = 0.5
MAX_BET_PCT = 0.05
LEAGUE_AVG_ERA = 4.20

TEAM_RUNS_2025 = {
    "New York Yankees": 4.8,
    "Los Angeles Dodgers": 5.1,
    "Atlanta Braves": 5.0,
    "Houston Astros": 4.6,
    "Philadelphia Phillies": 4.9,
    "Baltimore Orioles": 4.5,
    "Minnesota Twins": 4.5,
    "Texas Rangers": 4.4,
    "Seattle Mariners": 4.2,
    "Boston Red Sox": 4.7,
    "San Diego Padres": 4.4,
    "Cleveland Guardians": 4.3,
    "Milwaukee Brewers": 4.2,
    "Chicago Cubs": 4.4,
    "San Francisco Giants": 4.1,
    "Detroit Tigers": 4.3,
    "Kansas City Royals": 4.4,
    "Pittsburgh Pirates": 4.0,
    "Toronto Blue Jays": 4.8,
    "New York Mets": 4.6,
    "St. Louis Cardinals": 4.2,
    "Arizona Diamondbacks": 4.7,
    "Tampa Bay Rays": 4.2,
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
    "Paul Skenes": 1.96,
    "Yoshinobu Yamamoto": 2.49,
    "Chris Sale": 3.10,
    "Tarik Skubal": 2.94,
    "Nick Pivetta": 2.87,
    "Drew Rasmussen": 2.76,
    "Cristopher Sanchez": 2.95,
    "Logan Webb": 3.12,
    "Hunter Brown": 3.18,
    "Corbin Burnes": 3.22,
    "Max Fried": 3.25,
    "Zack Wheeler": 3.18,
    "Kevin Gausman": 3.45,
    "Tanner Bibee": 4.24,
    "Framber Valdez": 3.45,
    "Dylan Cease": 3.38,
    "Zac Gallen": 3.85,
    "Gavin Williams": 3.92,
    "Spencer Strider": 3.20,
    "Gerrit Cole": 3.40,
    "Shane Bieber": 3.60,
    "Sandy Alcantara": 3.50,
    "Freddy Peralta": 3.40,
    "Yu Darvish": 3.80,
    "Luis Severino": 4.10,
    "Andrew Abbott": 4.05,
    "Cade Cavalli": 4.55,
    "Trevor Rogers": 4.35,
    "Matthew Liberatore": 4.40,
    "Kyle Freeland": 4.65,
    "Nestor Cortes": 4.20,
    "Carlos Rodon": 4.50,
    "Sonny Gray": 3.80,
    "Luis Castillo": 3.50,
    "Braxton Garrett": 4.30,
    "Edward Cabrera": 4.45,
    "Patrick Corbin": 5.20,
    "Jake Irvin": 4.60,
    "Robbie Ray": 4.80,
    "Michael Soroka": 4.30,
    "Reese Olson": 4.15,
    "Jared Jones": 4.20,
    "Mitch Keller": 3.91,
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

def model_to_probability(model_total, kalshi_line):
    diff = model_total - kalshi_line
    prob = 50 + (diff * 8)
    prob = max(20, min(80, prob))
    return int(round(prob))

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

                    auto_prob = model_to_probability(model_total, kalshi_line)

                    if model_total > kalshi_line:
                        st.info("Model leans OVER — suggested probability: " + str(auto_prob) + "%")
                    elif model_total < kalshi_line:
                        st.info("Model leans UNDER — suggested probability: " + str(auto_prob) + "%")
                    else:
                        st.info("Model is neutral on this game.")

                    kalshi_over_price = st.number_input("Kalshi Over Price (cents)", min_value=1, max_value=99, value=50, step=1, key="price_" + game_id)
                    your_prob = st.slider("Your Over Probability %", 0, 100, auto_prob, key="prob_" + game_id)

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
