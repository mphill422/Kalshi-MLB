import streamlit as st
import streamlit.components.v1 as components
import statsapi
import pandas as pd
import requests
from datetime import datetime, timedelta
from supabase import create_client

st.set_page_config(page_title="Kalshi MLB Model", layout="wide")
st.title("Kalshi MLB Run Total Model")
st.caption("Version 4.1 - " + datetime.today().strftime('%B %d, %Y'))

BANKROLL = 500
EDGE_THRESHOLD = 0.05
KELLY_FRACTION = 0.5
MAX_BET_PCT = 0.05
LEAGUE_AVG_ERA = 4.20
LEAGUE_AVG_BULLPEN_ERA = 4.10
SP_INNINGS = 5.0   # expected starter innings
TOTAL_INNINGS = 9.0

try:
    supabase = create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"]
    )
    supabase_connected = True
except:
    supabase_connected = False

# ── Team offense (2025 full season RPG baseline) ──────────────────────────────
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

# ── Bullpen ERA by team (2025 full season) ────────────────────────────────────
TEAM_BULLPEN_ERA = {
    # AL East
    "New York Yankees": 3.20,   # Elite — Bednar, Holmes, Abreu
    "Boston Red Sox": 4.10,
    "Toronto Blue Jays": 3.85,
    "Baltimore Orioles": 3.95,
    "Tampa Bay Rays": 3.50,     # Jax, strong pen
    # AL Central
    "Cleveland Guardians": 3.70,
    "Minnesota Twins": 4.00,
    "Detroit Tigers": 3.90,
    "Kansas City Royals": 4.50, # Blown saves early 2026
    "Chicago White Sox": 5.10,  # Weak pen
    # AL West
    "Houston Astros": 3.40,     # Abreu, strong core
    "Seattle Mariners": 3.72,   # Hader anchor
    "Texas Rangers": 4.20,
    "Los Angeles Angels": 4.60,
    "Oakland Athletics": 4.80,
    "Athletics": 4.80,
    # NL East
    "New York Mets": 3.80,      # Diaz
    "Philadelphia Phillies": 3.60,
    "Atlanta Braves": 3.90,
    "Washington Nationals": 4.40,
    "Miami Marlins": 4.30,
    # NL Central
    "Chicago Cubs": 4.10,
    "Milwaukee Brewers": 3.30,  # Megill, Ashby — elite
    "St. Louis Cardinals": 4.20,
    "Pittsburgh Pirates": 4.00,
    "Cincinnati Reds": 4.30,
    # NL West
    "Los Angeles Dodgers": 3.60, # Diaz signed, upgraded
    "San Diego Padres": 3.20,    # Best pen in MLB 2025
    "Arizona Diamondbacks": 4.10,
    "San Francisco Giants": 4.00,
    "Colorado Rockies": 5.20,    # Worst pen in baseball
}

# ── Park factors ──────────────────────────────────────────────────────────────
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

# ── Starting pitcher ERA (2025 season / 2026 projection) ─────────────────────
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
    # 2026 names
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

# ── Helper functions ──────────────────────────────────────────────────────────
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

def get_bullpen_era(team_name):
    for key in TEAM_BULLPEN_ERA:
        if key.lower() in team_name.lower() or team_name.lower() in key.lower():
            return TEAM_BULLPEN_ERA[key]
    return LEAGUE_AVG_BULLPEN_ERA

def get_pitcher_era(pitcher_name):
    if not pitcher_name or pitcher_name == 'TBD':
        return LEAGUE_AVG_ERA
    for key in PITCHER_ERA_2025:
        if key.lower() in pitcher_name.lower() or pitcher_name.lower() in key.lower():
            return PITCHER_ERA_2025[key]
    return LEAGUE_AVG_ERA

def get_pitcher_recent_era(pitcher_name):
    """
    Fetch last 3 starts ERA from StatsAPI.
    Returns recent ERA or None if unavailable.
    """
    if not pitcher_name or pitcher_name == 'TBD':
        return None
    try:
        results = statsapi.lookup_player(pitcher_name)
        if not results:
            return None
        player_id = results[0]['id']
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - timedelta(days=45)).strftime('%Y-%m-%d')
        logs = statsapi.player_stat_data(
            player_id,
            group='pitching',
            type='gameLog',
            sportId=1
        )
        if not logs or 'stats' not in logs:
            return None
        games = logs['stats']
        starts = [g for g in games if g.get('gamesStarted', 0) >= 1][-3:]
        if not starts:
            return None
        total_er = sum(float(g.get('earnedRuns', 0)) for g in starts)
        total_ip = sum(float(g.get('inningsPitched', 0)) for g in starts)
        if total_ip < 3:
            return None
        return round((total_er / total_ip) * 9, 2)
    except Exception:
        return None

def blend_pitcher_era(pitcher_name):
    """
    Blend season ERA (70%) with last 3 starts ERA (30%).
    Falls back to season ERA if recent data unavailable.
    """
    season_era = get_pitcher_era(pitcher_name)
    recent_era = get_pitcher_recent_era(pitcher_name)
    if recent_era is None:
        return season_era, None
    blended = round(season_era * 0.70 + recent_era * 0.30, 2)
    return blended, recent_era

def era_adjustment(pitcher_era):
    diff = pitcher_era - LEAGUE_AVG_ERA
    return round(diff * 0.5, 2)

def bullpen_adjustment(team_name):
    """
    Runs contributed by bullpen over expected ~4 innings.
    Relative to league average bullpen.
    """
    bp_era = get_bullpen_era(team_name)
    bp_innings = TOTAL_INNINGS - SP_INNINGS
    league_bp_runs = (LEAGUE_AVG_BULLPEN_ERA / 9) * bp_innings
    team_bp_runs = (bp_era / 9) * bp_innings
    return round(team_bp_runs - league_bp_runs, 2)

def calc_model_total(away, home, away_pitcher, home_pitcher):
    """
    Full model calculation. Returns dict of all components.
    """
    away_rpg = get_team_rpg(away)
    home_rpg = get_team_rpg(home) + HOME_ADVANTAGE_RUNS
    base_total = round(away_rpg + home_rpg, 1)

    away_sp_era, away_recent = blend_pitcher_era(away_pitcher)
    home_sp_era, home_recent = blend_pitcher_era(home_pitcher)

    away_sp_adj = era_adjustment(away_sp_era)
    home_sp_adj = era_adjustment(home_sp_era)

    # Bullpen: away bullpen faces home offense, home bullpen faces away offense
    away_bp_adj = bullpen_adjustment(away)
    home_bp_adj = bullpen_adjustment(home)

    park_factor = get_park_factor(home)

    raw_total = base_total + away_sp_adj + home_sp_adj + away_bp_adj + home_bp_adj
    model_total = round(raw_total * park_factor, 1)

    return {
        "base_total": base_total,
        "away_sp_era": away_sp_era,
        "home_sp_era": home_sp_era,
        "away_recent_era": away_recent,
        "home_recent_era": home_recent,
        "away_sp_adj": away_sp_adj,
        "home_sp_adj": home_sp_adj,
        "away_bp_era": get_bullpen_era(away),
        "home_bp_era": get_bullpen_era(home),
        "away_bp_adj": away_bp_adj,
        "home_bp_adj": home_bp_adj,
        "park_factor": park_factor,
        "model_total": model_total,
    }

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
    try:
        if game_id:
            games = statsapi.schedule(game_id=int(game_id), sportId=1, hydrate='linescore')
        else:
            games = statsapi.schedule(date=game_date, sportId=1, hydrate='linescore')
        if not games:
            return None
        for g in games:
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
                return None
            away_runs = g.get('away_score')
            home_runs = g.get('home_score')
            if away_runs is None or home_runs is None:
                return None
            return int(away_runs), int(home_runs), int(away_runs) + int(home_runs)
        return None
    except Exception:
        return None

def settle_result(actual_total, kalshi_line, bet_direction, bet_amount, kalshi_over_price):
    if actual_total == kalshi_line:
        return "PUSH", 0.0
    if bet_direction == "OVER":
        won = actual_total > kalshi_line
        price = kalshi_over_price / 100
    else:
        won = actual_total < kalshi_line
        price = 1 - (kalshi_over_price / 100)
    if won:
        payout = round(bet_amount * ((1 / price) - 1), 2)
        return "WIN", payout
    else:
        return "LOSS", -round(bet_amount, 2)

def run_auto_settlement():
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


# ── Kalshi MLB market feed ────────────────────────────────────────────────────
# Team abbreviation map: Kalshi 3-letter code → full team name fragment
KALSHI_TEAM_MAP = {
    "NYY": "Yankees", "BOS": "Red Sox", "TOR": "Blue Jays",
    "BAL": "Orioles", "TBR": "Rays",    "TAM": "Rays",
    "CLE": "Guardians", "MIN": "Twins", "DET": "Tigers",
    "KCR": "Royals",  "KAN": "Royals", "CWS": "White Sox", "CHW": "White Sox",
    "HOU": "Astros",  "SEA": "Mariners", "TEX": "Rangers",
    "LAA": "Angels",  "OAK": "Athletics", "ATH": "Athletics",
    "NYM": "Mets",    "PHI": "Phillies", "ATL": "Braves",
    "WSH": "Nationals", "WAS": "Nationals", "MIA": "Marlins",
    "CHC": "Cubs",    "MIL": "Brewers", "STL": "Cardinals",
    "PIT": "Pirates", "CIN": "Reds",
    "LAD": "Dodgers", "SDP": "Padres",  "SAN": "Padres",
    "ARI": "Diamondbacks", "SFG": "Giants", "COL": "Rockies",
}

@st.cache_data(ttl=300)
def fetch_kalshi_mlb_lines():
    """
    Read Kalshi MLB lines from Supabase kalshi_lines table.
    Table is populated by the fetch-kalshi-lines Edge Function.
    """
    if not supabase_connected:
        return {"__error__": "Supabase not connected"}
    try:
        today = datetime.today().strftime('%Y-%m-%d')
        resp = supabase.table("kalshi_lines").select("*").eq("game_date", today).execute()
        rows = resp.data or []
        result = {}
        for row in rows:
            away = (row.get("away_team") or "").lower()
            home = (row.get("home_team") or "").lower()
            if not away or not home:
                continue
            result[(away, home)] = {
                "line": float(row.get("line", 8.5)),
                "over_price_cents": int(row.get("over_price_cents", 50)),
                "ticker": row.get("ticker", ""),
                "title": "",
            }
        if not result:
            return {"__error__": f"No lines in table for {today} — trigger Edge Function"}
        return result
    except Exception as e:
        return {"__error__": str(e)}


def match_kalshi_line(away_name, home_name, kalshi_lines):
    """
    Find the Kalshi market for a given game by fuzzy team name matching.
    Returns {line, over_price_cents} or None.
    """
    for (k_away, k_home), data in kalshi_lines.items():
        if k_away in away_name.lower() or away_name.lower() in k_away:
            if k_home in home_name.lower() or home_name.lower() in k_home:
                return data
    return None

# ── Auto-settlement on load ───────────────────────────────────────────────────
run_auto_settlement()

# ── Fetch Kalshi lines via browser-side JS component ─────────────────────────
import json as _json

def get_kalshi_via_js():
    """
    Injects a JS fetch call that runs in the user browser (not Streamlit server).
    Browser has no network restrictions. Returns data via Streamlit component.
    """
    kalshi_js = """
    <script>
    async function fetchKalshi() {
        try {
            const url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXMLBGAME&status=open&limit=200";
            const resp = await fetch(url, {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                }
            });
            const data = await resp.json();
            const markets = data.markets || [];
            
            // Send to Streamlit via query param trick
            const result = JSON.stringify(markets);
            const encoded = encodeURIComponent(result);
            
            // Store in sessionStorage so Streamlit can read it
            sessionStorage.setItem('kalshi_markets', result);
            document.getElementById('kalshi-status').innerText = 'loaded:' + markets.length;
        } catch(e) {
            document.getElementById('kalshi-status').innerText = 'error:' + e.message;
        }
    }
    
    // Check if already loaded this session
    const cached = sessionStorage.getItem('kalshi_markets');
    if (cached) {
        document.getElementById('kalshi-status').innerText = 'cached:' + JSON.parse(cached).length;
    } else {
        fetchKalshi();
    }
    </script>
    <div id="kalshi-status" style="display:none">loading</div>
    """
    result = st.components.v1.html(kalshi_js, height=0)
    return result

# Try server-side first, fall back to client-side approach
kalshi_lines = fetch_kalshi_mlb_lines()
_kalshi_error = kalshi_lines.pop("__error__", None) if kalshi_lines else None
if kalshi_lines:
    kalshi_status = f"✅ Kalshi feed live: {len(kalshi_lines)} game(s) loaded"
    kalshi_caption_type = "success"
else:
    err_msg = _kalshi_error or "connection failed"
    kalshi_status = f"⚠️ Kalshi feed unavailable: {err_msg}"
    kalshi_caption_type = "warning"

# ── Tabs ──────────────────────────────────────────────────────────────────────
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
                    m = calc_model_total(_away, _home, _ap, _hp)
                    _model = m["model_total"]
                    _pf = m["park_factor"]
                    _pf_str = f"{_pf:.2f} {'🏔️' if _pf >= 1.04 else '⬆️' if _pf > 1.0 else '➡️' if _pf == 1.0 else '⬇️'}"
                    # Use real Kalshi line if available, else 8.5 default
                    _kalshi = match_kalshi_line(_away, _home, kalshi_lines)
                    _k_line = _kalshi["line"] if _kalshi else 8.5
                    _k_price = _kalshi["over_price_cents"] if _kalshi else 50
                    _has_kalshi = _kalshi is not None

                    _diff = round(_model - _k_line, 1)
                    _lean = "OVER" if _diff > 0.3 else "UNDER" if _diff < -0.3 else "EVEN"
                    _diff_str = f"{_diff:+.1f}"

                    # Real edge vs actual Kalshi market
                    _model_prob = model_to_probability(_model, _k_line) / 100
                    if _lean == "OVER":
                        _real_edge = _model_prob - (_k_price / 100)
                    else:
                        _real_edge = (1 - _model_prob) - (1 - _k_price / 100)
                    _edge_pct = round(abs(_real_edge) * 100, 1)
                    _has_edge = _real_edge >= EDGE_THRESHOLD

                    # Confidence tier
                    if not _has_edge:
                        _tier = "⚪ NO EDGE"
                    elif _edge_pct >= 12:
                        _tier = "🔥 HIGH"
                    elif _edge_pct >= 8:
                        _tier = "💪 STRONG"
                    else:
                        _tier = "👍 LEAN"

                    _line_label = f"{_k_line} {'✅' if _has_kalshi else '~'}"
                    summary_rows.append({
                        "Time": _et,
                        "Matchup": f"{_away} @ {_home}",
                        "Away SP": _ap if _ap != 'TBD' else '❓',
                        "Home SP": _hp if _hp != 'TBD' else '❓',
                        "Park": _pf_str,
                        "Model": _model,
                        "Line": _line_label,
                        "vs Line": ("🟢 " if _diff > 0.3 else "🔴 " if _diff < -0.3 else "⚪ ") + _diff_str,
                        "Lean": "🟢 OVER" if _lean == "OVER" else "🔴 UNDER" if _lean == "UNDER" else "⚪ EVEN",
                        "Edge": f"{_edge_pct}%",
                        "Signal": _tier,
                    })
                except Exception:
                    continue

            if summary_rows:
                st.subheader("📋 Today's Slate")
                if kalshi_caption_type == "success":
                    st.success(kalshi_status)
                else:
                    st.warning(kalshi_status)
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

                        m = calc_model_total(away, home, away_pitcher, home_pitcher)
                        model_total = m["model_total"]

                        st.markdown("---")

                        # Row 1: Base total + park factor + home adv
                        col3, col4, col5 = st.columns(3)
                        with col3:
                            st.metric("Base Total", m["base_total"])
                        with col4:
                            pf = m["park_factor"]
                            st.metric("🏟️ Park Factor", pf,
                                delta=f"{'Hitter' if pf > 1.0 else 'Pitcher' if pf < 1.0 else 'Neutral'} park")
                        with col5:
                            st.metric("Home Advantage", f"+{HOME_ADVANTAGE_RUNS} R/G")

                        # Row 2: SP ERAs with recent form
                        col6, col7 = st.columns(2)
                        with col6:
                            away_era_label = f"Away SP ERA ({away_pitcher})"
                            away_era_display = m["away_sp_era"]
                            away_recent = m["away_recent_era"]
                            delta_str = f"Recent: {away_recent}" if away_recent else "Season only"
                            st.metric(away_era_label, away_era_display, delta=delta_str)
                        with col7:
                            home_era_label = f"Home SP ERA ({home_pitcher})"
                            home_era_display = m["home_sp_era"]
                            home_recent = m["home_recent_era"]
                            delta_str = f"Recent: {home_recent}" if home_recent else "Season only"
                            st.metric(home_era_label, home_era_display, delta=delta_str)

                        # Row 3: Bullpen ERAs
                        col8, col9 = st.columns(2)
                        with col8:
                            st.metric(f"Away Bullpen ERA ({away})",
                                m["away_bp_era"],
                                delta=f"Adj: {m['away_bp_adj']:+.2f} runs")
                        with col9:
                            st.metric(f"Home Bullpen ERA ({home})",
                                m["home_bp_era"],
                                delta=f"Adj: {m['home_bp_adj']:+.2f} runs")

                        st.metric("🎯 Model Run Total Estimate", model_total)

                        # Pre-fill from Kalshi feed if available
                        _game_kalshi = match_kalshi_line(away, home, kalshi_lines)
                        _default_line = float(_game_kalshi["line"]) if _game_kalshi else 8.5
                        _default_price = int(_game_kalshi["over_price_cents"]) if _game_kalshi else 50
                        if _game_kalshi:
                            st.success(f"✅ Kalshi line auto-loaded: {_default_line} | Over price: {_default_price}¢")

                        kalshi_line = st.number_input("Enter Kalshi Line", min_value=0.0, max_value=20.0, value=_default_line, step=0.5, key="line_" + game_id)
                        auto_prob = model_to_probability(model_total, kalshi_line)

                        if model_total > kalshi_line:
                            st.info("Model leans OVER — suggested probability: " + str(auto_prob) + "%")
                        elif model_total < kalshi_line:
                            st.info("Model leans UNDER — suggested probability: " + str(auto_prob) + "%")
                        else:
                            st.info("Model is neutral on this game.")

                        kalshi_over_price = st.number_input("Kalshi Over Price (cents)", min_value=1, max_value=99, value=_default_price, step=1, key="price_" + game_id)
                        your_prob = st.slider("Your Over Probability %", 0, 100, auto_prob, key="prob_" + game_id)

                        kalshi_implied = kalshi_over_price / 100
                        your_implied = your_prob / 100
                        edge = your_implied - kalshi_implied

                        if edge >= EDGE_THRESHOLD:
                            bet_pct, bet_amt = calc_kelly(edge)
                            st.success("BET OVER — Edge: " + str(round(edge*100,1)) + "% | Bet: $" + str(bet_amt))
                            if supabase_connected:
                                if st.button("Log This Bet", key="log_" + game_id):
                                    if save_bet(today, away, home, away_pitcher, home_pitcher,
                                                model_total, kalshi_line, kalshi_over_price,
                                                auto_prob, your_prob, edge, "OVER", bet_amt,
                                                game_id=game_id):
                                        st.success("Bet logged!")
                        elif edge <= -EDGE_THRESHOLD:
                            bet_pct, bet_amt = calc_kelly(abs(edge))
                            st.success("BET UNDER — Edge: " + str(round(abs(edge)*100,1)) + "% | Bet: $" + str(bet_amt))
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
