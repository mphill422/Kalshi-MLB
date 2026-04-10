import streamlit as st
import streamlit.components.v1 as components
import statsapi
import pandas as pd
import requests
from datetime import datetime, timedelta
from supabase import create_client

st.set_page_config(page_title="Kalshi MLB Model", layout="wide")
st.title("Kalshi MLB Run Total Model")
st.caption("Version 4.12 - " + datetime.today().strftime('%B %d, %Y'))

BANKROLL = 500
EDGE_THRESHOLD = 0.05
KELLY_FRACTION = 0.5
MAX_BET_PCT = 0.05
LEAGUE_AVG_ERA = 4.20
LEAGUE_AVG_BULLPEN_ERA = 4.10
SP_INNINGS = 5.0
TOTAL_INNINGS = 9.0
F5_INNINGS = 5.0

try:
    supabase = create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"]
    )
    supabase_connected = True
except:
    supabase_connected = False

def get_secret(key):
    try:
        val = st.secrets["api_keys"][key]
        if val:
            return str(val)
    except Exception:
        pass
    try:
        val = st.secrets[key]
        if val:
            return str(val)
    except Exception:
        pass
    return ""

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🔧 System Status")
    st.markdown(f"**Supabase:** {'✅ Connected' if supabase_connected else '❌ Not connected'}")
    _odds_key = get_secret("ODDS_API_KEY")
    _wethr_key = get_secret("WETHR_API_KEY")
    st.markdown(f"**Odds API Key:** {'✅ Loaded' if _odds_key else '❌ Missing'}")
    if _odds_key:
        st.caption(f"Prefix: {_odds_key[:6]}…")
    st.markdown(f"**Wethr API Key:** {'✅ Loaded' if _wethr_key else '❌ Missing'}")
    if _wethr_key:
        st.caption(f"Prefix: {_wethr_key[:6]}…")
    st.markdown("---")

# ── Static data ───────────────────────────────────────────────────────────────

PARK_FACTORS = {
    "Colorado Rockies": 1.15, "Cincinnati Reds": 1.07, "Texas Rangers": 1.06,
    "Boston Red Sox": 1.05, "Chicago Cubs": 1.04, "Philadelphia Phillies": 1.04,
    "Baltimore Orioles": 1.03, "Atlanta Braves": 1.02, "Kansas City Royals": 1.02,
    "Toronto Blue Jays": 1.01, "Houston Astros": 1.01, "Detroit Tigers": 1.00,
    "Minnesota Twins": 1.00, "New York Yankees": 1.00, "Chicago White Sox": 1.00,
    "Cleveland Guardians": 0.99, "Pittsburgh Pirates": 0.99, "St. Louis Cardinals": 0.98,
    "Arizona Diamondbacks": 0.98, "Washington Nationals": 0.98, "Tampa Bay Rays": 0.97,
    "Los Angeles Angels": 0.97, "New York Mets": 0.97, "Miami Marlins": 0.96,
    "Oakland Athletics": 0.96, "Athletics": 0.96, "Seattle Mariners": 0.95,
    "Los Angeles Dodgers": 0.95, "San Francisco Giants": 0.94, "San Diego Padres": 0.92,
}

HOME_ADVANTAGE_RUNS = 0.20
HOME_ADVANTAGE_F5 = 0.10

STADIUM_WEATHER = {
    "Arizona Diamondbacks": None, "Atlanta Braves": "KATL", "Baltimore Orioles": "KBWI",
    "Boston Red Sox": "KBOS", "Chicago Cubs": "KORD", "Chicago White Sox": None,
    "Cincinnati Reds": "KLUK", "Cleveland Guardians": "KCLE", "Colorado Rockies": "KDEN",
    "Detroit Tigers": "KDTW", "Houston Astros": None, "Kansas City Royals": "KMCI",
    "Los Angeles Angels": "KSNA", "Los Angeles Dodgers": "KLAX", "Miami Marlins": None,
    "Milwaukee Brewers": None, "Minnesota Twins": None, "New York Mets": "KJFK",
    "New York Yankees": "KJFK", "Oakland Athletics": "KOAK", "Athletics": "KOAK",
    "Philadelphia Phillies": "KPHL", "Pittsburgh Pirates": "KPIT", "San Diego Padres": "KSAN",
    "San Francisco Giants": "KSFO", "Seattle Mariners": None, "St. Louis Cardinals": "KSTL",
    "Tampa Bay Rays": None, "Texas Rangers": None, "Toronto Blue Jays": None,
    "Washington Nationals": "KDCA",
}

PITCHER_ERA_FALLBACK = {
    "Paul Skenes": 1.96, "Tarik Skubal": 2.94, "Yoshinobu Yamamoto": 2.49,
    "Chris Sale": 3.10, "Max Fried": 3.25, "Zack Wheeler": 3.18,
    "Cristopher Sanchez": 2.95, "Logan Webb": 3.12, "Corbin Burnes": 3.22,
    "Spencer Strider": 3.20, "Freddy Peralta": 3.40, "Gerrit Cole": 3.40,
    "Dylan Cease": 3.38, "Luis Castillo": 3.50, "Sandy Alcantara": 3.50,
    "Framber Valdez": 3.45, "Kevin Gausman": 3.45, "Hunter Brown": 3.18,
    "Nick Pivetta": 2.87, "Drew Rasmussen": 2.76, "Sonny Gray": 3.80,
    "Yu Darvish": 3.80, "Mitch Keller": 3.91, "Jameson Taillon": 3.68,
    "Shane McClanahan": 3.86, "Roki Sasaki": 3.70, "Tanner Bibee": 4.24,
    "Zac Gallen": 3.85, "Gavin Williams": 3.92, "Shane Bieber": 3.60,
    "Luis Severino": 4.10, "Andrew Abbott": 4.05, "Reese Olson": 4.15,
    "Jared Jones": 4.20, "Nestor Cortes": 4.20, "Edward Cabrera": 4.20,
    "Chase Burns": 4.10, "Parker Messick": 4.20, "Emerson Hancock": 4.50,
    "Kyle Harrison": 4.30, "Nick Martinez": 4.40, "Eric Lauer": 4.35,
    "Chris Paddack": 4.55, "Walker Buehler": 4.80, "Braxton Garrett": 4.30,
    "Michael Soroka": 4.30, "Matthew Liberatore": 4.40, "Trevor Rogers": 4.35,
    "Robbie Ray": 4.80, "Jake Irvin": 4.60, "Carlos Rodon": 4.50,
    "Kyle Freeland": 4.65, "Cade Cavalli": 4.55, "Patrick Corbin": 5.20,
    "Konnor Griffin": 3.90, "Simeon Woods Richardson": 4.40, "Jared Bubic": 4.50,
    "Frankie Montas": 4.60, "Jesus Luzardo": 4.10, "Jose Suarez": 4.70,
    "Bailey Ober": 3.90, "Joe Ryan": 3.85, "Aaron Civale": 4.50,
    "Bryce Miller": 4.20, "George Kirby": 3.60, "Bryan Woo": 3.80,
    "Michael King": 3.75, "MacKenzie Gore": 3.90, "Ranger Suarez": 3.80,
    "Tylor Megill": 4.30, "Jose Quintana": 4.50, "Charlie Morton": 4.40,
    "Dane Dunning": 4.60, "Graham Ashcraft": 4.55, "Hayden Wesneski": 4.40,
}

TEAM_RUNS_FALLBACK = {
    "New York Yankees": 4.7, "Boston Red Sox": 4.7, "Toronto Blue Jays": 4.8,
    "Baltimore Orioles": 4.5, "Tampa Bay Rays": 4.1, "Cleveland Guardians": 4.3,
    "Minnesota Twins": 4.5, "Detroit Tigers": 4.4, "Kansas City Royals": 4.3,
    "Chicago White Sox": 3.6, "Houston Astros": 4.6, "Seattle Mariners": 4.2,
    "Texas Rangers": 4.4, "Los Angeles Angels": 3.9, "Oakland Athletics": 3.7,
    "Athletics": 3.7, "New York Mets": 4.7, "Philadelphia Phillies": 4.9,
    "Atlanta Braves": 5.0, "Washington Nationals": 4.1, "Miami Marlins": 3.8,
    "Chicago Cubs": 4.4, "Milwaukee Brewers": 4.3, "St. Louis Cardinals": 4.2,
    "Pittsburgh Pirates": 4.0, "Cincinnati Reds": 4.4, "Los Angeles Dodgers": 5.1,
    "San Diego Padres": 4.4, "Arizona Diamondbacks": 4.7, "San Francisco Giants": 4.1,
    "Colorado Rockies": 4.5,
}

TEAM_BULLPEN_FALLBACK = {
    "New York Yankees": 3.20, "Boston Red Sox": 4.10, "Toronto Blue Jays": 3.85,
    "Baltimore Orioles": 3.95, "Tampa Bay Rays": 3.50, "Cleveland Guardians": 3.70,
    "Minnesota Twins": 4.00, "Detroit Tigers": 3.90, "Kansas City Royals": 4.50,
    "Chicago White Sox": 5.10, "Houston Astros": 3.40, "Seattle Mariners": 3.72,
    "Texas Rangers": 4.20, "Los Angeles Angels": 4.60, "Oakland Athletics": 4.80,
    "Athletics": 4.80, "New York Mets": 3.80, "Philadelphia Phillies": 3.60,
    "Atlanta Braves": 3.90, "Washington Nationals": 4.40, "Miami Marlins": 4.30,
    "Chicago Cubs": 4.10, "Milwaukee Brewers": 3.30, "St. Louis Cardinals": 4.20,
    "Pittsburgh Pirates": 4.00, "Cincinnati Reds": 4.30, "Los Angeles Dodgers": 3.60,
    "San Diego Padres": 3.20, "Arizona Diamondbacks": 4.10, "San Francisco Giants": 4.00,
    "Colorado Rockies": 5.20,
}

# ── Live stat fetchers ────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def fetch_live_team_stats():
    rpg = {}
    bullpen_era = {}
    try:
        season = datetime.today().year
        teams = statsapi.get('teams', {'sportId': 1, 'season': season})
        for team in teams.get('teams', []):
            team_id = team['id']
            team_name = team['name']
            try:
                hitting = statsapi.get('team_stats', {
                    'teamId': team_id, 'group': 'hitting',
                    'type': 'season', 'season': season, 'sportId': 1
                })
                for split in hitting.get('stats', [{}])[0].get('splits', []):
                    stat = split.get('stat', {})
                    games = int(stat.get('gamesPlayed', 0) or 0)
                    runs = int(stat.get('runs', 0) or 0)
                    if games >= 5:
                        rpg[team_name] = round(runs / games, 2)
            except Exception:
                pass
            try:
                pitching = statsapi.get('team_stats', {
                    'teamId': team_id, 'group': 'pitching',
                    'type': 'season', 'season': season, 'sportId': 1
                })
                for split in pitching.get('stats', [{}])[0].get('splits', []):
                    stat = split.get('stat', {})
                    era = stat.get('era')
                    games = int(stat.get('gamesPlayed', 0) or 0)
                    if era and games >= 5:
                        bullpen_era[team_name] = round(float(era), 2)
            except Exception:
                pass
    except Exception:
        pass
    return rpg, bullpen_era

@st.cache_data(ttl=3600)
def fetch_live_sp_era(pitcher_name):
    if not pitcher_name or pitcher_name == 'TBD':
        return LEAGUE_AVG_ERA, 'default'
    try:
        results = statsapi.lookup_player(pitcher_name)
        if not results:
            raise ValueError("Not found")
        player_id = results[0]['id']
        stats = statsapi.player_stat_data(player_id, group='pitching', type='season', sportId=1)
        if stats and 'stats' in stats:
            for sg in stats['stats']:
                splits = sg.get('splits', [])
                if splits:
                    s = splits[0].get('stat', {})
                    era = s.get('era')
                    ip = float(s.get('inningsPitched', 0) or 0)
                    if era and ip >= 5:
                        return round(float(era), 2), 'live'
    except Exception:
        pass
    for key in PITCHER_ERA_FALLBACK:
        if key.lower() in pitcher_name.lower() or pitcher_name.lower() in key.lower():
            return PITCHER_ERA_FALLBACK[key], 'fallback'
    return LEAGUE_AVG_ERA, 'default'

@st.cache_data(ttl=3600)
def fetch_recent_era(pitcher_name):
    if not pitcher_name or pitcher_name == 'TBD':
        return None
    try:
        results = statsapi.lookup_player(pitcher_name)
        if not results:
            return None
        player_id = results[0]['id']
        logs = statsapi.player_stat_data(player_id, group='pitching', type='gameLog', sportId=1)
        if not logs or 'stats' not in logs:
            return None
        starts = [g for g in logs['stats'] if g.get('gamesStarted', 0) >= 1][-3:]
        if not starts:
            return None
        total_er = sum(float(g.get('earnedRuns', 0)) for g in starts)
        total_ip = sum(float(g.get('inningsPitched', 0)) for g in starts)
        if total_ip < 3:
            return None
        return round((total_er / total_ip) * 9, 2)
    except Exception:
        return None

@st.cache_data(ttl=1800)
def fetch_stadium_weather(home_team):
    station = STADIUM_WEATHER.get(home_team)
    if not station:
        return {"dome": True}
    api_key = get_secret("WETHR_API_KEY")
    if not api_key:
        return None
    endpoints = [
        (f"https://api.wethr.net/v1/current/{station}", {"Authorization": f"Bearer {api_key}"}),
        (f"https://api.wethr.net/v1/observations/{station}", {"X-API-Key": api_key}),
        (f"https://api.wethr.net/current/{station}", {"Authorization": f"Bearer {api_key}"}),
    ]
    for url, headers in endpoints:
        try:
            resp = requests.get(url, headers={**headers, "Accept": "application/json"}, timeout=8)
            if resp.status_code == 200:
                d = resp.json()
                temp = d.get("temperature_f") or d.get("temp_f") or d.get("temperature") or d.get("temp")
                wspeed = d.get("wind_speed_mph") or d.get("wind_speed") or d.get("windSpeed") or 0
                wdir_deg = d.get("wind_direction_deg") or d.get("wind_dir_deg") or d.get("windDirection") or 0
                wdir_label = d.get("wind_direction") or d.get("windDirectionLabel") or ""
                return {"dome": False, "temp_f": temp, "wind_speed_mph": wspeed,
                        "wind_dir_deg": wdir_deg, "wind_dir_label": wdir_label, "station": station}
        except Exception:
            continue
    return None

# Load live team stats
_live_rpg, _live_bullpen = fetch_live_team_stats()

with st.sidebar:
    rpg_count = len(_live_rpg)
    bp_count = len(_live_bullpen)
    st.markdown(f"**Live RPG:** {'✅' if rpg_count >= 20 else '⚠️'} {rpg_count} teams")
    st.markdown(f"**Live Bullpen ERA:** {'✅' if bp_count >= 20 else '⚠️'} {bp_count} teams")
    st.caption("Live stats kick in after ≥5 games played.")

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_team_rpg(team_name):
    for key in _live_rpg:
        if key.lower() in team_name.lower() or team_name.lower() in key.lower():
            return _live_rpg[key]
    for key in TEAM_RUNS_FALLBACK:
        if key.lower() in team_name.lower() or team_name.lower() in key.lower():
            return TEAM_RUNS_FALLBACK[key]
    return 4.2

def get_bullpen_era(team_name):
    for key in _live_bullpen:
        if key.lower() in team_name.lower() or team_name.lower() in key.lower():
            return _live_bullpen[key]
    for key in TEAM_BULLPEN_FALLBACK:
        if key.lower() in team_name.lower() or team_name.lower() in key.lower():
            return TEAM_BULLPEN_FALLBACK[key]
    return LEAGUE_AVG_BULLPEN_ERA

def get_park_factor(home_team):
    for key in PARK_FACTORS:
        if key.lower() in home_team.lower() or home_team.lower() in key.lower():
            return PARK_FACTORS[key]
    return 1.0

def blend_era(pitcher_name):
    season_era, src = fetch_live_sp_era(pitcher_name)
    recent = fetch_recent_era(pitcher_name)
    if recent is None:
        return season_era, None, src
    return round(season_era * 0.70 + recent * 0.30, 2), recent, src

def weather_adjs(weather, scale=1.0):
    if not weather or weather.get("dome"):
        return 0.0, 0.0
    import math
    wspeed = weather.get("wind_speed_mph") or 0
    wdir = weather.get("wind_dir_deg") or 0
    w_adj = 0.0
    if wspeed and wspeed >= 5:
        out_factor = math.cos(math.radians(wdir)) * -1
        w_adj = round(out_factor * (wspeed / 10) * 0.3 * scale, 2)
    temp = weather.get("temp_f")
    t_adj = 0.0
    if temp and temp < 50:
        t_adj = round((50 - temp) * -0.02 * scale, 2)
    return w_adj, t_adj

def calc_f5(away, home, away_pitcher, home_pitcher, pf, weather):
    away_rpg = get_team_rpg(away) * (F5_INNINGS / TOTAL_INNINGS)
    home_rpg = (get_team_rpg(home) + HOME_ADVANTAGE_F5) * (F5_INNINGS / TOTAL_INNINGS)
    base = round(away_rpg + home_rpg, 2)
    away_era, away_recent, away_src = blend_era(away_pitcher)
    home_era, home_recent, home_src = blend_era(home_pitcher)
    away_sp_adj = round(((away_era - LEAGUE_AVG_ERA) / 9) * F5_INNINGS * 0.5, 2)
    home_sp_adj = round(((home_era - LEAGUE_AVG_ERA) / 9) * F5_INNINGS * 0.5, 2)
    w_adj, t_adj = weather_adjs(weather, scale=F5_INNINGS / TOTAL_INNINGS)
    raw = base + away_sp_adj + home_sp_adj + w_adj + t_adj
    return {
        "total": round(raw * pf, 1), "base": base,
        "away_era": away_era, "away_recent": away_recent, "away_src": away_src,
        "home_era": home_era, "home_recent": home_recent, "home_src": home_src,
        "away_sp_adj": away_sp_adj, "home_sp_adj": home_sp_adj,
        "wind_adj": w_adj, "temp_adj": t_adj,
    }

def calc_fg(away, home, away_pitcher, home_pitcher, pf, weather):
    away_rpg = get_team_rpg(away)
    home_rpg = get_team_rpg(home) + HOME_ADVANTAGE_RUNS
    base = round(away_rpg + home_rpg, 1)
    away_era, away_recent, away_src = blend_era(away_pitcher)
    home_era, home_recent, home_src = blend_era(home_pitcher)
    away_sp_adj = round(((away_era - LEAGUE_AVG_ERA) / 9) * SP_INNINGS * 0.5, 2)
    home_sp_adj = round(((home_era - LEAGUE_AVG_ERA) / 9) * SP_INNINGS * 0.5, 2)
    away_bp_era = get_bullpen_era(away)
    home_bp_era = get_bullpen_era(home)
    bp_inn = TOTAL_INNINGS - SP_INNINGS
    away_bp_adj = round(((away_bp_era - LEAGUE_AVG_BULLPEN_ERA) / 9) * bp_inn, 2)
    home_bp_adj = round(((home_bp_era - LEAGUE_AVG_BULLPEN_ERA) / 9) * bp_inn, 2)
    w_adj, t_adj = weather_adjs(weather, scale=1.0)
    raw = base + away_sp_adj + home_sp_adj + away_bp_adj + home_bp_adj + w_adj + t_adj
    return {
        "total": round(raw * pf, 1), "base": base,
        "away_era": away_era, "away_recent": away_recent, "away_src": away_src,
        "home_era": home_era, "home_recent": home_recent, "home_src": home_src,
        "away_sp_adj": away_sp_adj, "home_sp_adj": home_sp_adj,
        "away_bp_era": away_bp_era, "home_bp_era": home_bp_era,
        "away_bp_adj": away_bp_adj, "home_bp_adj": home_bp_adj,
        "wind_adj": w_adj, "temp_adj": t_adj,
    }

def model_to_prob(model_total, line):
    prob = 50 + ((model_total - line) * 8)
    return int(round(max(20, min(80, prob))))

def calc_kelly(edge):
    bet_pct = min((edge / 1.0) * KELLY_FRACTION, MAX_BET_PCT)
    return round(bet_pct * 100, 1), round(BANKROLL * bet_pct, 2)

def signal_boxes(model_total, line, price_cents, game_id, prefix, away, home,
                 away_pitcher, home_pitcher, market_type, today):
    auto_prob = model_to_prob(model_total, line)
    implied = price_cents / 100
    over_edge = (auto_prob / 100) - implied
    under_edge = (1 - auto_prob / 100) - (1 - implied)

    col_o, col_u = st.columns(2)
    with col_o:
        e = round(over_edge * 100, 1)
        if over_edge >= EDGE_THRESHOLD:
            _, bet_amt = calc_kelly(over_edge)
            st.success(f"🟢 **OVER**\nEdge: +{e}% | Kelly: ${bet_amt}")
            if supabase_connected:
                if st.button(f"📝 Log {prefix} OVER", key=f"log_{prefix}_over_{game_id}"):
                    if save_bet(today, away, home, away_pitcher, home_pitcher,
                                model_total, line, price_cents, auto_prob, auto_prob,
                                over_edge, "OVER", bet_amt, market_type, game_id):
                        st.success("Logged!")
        else:
            st.info(f"⚪ **OVER**\nEdge: {e}%")
    with col_u:
        e = round(under_edge * 100, 1)
        if under_edge >= EDGE_THRESHOLD:
            _, bet_amt = calc_kelly(under_edge)
            st.success(f"🔴 **UNDER**\nEdge: +{e}% | Kelly: ${bet_amt}")
            if supabase_connected:
                if st.button(f"📝 Log {prefix} UNDER", key=f"log_{prefix}_under_{game_id}"):
                    if save_bet(today, away, home, away_pitcher, home_pitcher,
                                model_total, line, price_cents, auto_prob, auto_prob,
                                under_edge, "UNDER", bet_amt, market_type, game_id):
                        st.success("Logged!")
        else:
            st.info(f"⚪ **UNDER**\nEdge: {e}%")
    return over_edge, under_edge

def save_bet(game_date, away, home, away_pitcher, home_pitcher, model_total,
             kalshi_line, kalshi_over_price, model_prob, your_prob, edge,
             direction, bet_amt, market_type="full", game_id=None):
    try:
        supabase.table("mlb_settlements").insert({
            "game_date": game_date, "away_team": away, "home_team": home,
            "away_pitcher": away_pitcher, "home_pitcher": home_pitcher,
            "model_total": model_total, "kalshi_line": kalshi_line,
            "kalshi_over_price": kalshi_over_price, "model_prob": model_prob,
            "your_prob": your_prob, "edge": round(edge, 4),
            "bet_direction": direction, "bet_amount": bet_amt,
            "market_type": market_type, "game_id": game_id,
        }).execute()
        return True
    except Exception as e:
        st.error(f"Save error: {e}")
        return False

def fetch_final_score(game_id=None, game_date=None, away_team=None, home_team=None):
    try:
        if game_id:
            games = statsapi.schedule(game_id=int(game_id), sportId=1)
        else:
            games = statsapi.schedule(date=game_date, sportId=1)
        if not games:
            return None
        for g in games:
            if not game_id:
                if not (away_team and (away_team.lower() in g.get('away_name','').lower() or
                        g.get('away_name','').lower() in away_team.lower())):
                    continue
                if not (home_team and (home_team.lower() in g.get('home_name','').lower() or
                        g.get('home_name','').lower() in home_team.lower())):
                    continue
            status = g.get('status', '')
            if not any(s.lower() in status.lower() for s in ['final', 'game over', 'completed']):
                return None
            ar, hr = g.get('away_score'), g.get('home_score')
            if ar is None or hr is None:
                return None
            return int(ar), int(hr), int(ar) + int(hr)
        return None
    except Exception as e:
        st.warning(f"Settlement fetch error (game_id={game_id}): {e}")
        return None

def settle_result(actual_total, kalshi_line, bet_direction, bet_amount, kalshi_over_price):
    if actual_total == kalshi_line:
        return "PUSH", 0.0
    won = actual_total > kalshi_line if bet_direction == "OVER" else actual_total < kalshi_line
    price = kalshi_over_price / 100 if bet_direction == "OVER" else 1 - (kalshi_over_price / 100)
    if won:
        return "WIN", round(bet_amount * ((1 / price) - 1), 2)
    return "LOSS", -round(bet_amount, 2)

def run_auto_settlement():
    if not supabase_connected:
        return
    today_str = datetime.today().strftime('%Y-%m-%d')
    try:
        resp = supabase.table("mlb_settlements").select("*") \
            .is_("actual_total", "null").lt("game_date", today_str).execute()
    except Exception:
        return
    rows = resp.data or []
    if not rows:
        return
    settled, skipped = 0, 0
    progress = st.empty()
    progress.info(f"⏳ Auto-settling {len(rows)} unsettled bet(s)…")
    for row in rows:
        score = fetch_final_score(game_id=row.get("game_id"), game_date=row.get("game_date"),
                                   away_team=row.get("away_team"), home_team=row.get("home_team"))
        if not score:
            skipped += 1
            continue
        ar, hr, actual = score
        result, pnl = settle_result(actual, row.get("kalshi_line"), row.get("bet_direction"),
                                     row.get("bet_amount", 0), row.get("kalshi_over_price", 50))
        try:
            supabase.table("mlb_settlements").update({
                "actual_total": actual, "away_score": ar, "home_score": hr,
                "result": result, "profit_loss": pnl,
                "settled_at": datetime.utcnow().isoformat(),
            }).eq("id", row["id"]).execute()
            settled += 1
        except Exception:
            skipped += 1
    msg = f"✅ Auto-settlement: {settled} settled"
    if skipped:
        msg += f", {skipped} skipped"
    progress.success(msg) if settled or skipped else progress.empty()

# ── Kalshi line fetchers ──────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def fetch_kalshi_lines():
    if not supabase_connected:
        return {"**error**": "Supabase not connected"}
    try:
        today = datetime.today().strftime('%Y-%m-%d')
        resp = supabase.table("kalshi_lines").select("*").eq("game_date", today).execute()
        rows = resp.data or []
        result = {}
        for row in rows:
            away = (row.get("away_team") or "").lower()
            home = (row.get("home_team") or "").lower()
            mtype = (row.get("market_type") or "full").lower()
            if not away or not home:
                continue
            result[(away, home, mtype)] = {
                "line": float(row.get("line", 8.5)),
                "over_price_cents": int(row.get("over_price_cents", 50)),
                "ticker": row.get("ticker", ""),
            }
        if not result:
            return {"**error**": f"No lines for {today} — trigger Edge Function"}
        return result
    except Exception as e:
        return {"**error**": str(e)}

@st.cache_data(ttl=300)
def fetch_odds_lines():
    try:
        api_key = get_secret("ODDS_API_KEY")
        if not api_key:
            return {}
        resp = requests.get("https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/",
            params={"apiKey": api_key, "regions": "us", "markets": "totals",
                    "oddsFormat": "american", "dateFormat": "iso"}, timeout=10)
        if resp.status_code != 200:
            return {}
        result = {}
        for game in resp.json():
            away = game.get("away_team", "").lower()
            home = game.get("home_team", "").lower()
            totals = []
            for bm in game.get("bookmakers", []):
                for mkt in bm.get("markets", []):
                    if mkt.get("key") != "totals":
                        continue
                    for oc in mkt.get("outcomes", []):
                        if oc.get("name") == "Over":
                            totals.append({"total": oc.get("point"), "odds": oc.get("price")})
            if totals:
                s = sorted(totals, key=lambda x: x["total"])
                m = s[len(s) // 2]
                result[(away, home)] = {"total": m["total"], "over_odds": m["odds"]}
        return result
    except Exception as e:
        st.warning(f"⚠️ Odds API: {e}")
        return {}

def match_kalshi(away, home, lines, mtype="full"):
    for (ka, kh, kt), data in lines.items():
        if kt != mtype:
            continue
        if (ka in away.lower() or away.lower() in ka) and (kh in home.lower() or home.lower() in kh):
            return data
    return None

def match_odds(away, home, lines):
    for (ka, kh), data in lines.items():
        if (ka in away.lower() or away.lower() in ka) and (kh in home.lower() or home.lower() in kh):
            return data
    return None

# ── App startup ───────────────────────────────────────────────────────────────

run_auto_settlement()

kalshi_lines = fetch_kalshi_lines()
odds_lines = fetch_odds_lines()

_kalshi_error = kalshi_lines.pop("**error**", None) if isinstance(kalshi_lines, dict) else None
full_ct = sum(1 for k in kalshi_lines if k[2] == "full") if kalshi_lines else 0
f5_ct = sum(1 for k in kalshi_lines if k[2] == "f5") if kalshi_lines else 0
kalshi_status = (f"✅ Kalshi: {full_ct} full game, {f5_ct} F5 loaded"
                 if kalshi_lines else f"⚠️ Kalshi: {_kalshi_error or 'unavailable'}")
odds_status = f"✅ Odds API: {len(odds_lines)} game(s)" if odds_lines else "⚠️ Odds API unavailable"

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab1, tab2 = st.tabs(["Today's Games", "Settlement Tracker"])

with tab1:
    try:
        today = datetime.today().strftime('%Y-%m-%d')
        schedule = statsapi.schedule(date=today)
        if not schedule:
            st.warning("No games scheduled today.")
        else:
            # Summary table
            rows = []
            for g in schedule:
                try:
                    _home, _away = g['home_name'], g['away_name']
                    _hp = g.get('home_probable_pitcher', 'TBD')
                    _ap = g.get('away_probable_pitcher', 'TBD')
                    _et = (datetime.strptime(g['game_datetime'], '%Y-%m-%dT%H:%M:%SZ')
                           - timedelta(hours=4)).strftime('%I:%M %p')
                    _pf = get_park_factor(_home)
                    _wx = fetch_stadium_weather(_home)
                    _f5 = calc_f5(_away, _home, _ap, _hp, _pf, _wx)
                    _fg = calc_fg(_away, _home, _ap, _hp, _pf, _wx)
                    _kf = match_kalshi(_away, _home, kalshi_lines, "full")
                    _k5 = match_kalshi(_away, _home, kalshi_lines, "f5")
                    _fg_line = _kf["line"] if _kf else 8.5
                    _f5_line = _k5["line"] if _k5 else 4.5
                    _odds = match_odds(_away, _home, odds_lines)
                    _pf_str = f"{_pf:.2f} {'🏔️' if _pf>=1.04 else '⬆️' if _pf>1.0 else '➡️' if _pf==1.0 else '⬇️'}"
                    _f5d = round(_f5["total"] - _f5_line, 1)
                    _fgd = round(_fg["total"] - _fg_line, 1)
                    rows.append({
                        "Time": _et,
                        "Matchup": f"{_away} @ {_home}",
                        "Away SP": _ap if _ap != 'TBD' else '❓',
                        "Home SP": _hp if _hp != 'TBD' else '❓',
                        "Park": _pf_str,
                        "F5 Model": _f5["total"],
                        "F5 Line": f"{_f5_line}{'✅' if _k5 else '~'}",
                        "F5 vs": ("🟢 " if _f5d > 0.3 else "🔴 " if _f5d < -0.3 else "⚪ ") + f"{_f5d:+.1f}",
                        "FG Model": _fg["total"],
                        "FG Line": f"{_fg_line}{'✅' if _kf else '~'}",
                        "Vegas": f"{_odds['total']}" if _odds else "—",
                        "FG vs": ("🟢 " if _fgd > 0.3 else "🔴 " if _fgd < -0.3 else "⚪ ") + f"{_fgd:+.1f}",
                    })
                except Exception:
                    continue

            if rows:
                st.subheader("📋 Today's Slate")
                c1, c2 = st.columns(2)
                with c1:
                    st.success(kalshi_status) if kalshi_lines else st.warning(kalshi_status)
                with c2:
                    st.success(odds_status) if odds_lines else st.warning(odds_status)
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                st.markdown("---")

            # Game expanders
            for game in schedule:
                try:
                    home, away = game['home_name'], game['away_name']
                    hp = game.get('home_probable_pitcher', 'TBD')
                    ap = game.get('away_probable_pitcher', 'TBD')
                    et = (datetime.strptime(game['game_datetime'], '%Y-%m-%dT%H:%M:%SZ')
                          - timedelta(hours=4)).strftime('%I:%M %p ET')
                    game_id = str(game['game_id'])
                    pf = get_park_factor(home)
                    wx = fetch_stadium_weather(home)
                    f5 = calc_f5(away, home, ap, hp, pf, wx)
                    fg = calc_fg(away, home, ap, hp, pf, wx)

                    with st.expander(f"**{away} @ {home}** — {et}"):
                        # Header
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(f"**Away:** {away}")
                            src = '🟢 Live' if f5['away_src'] == 'live' else '🟡 Fallback'
                            st.caption(f"SP: {ap} | ERA: {f5['away_era']} {src}")
                        with c2:
                            st.markdown(f"**Home:** {home}")
                            src = '🟢 Live' if f5['home_src'] == 'live' else '🟡 Fallback'
                            st.caption(f"SP: {hp} | ERA: {f5['home_era']} {src}")

                        # Park + weather row
                        c3, c4, c5 = st.columns(3)
                        with c3:
                            st.metric("🏟️ Park", pf,
                                      delta='Hitter' if pf > 1.0 else 'Pitcher' if pf < 1.0 else 'Neutral')
                        with c4:
                            if wx is None:
                                st.warning("⚠️ Weather unavailable")
                            elif wx.get("dome"):
                                st.info("🏟️ Dome")
                            else:
                                temp = wx.get("temp_f")
                                st.metric("🌡️ Temp", f"{temp}°F" if temp else "N/A")
                        with c5:
                            if wx and not wx.get("dome"):
                                ws = wx.get("wind_speed_mph", 0)
                                wd = wx.get("wind_dir_label", "")
                                st.metric("💨 Wind", f"{ws}mph {wd}" if ws else "Calm")

                        st.markdown("---")

                        # ── FIRST 5 INNINGS ───────────────────────────────────
                        st.markdown("### ⚾ First 5 Innings")
                        c6, c7, c8 = st.columns(3)
                        with c6:
                            st.metric("F5 Model", f5["total"])
                        with c7:
                            st.metric(f"Away ERA ({ap})", f5["away_era"],
                                      delta=f"Recent: {f5['away_recent']}" if f5["away_recent"] else "Season only")
                        with c8:
                            st.metric(f"Home ERA ({hp})", f5["home_era"],
                                      delta=f"Recent: {f5['home_recent']}" if f5["home_recent"] else "Season only")

                        _k5 = match_kalshi(away, home, kalshi_lines, "f5")
                        _f5_line = float(_k5["line"]) if _k5 else 4.5
                        _f5_price = int(_k5["over_price_cents"]) if _k5 else 50
                        if _k5:
                            st.success(f"✅ Kalshi F5: {_f5_line} | Over: {_f5_price}¢")
                        else:
                            st.caption("F5 Kalshi line not loaded — using default 4.5")

                        f5_line_in = st.number_input("F5 Line", 0.0, 15.0, _f5_line, 0.5, key=f"f5l_{game_id}")
                        f5_price_in = st.number_input("F5 Over Price (¢)", 1, 99, _f5_price, 1, key=f"f5p_{game_id}")
                        signal_boxes(f5["total"], f5_line_in, f5_price_in, game_id,
                                     "F5", away, home, ap, hp, "f5", today)

                        st.markdown("---")

                        # ── FULL GAME ─────────────────────────────────────────
                        st.markdown("### 🏟️ Full Game")
                        c9, c10, c11 = st.columns(3)
                        with c9:
                            st.metric("FG Model", fg["total"])
                        with c10:
                            st.metric(f"Away Bullpen ({away})", fg["away_bp_era"],
                                      delta=f"Adj: {fg['away_bp_adj']:+.2f}")
                        with c11:
                            st.metric(f"Home Bullpen ({home})", fg["home_bp_era"],
                                      delta=f"Adj: {fg['home_bp_adj']:+.2f}")

                        _kf = match_kalshi(away, home, kalshi_lines, "full")
                        _fg_line = float(_kf["line"]) if _kf else 8.5
                        _fg_price = int(_kf["over_price_cents"]) if _kf else 50
                        _game_odds = match_odds(away, home, odds_lines)
                        if _game_odds:
                            st.info(f"📊 Vegas: {_game_odds['total']} | Over odds: {_game_odds['over_odds']}")
                        if _kf:
                            st.success(f"✅ Kalshi FG: {_fg_line} | Over: {_fg_price}¢")
                        else:
                            st.caption("Full game Kalshi line not loaded — using default 8.5")

                        fg_line_in = st.number_input("FG Line", 0.0, 20.0, _fg_line, 0.5, key=f"fgl_{game_id}")
                        fg_price_in = st.number_input("FG Over Price (¢)", 1, 99, _fg_price, 1, key=f"fgp_{game_id}")
                        signal_boxes(fg["total"], fg_line_in, fg_price_in, game_id,
                                     "FG", away, home, ap, hp, "full", today)

                except Exception as ge:
                    st.warning(f"Could not load game: {ge}")
                    continue

    except Exception as e:
        st.error(f"Error: {e}")

with tab2:
    st.subheader("Settlement Tracker")
    if supabase_connected:
        try:
            data = supabase.table("mlb_settlements").select("*").order("game_date", desc=True).execute()
            if data.data:
                df = pd.DataFrame(data.data)
                settled = df[df["result"].notna()]
                if not settled.empty:
                    wins = (settled["result"] == "WIN").sum()
                    losses = (settled["result"] == "LOSS").sum()
                    pushes = (settled["result"] == "PUSH").sum()
                    pnl = settled["profit_loss"].sum()
                    wp = round(wins / (wins + losses) * 100, 1) if (wins + losses) > 0 else 0
                    m1, m2, m3, m4, m5 = st.columns(5)
                    m1.metric("Total Bets", len(settled))
                    m2.metric("Record", f"{wins}W-{losses}L-{pushes}P")
                    m3.metric("Win %", f"{wp}%")
                    m4.metric("Total P&L", f"${pnl:+.2f}")
                    m5.metric("Unsettled", len(df[df["result"].isna()]))
                    st.markdown("---")
                display_cols = [c for c in [
                    "game_date", "away_team", "home_team", "market_type",
                    "model_total", "kalshi_line", "bet_direction", "bet_amount",
                    "actual_total", "result", "profit_loss", "settled_at"
                ] if c in df.columns]
                st.dataframe(df[display_cols], use_container_width=True)
            else:
                st.info("No bets logged yet.")
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Supabase not connected.")
