import streamlit as st
import statsapi
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client

st.set_page_config(page_title="Kalshi MLB Model", layout="wide")
st.title("Kalshi MLB Run Total Model")
st.caption("Version 2.3 - " + datetime.today().strftime('%B %d, %Y'))

BANKROLL = 500
EDGE_THRESHOLD = 0.05
KELLY_FRACTION = 0.5
MAX_BET_PCT = 0.05
LEAGUE_AVG_ERA = 4.20

try:
    supabase = create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"]
    )
    supabase_connected = True
except:
    supabase_connected = False

TEAM_RUNS_2025 = {
    # AL East
    "New York Yankees": 4.7,
    "Boston Red Sox": 4.7,
    "Toronto Blue Jays": 4.8,
    "Baltimore Orioles": 4.5,
    "Tampa Bay Rays": 4.1,
    # AL Central
    "Cleveland Guardians": 4.3,
    "Minnesota Twins": 4.5,
    "Detroit Tigers": 4.4,
    "Kansas City Royals": 4.3,
    "Chicago White Sox": 3.6,
    # AL West
    "Houston Astros": 4.6,
    "Seattle Mariners": 4.2,
    "Texas Rangers": 4.4,
    "Los Angeles Angels": 3.9,
    "Oakland Athletics": 3.7,
    "Athletics": 3.7,
    # NL East
    "New York Mets": 4.7,
    "Philadelphia Phillies": 4.9,
    "Atlanta Braves": 5.0,
    "Washington Nationals": 4.1,
    "Miami Marlins": 3.8,
    # NL Central
    "Chicago Cubs": 4.4,
    "Milwaukee Brewers": 4.3,
    "St. Louis Cardinals": 4.2,
    "Pittsburgh Pirates": 4.0,
    "Cincinnati Reds": 4.4,
    # NL West
    "Los Angeles Dodgers": 5.1,
    "San Diego Padres": 4.4,
    "Arizona Diamondbacks": 4.7,
    "San Francisco Giants": 4.1,
    "Colorado Rockies": 4.5,
}

# Park run factors: 1.0 = neutral, >1.0 = hitter friendly, <1.0 = pitcher friendly
PARK_FACTORS = {
    "Colorado Rockies":        1.15,
    "Cincinnati Reds":         1.07,
    "Texas Rangers":           1.06,
    "Boston Red Sox":          1.05,
    "Chicago Cubs":            1.04,
    "Philadelphia Phillies":   1.04,
    "Baltimore Orioles":       1.03,
    "Atlanta Braves":          1.02,
    "Kansas City Royals":      1.02,
    "Toronto Blue Jays":       1.01,
    "Houston Astros":          1.01,
    "Detroit Tigers":          1.00,
    "Minnesota Twins":         1.00,
    "New York Yankees":        1.00,
    "Chicago White Sox":       1.00,
    "Cleveland Guardians":     0.99,
    "Pittsburgh Pirates":      0.99,
    "St. Louis Cardinals":     0.98,
    "Arizona Diamondbacks":    0.98,
    "Washington Nationals":    0.98,
    "Tampa Bay Rays":          0.97,
    "Los Angeles Angels":      0.97,
    "New York Mets":           0.97,
    "Miami Marlins":           0.96,
    "Oakland Athletics":       0.96,
    "Athletics":               0.96,
    "Seattle Mariners":        0.95,
    "Los Angeles Dodgers":     0.95,
    "San Francisco Giants":    0.94,
    "San Diego Padres":        0.92,
}

HOME_ADVANTAGE_RUNS = 0.20

PITCHER_ERA_2025 = {
    # Elite tier
    "Paul Skenes": 1.96,
    "Tarik Skubal": 2.94,
    "Yoshinobu Yamamoto": 2.49,
    "Chris Sale": 3.10,
    "Max Fried": 3.25,
    "Zack Wheeler": 3.18,
    "Cristopher Sanchez": 2.95,
    "Logan Webb": 3.12,
    "Corbin Burnes": 3.22,
    "Spencer Strider": 3.20,
    "Freddy Peralta": 3.40,
    "Gerrit Cole": 3.40,
    "Dylan Cease": 3.38,
    "Luis Castillo": 3.50,
    "Sandy Alcantara": 3.50,
    "Framber Valdez": 3.45,
    "Kevin Gausman": 3.45,
    "Hunter Brown": 3.18,
    "Nick Pivetta": 2.87,
    "Drew Rasmussen": 2.76,
    "Sonny Gray": 3.80,
    "Yu Darvish": 3.80,
    "Mitch Keller": 3.91,
    # Mid tier
    "Jameson Taillon": 3.68,
    "Shane McClanahan": 3.86,
    "Roki Sasaki": 3.70,
    "Tanner Bibee": 4.24,
    "Zac Gallen": 3.85,
    "Gavin Williams": 3.92,
    "Shane Bieber": 3.60,
    "Luis Severino": 4.10,
    "Andrew Abbott": 4.05,
    "Reese Olson": 4.15,
    "Jared Jones": 4.20,
    "Nestor Cortes": 4.20,
    "Edward Cabrera": 4.20,
    "Chase Burns": 4.10,
    "Parker Messick": 4.20,
    "Emerson Hancock": 4.50,
    "Kyle Harrison": 4.30,
    "Nick Martinez": 4.40,
    "Eric Lauer": 4.35,
    "Chris Paddack": 4.55,
    "Walker Buehler": 4.80,
    "Braxton Garrett": 4.30,
    "Michael Soroka": 4.30,
    "Matthew Liberatore": 4.40,
    "Trevor Rogers": 4.35,
    "Robbie Ray": 4.80,
    "Jake Irvin": 4.60,
    "Carlos Rodon": 4.50,
    "Kyle Freeland": 4.65,
    "Cade Cavalli": 4.55,
    "Patrick Corbin": 5.20,
    # New 2026 names from early slate
    "Konnor Griffin": 3.90,
    "Simeon Woods Richardson": 4.40,
    "Jared Bubic": 4.50,
    "Frankie Montas": 4.60,
    "Jesus Luzardo": 4.10,
    "Jose Suarez": 4.70,
    "Bailey Ober": 3.90,
    "Joe Ryan": 3.85,
    "Aaron Civale": 4.50,
    "Bryce Miller": 4.20,
    "George Kirby": 3.60,
    "Bryan Woo": 3.80,
    "Michael King": 3.75,
    "MacKenzie Gore": 3.90,
    "Ranger Suarez": 3.80,
    "Tylor Megill": 4.30,
    "Jose Quintana": 4.50,
    "Charlie Morton": 4.40,
    "Dane Dunning": 4.60,
    "Graham Ashcraft": 4.55,
    "Hayden Wesneski": 4.40,
}

def get_park_factor(home_team):
    for key in PARK_FACTORS:
        if key.lower() in home_team.lower() or home_team.lower() in key.lower():
            return PARK_FACTORS[key]
    return 1.0

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

def save_bet(game_date, away, home, away_pitcher, home_pitcher, model_total,
             kalshi_line, kalshi_over_price, model_prob, your_prob, edge,
             direction, bet_amt, game_id=None):
    try:
        supabase.table("mlb_settlements").insert({
            "game_date": game_date,
            "away_team": away,
            "home_team": home,
            "away_pitcher": away_pitcher,
            "home_pitcher": home_pitcher,
            "model_total": model_total,
            "kalshi_line": kalshi_line,
            "kalshi_over_price": kalshi_over_price,
            "model_prob": model_prob,
            "your_prob": your_prob,
            "edge": round(edge, 4),
            "bet_direction": direction,
            "bet_amount": bet_amt,
            "game_id": game_id,
        }).execute()
        return True
    except Exception as e:
        st.error("Save error: " + str(e))
        return False

def fetch_final_score(game_id=None, game_date=None, away_team=None, home_team=None):
    """
    Fetch final run totals for a completed game.
    Tries by game_id first; falls back to matching by date + team names.
    Returns (away_runs, home_runs, total_runs) or None if not available.
    """
    try:
        if game_id:
            games = statsapi.schedule(game_id=int(game_id), sportId=1, hydrate='linescore')
        else:
            games = statsapi.schedule(date=game_date, sportId=1, hydrate='linescore')

        if not games:
            return None

        for g in games:
            # If we don't have a game_id, match by team name substring
            if not game_id:
                away_match = away_team and (
                    away_team.lower() in g.get('away_name', '').lower() or
                    g.get('away_name', '').lower() in away_team.lower()
                )
                home_match = home_team and (
                    home_team.lower() in g.get('home_name', '').lower() or
                    g.get('home_name', '').lower() in home_team.lower()
                )
                if not (away_match and home_match):
                    continue

            status = g.get('status', '')
            if status not in ('Final', 'Game Over', 'Completed Early'):
                return None  # Game not finished yet

            away_runs = g.get('away_score')
            home_runs = g.get('home_score')

            if away_runs is None or home_runs is None:
                return None

            return int(away_runs), int(home_runs), int(away_runs) + int(home_runs)

        return None

    except Exception:
        return None

def settle_result(actual_total, kalshi_line, bet_direction, bet_amount, kalshi_over_price):
    """
    Determine win/loss/push and calculate P&L.
    Returns (result_str, profit_loss)
    """
    if actual_total == kalshi_line:
        return "PUSH", 0.0

    if bet_direction == "OVER":
        won = actual_total > kalshi_line
        price = kalshi_over_price / 100
    else:  # UNDER
        won = actual_total < kalshi_line
        price = 1 - (kalshi_over_price / 100)

    if won:
        payout = round(bet_amount * ((1 / price) - 1), 2)
        return "WIN", payout
    else:
        return "LOSS", -round(bet_amount, 2)

def run_auto_settlement():
    """
    Called on app load. Finds all unsettled rows (actual_total IS NULL)
    for games before today, fetches final scores, and upserts results.
    """
    if not supabase_connected:
        return

    today_str = datetime.today().strftime('%Y-%m-%d')

    try:
        resp = supabase.table("mlb_settlements") \
            .select("*") \
            .is_("actual_total", "null") \
            .lt("game_date", today_str) \
            .execute()
    except Exception:
        return

    rows = resp.data if resp.data else []
    if not rows:
        return

    settled_count = 0
    skipped_count = 0

    progress = st.empty()
    progress.info(f"⏳ Auto-settling {len(rows)} unsettled bet(s)...")

    for row in rows:
        row_id = row.get("id")
        game_id = row.get("game_id")
        game_date = row.get("game_date")
        away_team = row.get("away_team")
        home_team = row.get("home_team")
        kalshi_line = row.get("kalshi_line")
        kalshi_over_price = row.get("kalshi_over_price", 50)
        bet_direction = row.get("bet_direction")
        bet_amount = row.get("bet_amount", 0)

        score = fetch_final_score(
            game_id=game_id,
            game_date=game_date,
            away_team=away_team,
            home_team=home_team
        )

        if score is None:
            skipped_count += 1
            continue

        away_runs, home_runs, actual_total = score
        result, profit_loss = settle_result(
            actual_total, kalshi_line, bet_direction, bet_amount, kalshi_over_price
        )

        try:
            supabase.table("mlb_settlements").update({
                "actual_total": actual_total,
                "away_score": away_runs,
                "home_score": home_runs,
                "result": result,
                "profit_loss": profit_loss,
                "settled_at": datetime.utcnow().isoformat(),
            }).eq("id", row_id).execute()
            settled_count += 1
        except Exception:
            skipped_count += 1
            continue

    if settled_count > 0 or skipped_count > 0:
        msg = f"✅ Auto-settlement complete: {settled_count} settled"
        if skipped_count:
            msg += f", {skipped_count} skipped (game not final or score unavailable)"
        progress.success(msg)
    else:
        progress.empty()

# ── Auto-settlement runs on every app load ──────────────────────────────────
run_auto_settlement()

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["Today's Games", "Settlement Tracker"])

with tab1:
    try:
        today = datetime.today().strftime('%Y-%m-%d')
        schedule = statsapi.schedule(date=today)

        if not schedule:
            st.warning("No games scheduled today.")
        else:
            # ── Compact summary table ─────────────────────────────────────────
            summary_rows = []
            for g in schedule:
                try:
                    _home = g['home_name']
                    _away = g['away_name']
                    _hp = g.get('home_probable_pitcher', 'TBD')
                    _ap = g.get('away_probable_pitcher', 'TBD')
                    _utc = datetime.strptime(g['game_datetime'], '%Y-%m-%dT%H:%M:%SZ')
                    _et = (_utc - timedelta(hours=4)).strftime('%I:%M %p')
                    _away_rpg = get_team_rpg(_away)
                    _home_rpg = get_team_rpg(_home) + HOME_ADVANTAGE_RUNS
                    _base = _away_rpg + _home_rpg
                    _model = round((_base + era_adjustment(get_pitcher_era(_ap)) + era_adjustment(get_pitcher_era(_hp))) * get_park_factor(_home), 1)
                    _pf = get_park_factor(_home)
                    _pf_str = f"{_pf:.2f} {'🏔️' if _pf >= 1.04 else '⬆️' if _pf > 1.0 else '➡️' if _pf == 1.0 else '⬇️'}"
                    _diff = _model - 8.5
                    _lean = "⬆️ OVER" if _diff > 0.3 else "⬇️ UNDER" if _diff < -0.3 else "➡️ EVEN"
                    summary_rows.append({
                        "Time": _et,
                        "Matchup": f"{_away} @ {_home}",
                        "Away SP": _ap if _ap != 'TBD' else '❓',
                        "Home SP": _hp if _hp != 'TBD' else '❓',
                        "Park": _pf_str,
                        "Model": _model,
                        "vs 8.5": f"{_diff:+.1f}",
                        "Lean": _lean,
                    })
                except Exception:
                    continue

            if summary_rows:
                st.subheader("📋 Today's Slate")
                st.caption("Model totals vs default 8.5 line — open a game below to enter the real Kalshi line.")
                st.dataframe(
                    pd.DataFrame(summary_rows),
                    use_container_width=True,
                    hide_index=True,
                )
                st.markdown("---")

            # ── Game expanders ────────────────────────────────────────────────
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
                        home_rpg = get_team_rpg(home) + HOME_ADVANTAGE_RUNS
                        base_total = round(away_rpg + home_rpg, 1)

                        away_era = get_pitcher_era(away_pitcher)
                        home_era = get_pitcher_era(home_pitcher)

                        away_adj = era_adjustment(away_era)
                        home_adj = era_adjustment(home_era)

                        park_factor = get_park_factor(home)
                        model_total = round((base_total + away_adj + home_adj) * park_factor, 1)

                        st.markdown("---")
                        col3, col4, col5 = st.columns(3)
                        with col3:
                            st.metric("Base Total", base_total)
                        with col4:
                            st.metric("Away ERA", away_era)
                        with col5:
                            st.metric("Home ERA", home_era)

                        col6, col7 = st.columns(2)
                        with col6:
                            pf_label = "🏟️ Park Factor"
                            pf_delta = f"{'Hitter' if park_factor > 1.0 else 'Pitcher' if park_factor < 1.0 else 'Neutral'} park"
                            st.metric(pf_label, park_factor, delta=pf_delta)
                        with col7:
                            st.metric("Home Advantage", f"+{HOME_ADVANTAGE_RUNS} R/G")

                        st.metric("Model Run Total Estimate", model_total)

                        kalshi_line = st.number_input("Enter Kalshi Line", min_value=0.0, max_value=20.0, value=8.5, step=0.5, key="line_" + game_id)

                        auto_prob = model_to_probability(model_total, kalshi_line)

                        if model_total > kalshi_line:
                            st.info("Model leans OVER - suggested probability: " + str(auto_prob) + "%")
                        elif model_total < kalshi_line:
                            st.info("Model leans UNDER - suggested probability: " + str(auto_prob) + "%")
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
                            if supabase_connected:
                                if st.button("Log This Bet", key="log_" + game_id):
                                    if save_bet(today, away, home, away_pitcher, home_pitcher,
                                                model_total, kalshi_line, kalshi_over_price,
                                                auto_prob, your_prob, edge, "OVER", bet_amt,
                                                game_id=game_id):
                                        st.success("Bet logged!")
                        elif edge <= -EDGE_THRESHOLD:
                            bet_pct, bet_amt = calc_kelly(abs(edge))
                            st.success("BET UNDER - Edge: " + str(round(abs(edge)*100,1)) + "% | Bet: $" + str(bet_amt))
                            if supabase_connected:
                                if st.button("Log This Bet", key="log_" + game_id):
                                    if save_bet(today, away, home, away_pitcher, home_pitcher,
                                                model_total, kalshi_line, kalshi_over_price,
                                                auto_prob, your_prob, edge, "UNDER", bet_amt,
                                                game_id=game_id):
                                        st.success("Bet logged!")
                        else:
                            st.info("No edge. Current edge: " + str(round(edge*100,1)) + "%")

                except Exception as game_error:
                    st.warning("Could not load game: " + str(game_error))
                    continue

    except Exception as e:
        st.error("Error: " + str(e))

with tab2:
    st.subheader("Settlement Tracker")
    if supabase_connected:
        try:
            data = supabase.table("mlb_settlements").select("*").order("game_date", desc=True).execute()
            if data.data:
                df = pd.DataFrame(data.data)

                # ── Summary metrics ───────────────────────────────────────────
                settled = df[df["result"].notna()]
                if not settled.empty:
                    total_bets = len(settled)
                    wins = (settled["result"] == "WIN").sum()
                    losses = (settled["result"] == "LOSS").sum()
                    pushes = (settled["result"] == "PUSH").sum()
                    total_pnl = settled["profit_loss"].sum()
                    win_pct = round(wins / (wins + losses) * 100, 1) if (wins + losses) > 0 else 0

                    m1, m2, m3, m4, m5 = st.columns(5)
                    m1.metric("Total Bets", total_bets)
                    m2.metric("Record", f"{wins}W-{losses}L-{pushes}P")
                    m3.metric("Win %", f"{win_pct}%")
                    m4.metric("Total P&L", f"${total_pnl:+.2f}")
                    m5.metric("Unsettled", len(df[df["result"].isna()]))

                    st.markdown("---")

                # ── Full table ────────────────────────────────────────────────
                display_cols = [c for c in [
                    "game_date", "away_team", "home_team",
                    "model_total", "kalshi_line", "bet_direction", "bet_amount",
                    "actual_total", "result", "profit_loss", "settled_at"
                ] if c in df.columns]

                st.dataframe(df[display_cols], use_container_width=True)
            else:
                st.info("No bets logged yet.")
        except Exception as e:
            st.error("Error loading settlements: " + str(e))
    else:
        st.warning("Supabase not connected.")
