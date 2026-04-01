import streamlit as st
import statsapi
import pandas as pd
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="Kalshi MLB Model", layout="wide")
st.title("Kalshi MLB Run Total Model")
st.caption("Version 1.2 - " + datetime.today().strftime('%B %d, %Y'))

BANKROLL = 500
EDGE_THRESHOLD = 0.05
KELLY_FRACTION = 0.5
MAX_BET_PCT = 0.05

def get_pitcher_era(pitcher_name):
    try:
        results = statsapi.lookup_player(pitcher_name)
        if not results:
            return None
        pid = results[0]['id']
        stats = statsapi.player_stat_data(pid, group='pitching', type='season')
        for s in stats['stats']:
            for split in s.get('splits', []):
                era = split['stat'].get('era', None)
                whip = split['stat'].get('whip', None)
                if era:
                    return float(era), float(whip) if whip else 1.30
    except:
        return None
    return None

def get_team_runs_per_game(team_id):
    try:
        stats = statsapi.team_stats(team_id, group='hitting', type='season')
        runs = None
        games = None
        for line in stats.split('\n'):
            if 'runs' in line.lower():
                parts = line.split()
                for p in parts:
                    try:
                        runs = float(p)
                        break
                    except:
                        pass
            if 'gamesplayed' in line.lower() or 'games played' in line.lower():
                parts = line.split()
                for p in parts:
                    try:
                        games = float(p)
                        break
                    except:
                        pass
        if runs and games and games > 0:
            return round(runs / games, 2)
    except:
        pass
    return 4.5

def calc_kelly(edge, odds=1.0):
    kelly = (edge / odds) * KELLY_FRACTION
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
            home = game['home_name']
            away = game['away_name']
            home_id = game['home_id']
            away_id = game['away_id']
            home_pitcher = game.get('home_probable_pitcher', 'TBD')
            away_pitcher = game.get('away_probable_pitcher', 'TBD')
            game_time = game['game_datetime']
            utc = datetime.strptime(game_time, '%Y-%m-%dT%H:%M:%SZ')
            et = utc - timedelta(hours=4)
            time_str = et.strftime('%I:%M %p ET')

            with st.expander("**" + away + " @ " + home + "** - " + time_str):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Away:** " + away)
                    st.caption("SP: " + away_pitcher)
                with col2:
                    st.markdown("**Home:** " + home)
                    st.caption("SP: " + home_pitcher)

                away_rpg = get_team_runs_per_game(away_id)
                home_rpg = get_team_runs_per_game(home_id)
                model_total = round(away_rpg + home_rpg, 1)

                st.markdown("---")
                st.metric("Model Run Total Estimate", model_total)

                kalshi_line = st.number_input(
                    "Enter Kalshi Line",
                    min_value=0.0,
                    max_value=20.0,
                    value=8.5,
                    step=0.5,
                    key="line_" + str(game['game_id'])
                )

                over_prob = st.slider(
                    "Your Over Probability %",
                    0, 100, 50,
                    key="prob_" + str(game['game_id'])
                )

                kalshi_implied = over_prob / 100
                edge = kalshi_implied - 0.50

                if abs(edge) >= EDGE_THRESHOLD:
                    direction = "OVER" if edge > 0 else "UNDER"
                    bet_pct, bet_amt = calc_kelly(abs(edge))
                    st.success(direction + " — Edge: " + str(round(abs(edge)*100,1)) + "% | Bet: $" + str(bet_amt))
                else:
                    st.info("No edge detected on this game.")

except Exception as e:
    st.error("Error: " + str(e))
