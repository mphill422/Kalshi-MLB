import streamlit as st
import statsapi
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Kalshi MLB Model", layout="wide")
st.title("Kalshi MLB Run Total Model")
st.caption("Version 1.4 - " + datetime.today().strftime('%B %d, %Y'))

BANKROLL = 500
EDGE_THRESHOLD = 0.05
KELLY_FRACTION = 0.5
MAX_BET_PCT = 0.05
LEAGUE_AVG_ERA = 4.20

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

def get_pitcher_era(pitcher_name):
    try:
        if not pitcher_name or pitcher_name == 'TBD':
            return LEAGUE_AVG_ERA
        results = statsapi.lookup_player(pitcher_name)
        if not results:
            return LEAGUE_AVG_ERA
        pid = results[0]['id']
        stats = statsapi.player_stat_data(pid, group='pitching', type='season')
        for s in stats['stats']:
            for split in s.get('splits', []):
                era = split['stat'].get('era', None)
                if era:
                    return float(era)
    except:
        pass
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
            game_id = str(game['game_id'])

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
                base_total = away_rpg + home_rpg

                away_era = get_pitcher_era(away_pitcher)
                home_era = get_pitcher_era(home_pitcher)

                away_adj = era_adjustment(away_era)
                home_adj = era_adjustment(home_era)

                model_total = round(base_total + away_adj + home_adj, 1)

                st.markdown("---")
                col3, col4, col5 = st.columns(3)
                with col3:
                    st.metric("Base Run Total", round(base_total, 1))
                with col4:
                    era_label = away_pitcher.split()[-1] + " ERA: " + str(away_era) if away_pitcher != 'TBD' else "Away ERA"
                    st.metric(era_label, away_era)
                with col5:
                    era_label2 = home_pitcher.split()[-1] + " ERA: " + str(home_era) if home_pitcher != 'TBD' else "Home ERA"
                    st.metric(era_label2, home_era)

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

except Exception as e:
    st.error("Error: " + str(e))
