import streamlit as st
import statsapi
import pandas as pd
import requests
from datetime import datetime, timedelta
from supabase import create_client
from datetime import timezone
import math

ET_OFFSET = timezone(timedelta(hours=-4))

def today_et():
    return datetime.now(ET_OFFSET).strftime('%Y-%m-%d')

def now_et():
    return datetime.now(ET_OFFSET)

st.set_page_config(page_title="MPH MLB Model", layout="wide", page_icon="⚾")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, .stApp { background-color: #080c14 !important; font-family: 'Inter', sans-serif !important; }
.mph-header {
    background: linear-gradient(135deg, #0d1f3c 0%, #0a1628 100%);
    border-bottom: 2px solid #1e90ff33; padding: 18px 24px 14px 24px;
    margin: -1rem -1rem 1.5rem -1rem; display: flex; align-items: center; justify-content: space-between;
}
.mph-title { font-size: 1.6rem; font-weight: 800; letter-spacing: -0.5px; color: #ffffff; }
.mph-title span { color: #1e90ff; }
.mph-badge {
    background: #1e90ff18; border: 1px solid #1e90ff44; color: #1e90ff;
    font-size: 0.7rem; font-weight: 700; padding: 3px 10px; border-radius: 20px;
    letter-spacing: 1px; text-transform: uppercase;
}
.mph-sub { color: #4a6080; font-size: 0.8rem; margin-top: 2px; }
.section-header {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 2px; text-transform: uppercase;
    color: #1e90ff; border-bottom: 1px solid #1e90ff22; padding-bottom: 6px; margin: 1.2rem 0 0.8rem 0;
}
div[data-testid="metric-container"] {
    background: #0d1a2d !important; border: 1px solid #1e3a5f !important;
    border-radius: 8px !important; padding: 10px 14px !important; transition: border-color 0.2s;
}
div[data-testid="metric-container"]:hover { border-color: #1e90ff66 !important; }
div[data-testid="metric-container"] label { color: #4a6080 !important; font-size: 0.7rem !important; text-transform: uppercase; letter-spacing: 1px; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #e8f0fe !important; font-size: 1.4rem !important; font-weight: 700 !important; }
details { background: #0d1a2d !important; border: 1px solid #1e3a5f !important; border-radius: 8px !important; margin-bottom: 6px !important; transition: border-color 0.2s; }
details:hover { border-color: #1e90ff55 !important; }
details summary { font-weight: 600 !important; color: #c8d8f0 !important; padding: 10px 14px !important; }
details[open] { border-color: #1e90ff55 !important; }
.mph-divider { border: none; border-top: 1px solid #1e3a5f; margin: 1rem 0; }
.stButton > button {
    background: #0d1a2d !important; border: 1px solid #1e90ff55 !important; color: #1e90ff !important;
    border-radius: 6px !important; font-weight: 600 !important; font-size: 0.85rem !important;
    width: 100% !important; transition: all 0.2s !important;
}
.stButton > button:hover { background: #1e90ff15 !important; border-color: #1e90ff !important; }
.pill-live {
    display: inline-block; background: #00cc8822; border: 1px solid #00cc8866;
    color: #00cc88; font-size: 0.65rem; font-weight: 700; padding: 2px 8px;
    border-radius: 20px; letter-spacing: 1px; text-transform: uppercase; margin-left: 8px;
}
div[data-testid="stAlert"] { border-radius: 6px !important; font-size: 0.85rem !important; }
.stDataFrame { border-radius: 8px !important; border: 1px solid #1e3a5f !important; overflow: hidden !important; }
section[data-testid="stSidebar"] { background: #080c14 !important; border-right: 1px solid #1e3a5f !important; }
section[data-testid="stSidebar"] .stMarkdown { font-size: 0.85rem !important; }
.stTabs [data-baseweb="tab-list"] { background: #0d1a2d !important; border-radius: 8px !important; padding: 4px !important; gap: 4px !important; }
.stTabs [data-baseweb="tab"] { color: #4a6080 !important; font-weight: 600 !important; border-radius: 6px !important; }
.stTabs [aria-selected="true"] { background: #1e90ff22 !important; color: #1e90ff !important; }
@media (max-width: 768px) {
    .mph-title { font-size: 1.2rem !important; }
    div[data-testid="metric-container"] { padding: 8px 10px !important; }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] { font-size: 1.1rem !important; }
    .stDataFrame { font-size: 0.72rem !important; }
    details summary { font-size: 0.85rem !important; padding: 8px 12px !important; }
}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="mph-header">
  <div>
    <div class="mph-title">⚾ MPH <span>MLB</span> Model</div>
    <div class="mph-sub">Run Totals · First 5 Innings · Full Game &nbsp;
      <span class="pill-live">● LIVE</span>
    </div>
  </div>
  <div style="text-align:right">
    <div class="mph-badge">V4.37</div>
    <div class="mph-sub" style="margin-top:4px">{now_et().strftime('%b %d, %Y')}</div>
  </div>
</div>
""", unsafe_allow_html=True)

BANKROLL = 500
EDGE_THRESHOLD = 0.08
KELLY_FRACTION = 0.5
MAX_BET_PCT = 0.05
LEAGUE_AVG_ERA = 4.20
LEAGUE_AVG_BULLPEN_ERA = 4.10
SP_INNINGS = 5.0
TOTAL_INNINGS = 9.0
F5_INNINGS = 5.0
DEFAULT_FG_LINE = 8.5
DEFAULT_F5_LINE = 4.5
SEASON_ERA_WEIGHT = 0.50
RECENT_ERA_WEIGHT = 0.50
SEASON_RPG_WEIGHT = 0.60
RECENT_RPG_WEIGHT = 0.40
MAX_TEAM_RPG = 6.5          # Cap live RPG — early season small sample protection
ERA_REGRESSION_FLOOR = 3.00  # Any ERA under 2.00 with <5 live IP gets floored here
ERA_REGRESSION_THRESHOLD = 2.00
ERA_REGRESSION_MIN_IP = 10.0  # Must have 10+ IP before trusting sub-2 ERA

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
        if val: return str(val)
    except Exception: pass
    try:
        val = st.secrets[key]
        if val: return str(val)
    except Exception: pass
    return ""

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
    "Los Angeles Dodgers": 0.92, "San Francisco Giants": 0.94, "San Diego Padres": 0.92,
}

DOME_TEAMS = {
    "Arizona Diamondbacks", "Chicago White Sox", "Houston Astros", "Miami Marlins",
    "Milwaukee Brewers", "Seattle Mariners", "Tampa Bay Rays", "Texas Rangers",
    "Toronto Blue Jays",
}

HOME_ADVANTAGE_RUNS = 0.20
HOME_ADVANTAGE_F5 = 0.10

# ── Home/Away splits — V4.37 corrections ─────────────────────────────────────
# Colorado away dramatically reduced (Coors hangover effect)
# Atlanta away reduced (2026 early underperformance)
# Dome teams away slightly reduced (struggle in outdoor parks)
TEAM_HOME_AWAY_SPLITS = {
    "Los Angeles Dodgers":   (5.4, 4.8), "Atlanta Braves":        (5.0, 4.3),  # ↓ away
    "New York Yankees":      (5.0, 4.4), "Philadelphia Phillies": (5.1, 4.7),
    "Houston Astros":        (4.9, 4.1), "New York Mets":         (4.9, 4.5),  # dome away ↓
    "Boston Red Sox":        (4.9, 4.5), "Toronto Blue Jays":     (5.0, 4.4),  # dome away ↓
    "Minnesota Twins":       (4.7, 4.3), "Detroit Tigers":        (4.6, 4.2),
    "Cleveland Guardians":   (4.5, 4.1), "Kansas City Royals":    (4.5, 4.1),
    "Seattle Mariners":      (4.4, 3.8), "San Diego Padres":      (4.6, 4.2),  # dome away ↓
    "Arizona Diamondbacks":  (4.9, 4.3), "Colorado Rockies":      (5.0, 3.5),  # ↓↓ Coors hangover
    "Cincinnati Reds":       (4.6, 4.2), "Chicago Cubs":          (4.6, 4.2),
    "Milwaukee Brewers":     (4.5, 4.0), "St. Louis Cardinals":   (4.4, 4.0),  # dome away ↓
    "Pittsburgh Pirates":    (4.2, 3.8), "Baltimore Orioles":     (4.7, 4.3),
    "Tampa Bay Rays":        (4.3, 3.7), "Texas Rangers":         (4.6, 4.0),  # dome away ↓
    "Los Angeles Angels":    (4.1, 3.7), "Oakland Athletics":     (3.9, 3.5),
    "Athletics":             (3.9, 3.5), "Chicago White Sox":     (3.8, 3.3),  # dome away ↓
    "Miami Marlins":         (4.0, 3.5), "Washington Nationals":  (4.3, 3.9),  # dome away ↓
    "San Francisco Giants":  (4.3, 3.9),
}

def get_team_home_rpg(team_name):
    for key in TEAM_HOME_AWAY_SPLITS:
        if key.lower() in team_name.lower() or team_name.lower() in key.lower():
            return TEAM_HOME_AWAY_SPLITS[key][0]
    return get_team_rpg(team_name) + HOME_ADVANTAGE_RUNS

def get_team_away_rpg(team_name):
    for key in TEAM_HOME_AWAY_SPLITS:
        if key.lower() in team_name.lower() or team_name.lower() in key.lower():
            return TEAM_HOME_AWAY_SPLITS[key][1]
    return get_team_rpg(team_name)

TEAM_HANDEDNESS_SPLITS = {
    "New York Yankees":      (0.98, 1.08), "Boston Red Sox":        (1.02, 1.05),
    "Toronto Blue Jays":     (1.01, 1.03), "Baltimore Orioles":     (0.99, 1.02),
    "Tampa Bay Rays":        (1.00, 0.97), "Cleveland Guardians":   (0.98, 1.04),
    "Minnesota Twins":       (1.02, 1.01), "Detroit Tigers":        (0.99, 1.00),
    "Kansas City Royals":    (1.00, 0.98), "Chicago White Sox":     (0.97, 0.95),
    "Houston Astros":        (1.03, 1.05), "Seattle Mariners":      (1.01, 0.98),
    "Texas Rangers":         (1.02, 1.01), "Los Angeles Angels":    (0.96, 0.98),
    "Oakland Athletics":     (0.97, 0.96), "Athletics":             (0.97, 0.96),
    "New York Mets":         (1.03, 1.04), "Philadelphia Phillies": (1.04, 1.06),
    "Atlanta Braves":        (1.05, 1.03), "Washington Nationals":  (0.98, 0.97),
    "Miami Marlins":         (0.95, 0.96), "Chicago Cubs":          (1.02, 1.03),
    "Milwaukee Brewers":     (1.01, 1.00), "St. Louis Cardinals":   (1.00, 0.99),
    "Pittsburgh Pirates":    (0.97, 0.98), "Cincinnati Reds":       (1.01, 1.02),
    "Los Angeles Dodgers":   (1.06, 1.08), "San Diego Padres":      (1.02, 1.01),
    "Arizona Diamondbacks":  (1.03, 1.04), "San Francisco Giants":  (1.00, 1.01),
    "Colorado Rockies":      (1.04, 1.02),
}

def get_handedness_factor(team_name, pitcher_hand):
    for key in TEAM_HANDEDNESS_SPLITS:
        if key.lower() in team_name.lower() or team_name.lower() in key.lower():
            rhp_factor, lhp_factor = TEAM_HANDEDNESS_SPLITS[key]
            return rhp_factor if pitcher_hand == "R" else lhp_factor
    return 1.0

REST_ERA_ADJ = {3: +0.40, 4: +0.15, 5: 0.00, 6: +0.10, 7: +0.20, 8: +0.30}

@st.cache_data(ttl=3600)
def get_rest_adj(pitcher_name, game_date_str=None):
    if not pitcher_name or pitcher_name == 'TBD':
        return 0.0, None
    try:
        results = statsapi.lookup_player(pitcher_name)
        if not results: return 0.0, None
        player_id = results[0]['id']
        logs = statsapi.player_stat_data(player_id, group='pitching', type='gameLog', sportId=1)
        if not logs or 'stats' not in logs: return 0.0, None
        starts = [g for g in logs['stats'] if g.get('gamesStarted', 0) >= 1]
        if not starts: return 0.0, None
        last_date_str = starts[-1].get('date', '')
        if not last_date_str: return 0.0, None
        last_date = datetime.strptime(last_date_str, '%Y-%m-%d')
        today = datetime.strptime(game_date_str, '%Y-%m-%d') if game_date_str else datetime.now()
        days_rest = min((today - last_date).days, 8)
        return REST_ERA_ADJ.get(days_rest, 0.0), days_rest
    except Exception:
        return 0.0, None

UMPIRE_DATA = {
    "Angel Hernandez": {"factor": 1.08, "zone": "Loose"},
    "CB Bucknor":      {"factor": 1.06, "zone": "Loose"},
    "Joe West":        {"factor": 1.05, "zone": "Loose"},
    "Dan Iassogna":    {"factor": 1.04, "zone": "Loose"},
    "Adrian Johnson":  {"factor": 1.04, "zone": "Loose"},
    "Laz Diaz":        {"factor": 1.03, "zone": "Loose"},
    "Junior Valentine":{"factor": 1.05, "zone": "Loose"},
    "Mark Carlson":    {"factor": 1.02, "zone": "Average"},
    "Phil Cuzzi":      {"factor": 1.02, "zone": "Average"},
    "Jim Reynolds":    {"factor": 1.01, "zone": "Average"},
    "Bill Miller":     {"factor": 1.00, "zone": "Average"},
    "John Tumpane":    {"factor": 1.00, "zone": "Average"},
    "Todd Tichenor":   {"factor": 1.00, "zone": "Average"},
    "David Rackley":   {"factor": 1.01, "zone": "Average"},
    "Nate Tomlinson":  {"factor": 1.00, "zone": "Average"},
    "Alex MacKay":     {"factor": 1.03, "zone": "Average"},
    "Nestor Ceja":     {"factor": 1.02, "zone": "Average"},
    "Clint Vondrak":   {"factor": 0.99, "zone": "Average"},
    "Vic Carapazza":   {"factor": 0.99, "zone": "Tight"},
    "Brian Gorman":    {"factor": 0.99, "zone": "Tight"},
    "Mike Everitt":    {"factor": 0.99, "zone": "Tight"},
    "Stu Scheurwater": {"factor": 0.98, "zone": "Tight"},
    "Ryan Additon":    {"factor": 0.98, "zone": "Tight"},
    "Larry Vanover":   {"factor": 0.98, "zone": "Tight"},
    "Tim Timmons":     {"factor": 0.98, "zone": "Tight"},
    "Chris Guccione":  {"factor": 0.97, "zone": "Tight"},
    "Brennan Miller":  {"factor": 0.97, "zone": "Tight"},
    "Marvin Hudson":   {"factor": 0.97, "zone": "Tight"},
    "Doug Eddings":    {"factor": 0.96, "zone": "Tight"},
    "James Hoye":      {"factor": 0.96, "zone": "Tight"},
    "Jeremie Rehak":   {"factor": 0.96, "zone": "Tight"},
    "Bob Davidson":    {"factor": 0.95, "zone": "Tight"},
    "Mike DiMuro":     {"factor": 0.95, "zone": "Tight"},
    "Jeff Kellogg":    {"factor": 0.95, "zone": "Tight"},
    "Jerry Meals":     {"factor": 0.94, "zone": "Tight"},
    "Tom Hallion":     {"factor": 0.94, "zone": "Tight"},
    "Sam Holbrook":    {"factor": 0.93, "zone": "Tight"},
    "Ted Barrett":     {"factor": 0.93, "zone": "Tight"},
    "Mark Wegner":     {"factor": 0.92, "zone": "Tight"},
    "Lance Barrett":   {"factor": 0.92, "zone": "Tight"},
}

def get_umpire_data(ump_name):
    if not ump_name: return 1.0, "Average"
    for key, val in UMPIRE_DATA.items():
        if key.lower() in ump_name.lower() or ump_name.lower() in key.lower():
            return val["factor"], val["zone"]
    return 1.0, "Average"

def get_umpire_factor(ump_name):
    return get_umpire_data(ump_name)[0]

@st.cache_data(ttl=3600)
def fetch_todays_umpires():
    import requests as _req
    result = {}
    try:
        resp = _req.get(
            f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today_et()}"
            f"&hydrate=officials&gameType=R", timeout=8)
        if resp.status_code != 200: return result
        for date_entry in resp.json().get('dates', []):
            for game in date_entry.get('games', []):
                gid = str(game.get('gamePk', ''))
                for official in game.get('officials', []):
                    if official.get('officialType') == 'Home Plate':
                        name = official.get('official', {}).get('fullName', '')
                        if name:
                            result[gid] = name
                            break
    except Exception:
        pass
    return result

STADIUM_ORIENTATION = {
    "Atlanta Braves":        {"cf": 22,  "lf": 337, "rf": 67},
    "Baltimore Orioles":     {"cf": 90,  "lf": 45,  "rf": 135},
    "Boston Red Sox":        {"cf": 95,  "lf": 50,  "rf": 140},
    "Chicago Cubs":          {"cf": 180, "lf": 135, "rf": 225},
    "Cincinnati Reds":       {"cf": 355, "lf": 310, "rf": 40},
    "Cleveland Guardians":   {"cf": 225, "lf": 180, "rf": 270},
    "Colorado Rockies":      {"cf": 292, "lf": 247, "rf": 337},
    "Detroit Tigers":        {"cf": 352, "lf": 307, "rf": 37},
    "Kansas City Royals":    {"cf": 30,  "lf": 345, "rf": 75},
    "Los Angeles Angels":    {"cf": 225, "lf": 180, "rf": 270},
    "Los Angeles Dodgers":   {"cf": 315, "lf": 270, "rf": 0},
    "Minnesota Twins":       {"cf": 105, "lf": 60,  "rf": 150},
    "New York Mets":         {"cf": 355, "lf": 310, "rf": 40},
    "New York Yankees":      {"cf": 225, "lf": 180, "rf": 270},
    "Oakland Athletics":     {"cf": 225, "lf": 180, "rf": 270},
    "Athletics":             {"cf": 225, "lf": 180, "rf": 270},
    "Philadelphia Phillies": {"cf": 55,  "lf": 10,  "rf": 100},
    "Pittsburgh Pirates":    {"cf": 125, "lf": 80,  "rf": 170},
    "San Diego Padres":      {"cf": 315, "lf": 270, "rf": 0},
    "San Francisco Giants":  {"cf": 115, "lf": 70,  "rf": 160},
    "St. Louis Cardinals":   {"cf": 105, "lf": 60,  "rf": 150},
    "Washington Nationals":  {"cf": 45,  "lf": 0,   "rf": 90},
}

STADIUM_CF_BEARING = {k: v["cf"] for k, v in STADIUM_ORIENTATION.items()}

STADIUM_COORDS = {
    "Arizona Diamondbacks": None, "Atlanta Braves": (33.8908, -84.4678),
    "Baltimore Orioles": (39.2838, -76.6216), "Boston Red Sox": (42.3467, -71.0972),
    "Chicago Cubs": (41.9484, -87.6553), "Chicago White Sox": None,
    "Cincinnati Reds": (39.0979, -84.5082), "Cleveland Guardians": (41.4962, -81.6852),
    "Colorado Rockies": (39.7559, -104.9942), "Detroit Tigers": (42.3390, -83.0485),
    "Houston Astros": None, "Kansas City Royals": (39.0517, -94.4803),
    "Los Angeles Angels": (33.8003, -117.8827), "Los Angeles Dodgers": (34.0739, -118.2400),
    "Miami Marlins": None, "Milwaukee Brewers": None,
    "Minnesota Twins": (44.9817, -93.2778), "New York Mets": (40.7571, -73.8458),
    "New York Yankees": (40.8296, -73.9262), "Oakland Athletics": (38.5803, -121.4994),
    "Athletics": (38.5803, -121.4994), "Philadelphia Phillies": (39.9061, -75.1665),
    "Pittsburgh Pirates": (40.4469, -80.0057), "San Diego Padres": (32.7073, -117.1566),
    "San Francisco Giants": (37.7786, -122.3893), "Seattle Mariners": None,
    "St. Louis Cardinals": (38.6226, -90.1928), "Tampa Bay Rays": None,
    "Texas Rangers": None, "Toronto Blue Jays": None,
    "Washington Nationals": (38.8730, -77.0074),
}

PITCHER_ERA_FALLBACK = {
    "Tarik Skubal": 0.69, "Chase Burns": 0.82, "Cristopher Sanchez": 1.65,
    "Rhett Lowder": 1.64, "Cam Schlittler": 1.62, "Trevor Rogers": 1.89,
    "Bryan Woo": 1.50, "Garrett Crochet": 2.59, "Yoshinobu Yamamoto": 2.49,
    "Bryce Elder": 2.50, "Cade Cavalli": 2.51, "Spencer Schwellenbach": 3.00,
    "Cade Horton": 2.67, "Nick Pivetta": 2.87, "Ryan Weathers": 2.81,
    "Spencer Springs": 3.20, "Javier Assad": 3.20, "Logan Webb": 3.12,
    "Will Warren": 3.07, "Corbin Burnes": 3.22, "Max Fried": 3.25,
    "Zack Wheeler": 3.18, "Hunter Brown": 3.18, "Framber Valdez": 3.66,
    "Freddy Peralta": 3.40, "Logan Gilbert": 3.40, "Andrew Abbott": 3.42,
    "Dylan Cease": 3.38, "Luis Castillo": 3.50, "Kevin Gausman": 3.45,
    "Paul Skenes": 3.50, "Kodai Senga": 3.50, "Cole Ragans": 3.50,
    "Sandy Alcantara": 3.50, "George Kirby": 3.60, "Shane Bieber": 3.60,
    "Colin Rea": 3.60, "Roki Sasaki": 3.70, "Mitch Keller": 3.91,
    "Jameson Taillon": 3.68, "Michael King": 3.75, "Joe Ryan": 3.85,
    "Zac Gallen": 3.85, "Shane McClanahan": 3.86, "Landen Roupp": 3.80,
    "Clay Holmes": 3.80, "Yu Darvish": 3.80, "Jack Leiter": 3.80,
    "Sonny Gray": 3.80, "Ranger Suarez": 3.80, "MacKenzie Gore": 3.90,
    "Bailey Ober": 3.90, "Konnor Griffin": 3.90, "Lance McCullers Jr.": 3.90,
    "Chris Bassitt": 4.00, "Jesus Luzardo": 4.10, "Michael Wacha": 4.10,
    "Merrill Kelly": 4.10, "Tanner Bibee": 4.24, "Gavin Williams": 3.92,
    "Reese Olson": 4.15, "Jared Jones": 4.20, "Nestor Cortes": 4.20,
    "Edward Cabrera": 4.20, "Parker Messick": 4.20, "Ryne Nelson": 4.20,
    "Bryce Miller": 4.20, "Aaron Nola": 4.20, "J.T. Ginn": 4.20,
    "Brandon Pfaadt": 4.20, "Emmet Sheehan": 4.20, "Mike Burrows": 4.20,
    "Brandon Williamson": 4.20, "Kris Bubic": 4.20, "Shane Baz": 4.20,
    "Jacob Lopez": 4.20, "Tylor Megill": 4.30, "Braxton Garrett": 4.30,
    "Paul Blackburn": 4.30, "Dustin May": 4.30, "Braxton Ashcraft": 4.30,
    "Kyle Harrison": 4.30, "Casey Mize": 4.30, "Nick Martinez": 4.40,
    "Matthew Liberatore": 4.40, "Hayden Wesneski": 4.40, "Erick Fedde": 4.40,
    "Jack Kochanowicz": 4.40, "Simeon Woods Richardson": 4.40, "Slade Cecconi": 4.40,
    "Martin Perez": 4.40, "Charlie Morton": 4.40, "Eric Lauer": 4.35,
    "Emerson Hancock": 4.50, "Chris Paddack": 4.55, "Jose Quintana": 4.50,
    "Aaron Civale": 4.50, "Jared Bubic": 4.50, "Carlos Rodon": 4.50,
    "Taijuan Walker": 4.50, "Steven Matz": 4.50, "Chad Patrick": 4.50,
    "Kyle Leahy": 4.50, "Keider Montero": 4.50, "Graham Ashcraft": 4.55,
    "Patrick Detmers": 4.60, "Jake Irvin": 4.60, "Dane Dunning": 4.60,
    "Davis Martin": 4.60, "Kyle Freeland": 4.65, "Ryan Feltner": 4.70,
    "Foster Griffin": 4.70, "Jose Suarez": 4.70, "Walker Buehler": 4.80,
    "Robbie Ray": 4.80, "Connelly Early": 4.80, "Janson Junk": 4.80,
    "Luis Severino": 4.88, "Patrick Corbin": 5.20, "German Marquez": 5.00,
    "Miles Mikolas": 6.50, "Yusei Kikuchi": 6.76, "Jake Abel": 6.08,
}

PITCHER_HAND = {
    "Paul Skenes": "R", "Tarik Skubal": "L", "Yoshinobu Yamamoto": "R",
    "Cristopher Sanchez": "L", "Chase Burns": "R", "Garrett Crochet": "L",
    "Cam Schlittler": "R", "Rhett Lowder": "L", "Logan Webb": "R",
    "Corbin Burnes": "R", "Max Fried": "L", "Zack Wheeler": "R",
    "Framber Valdez": "L", "Freddy Peralta": "R", "Dylan Cease": "R",
    "Luis Castillo": "R", "Kevin Gausman": "R", "Hunter Brown": "R",
    "George Kirby": "R", "Bryan Woo": "R", "Michael King": "R",
    "MacKenzie Gore": "L", "Ranger Suarez": "L", "Sandy Alcantara": "R",
    "Roki Sasaki": "R", "Joe Ryan": "R", "Bailey Ober": "R",
    "Tanner Bibee": "R", "Zac Gallen": "R", "Gavin Williams": "R",
    "Shane Bieber": "R", "Luis Severino": "R", "Andrew Abbott": "L",
    "Reese Olson": "R", "Jared Jones": "R", "Nestor Cortes": "L",
    "Edward Cabrera": "R", "Emerson Hancock": "R", "Kyle Harrison": "L",
    "Nick Martinez": "R", "Eric Lauer": "L", "Chris Paddack": "R",
    "Walker Buehler": "R", "Braxton Garrett": "L", "Matthew Liberatore": "L",
    "Trevor Rogers": "L", "Robbie Ray": "L", "Jake Irvin": "R",
    "Carlos Rodon": "L", "Kyle Freeland": "L", "Cade Cavalli": "R",
    "Konnor Griffin": "R", "Jesus Luzardo": "L", "Jose Suarez": "L",
    "Aaron Civale": "R", "Bryce Miller": "R", "Tylor Megill": "R",
    "Jose Quintana": "L", "Charlie Morton": "R", "Dane Dunning": "R",
    "Graham Ashcraft": "R", "Hayden Wesneski": "R", "Yu Darvish": "R",
    "Mitch Keller": "R", "Jameson Taillon": "R", "Shane McClanahan": "L",
    "Sonny Gray": "R", "Will Warren": "R", "Yusei Kikuchi": "L",
    "Ryne Nelson": "R", "Javier Assad": "R", "Mike Burrows": "R",
    "Janson Junk": "R", "Casey Mize": "R", "Brandon Williamson": "L",
    "Erick Fedde": "R", "Michael Wacha": "R", "Foster Griffin": "L",
    "Chris Bassitt": "R", "Brandon Pfaadt": "R", "Taijuan Walker": "R",
    "Landen Roupp": "R", "Bryce Elder": "R", "Jack Leiter": "R",
    "Lance McCullers Jr.": "R", "Kodai Senga": "R", "Clay Holmes": "R",
    "Braxton Ashcraft": "R", "Jacob Lopez": "R", "Martin Perez": "L",
    "Paul Blackburn": "R", "Steven Matz": "L", "Simeon Woods Richardson": "R",
    "Jared Bubic": "L", "Frankie Montas": "R", "Parker Messick": "L",
    "Logan Gilbert": "R", "Nick Pivetta": "R", "Cole Ragans": "L",
    "Spencer Schwellenbach": "R", "Cade Horton": "R", "Miles Mikolas": "R",
    "Aaron Nola": "R", "Merrill Kelly": "R", "Patrick Detmers": "L",
    "Ryan Weathers": "L", "Spencer Springs": "R", "Jake Abel": "R",
    "Colin Rea": "R",
}

LINEUP_LHH_PCT = {
    "New York Yankees": 0.52, "Boston Red Sox": 0.48, "Toronto Blue Jays": 0.44,
    "Baltimore Orioles": 0.42, "Tampa Bay Rays": 0.45, "Cleveland Guardians": 0.43,
    "Minnesota Twins": 0.46, "Detroit Tigers": 0.41, "Kansas City Royals": 0.44,
    "Chicago White Sox": 0.40, "Houston Astros": 0.47, "Seattle Mariners": 0.43,
    "Texas Rangers": 0.45, "Los Angeles Angels": 0.42, "Oakland Athletics": 0.41,
    "Athletics": 0.41, "New York Mets": 0.46, "Philadelphia Phillies": 0.48,
    "Atlanta Braves": 0.44, "Washington Nationals": 0.43, "Miami Marlins": 0.42,
    "Chicago Cubs": 0.47, "Milwaukee Brewers": 0.45, "St. Louis Cardinals": 0.44,
    "Pittsburgh Pirates": 0.43, "Cincinnati Reds": 0.44, "Los Angeles Dodgers": 0.50,
    "San Diego Padres": 0.46, "Arizona Diamondbacks": 0.45, "San Francisco Giants": 0.47,
    "Colorado Rockies": 0.43,
}

def get_lineup_lhh_pct(team_name):
    for key in LINEUP_LHH_PCT:
        if key.lower() in team_name.lower() or team_name.lower() in key.lower():
            return LINEUP_LHH_PCT[key]
    return 0.44

def platoon_adj(pitcher_name, opposing_team):
    hand = PITCHER_HAND.get(pitcher_name)
    if not hand: return 0.0
    lhh_pct = get_lineup_lhh_pct(opposing_team)
    NEUTRAL_LHH = 0.44
    if hand == "R":
        deviation = lhh_pct - NEUTRAL_LHH
    else:
        deviation = (1 - lhh_pct) - (1 - NEUTRAL_LHH)
    return round(-deviation * 2.0, 2)

TEAM_RUNS_FALLBACK = {
    "New York Yankees": 4.7, "Boston Red Sox": 4.7, "Toronto Blue Jays": 4.8,
    "Baltimore Orioles": 4.5, "Tampa Bay Rays": 4.1, "Cleveland Guardians": 4.3,
    "Minnesota Twins": 4.5, "Detroit Tigers": 4.4, "Kansas City Royals": 4.3,
    "Chicago White Sox": 3.6, "Houston Astros": 4.6, "Seattle Mariners": 4.2,
    "Texas Rangers": 4.4, "Los Angeles Angels": 3.9, "Oakland Athletics": 3.7,
    "Athletics": 3.7, "New York Mets": 4.7, "Philadelphia Phillies": 4.9,
    "Atlanta Braves": 4.8, "Washington Nationals": 4.1, "Miami Marlins": 3.8,
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

@st.cache_data(ttl=3600)
def fetch_live_team_stats():
    import requests as _req
    rpg, bullpen_era = {}, {}
    season = datetime.today().year
    try:
        teams_resp = _req.get(
            f"https://statsapi.mlb.com/api/v1/teams?sportId=1&season={season}", timeout=10)
        if teams_resp.status_code != 200: return rpg, bullpen_era
        for team in teams_resp.json().get('teams', []):
            team_id = team.get('id')
            team_name = team.get('name', '')
            if not team_id or not team_name: continue
            try:
                h_resp = _req.get(
                    f"https://statsapi.mlb.com/api/v1/teams/{team_id}/stats"
                    f"?stats=season&group=hitting&season={season}&sportId=1", timeout=8)
                if h_resp.status_code == 200:
                    for sg in h_resp.json().get('stats', []):
                        splits = sg.get('splits', [])
                        if splits:
                            stat = splits[0].get('stat', {})
                            runs = int(stat.get('runs', 0) or 0)
                            gp = int(stat.get('gamesPlayed', 0) or 0)
                            if gp >= 5 and runs > 0:
                                # Cap RPG at MAX_TEAM_RPG — early season protection
                                rpg[team_name] = min(round(runs / gp, 2), MAX_TEAM_RPG)
            except Exception: pass
            try:
                p_resp = _req.get(
                    f"https://statsapi.mlb.com/api/v1/teams/{team_id}/stats"
                    f"?stats=season&group=pitching&season={season}&sportId=1", timeout=8)
                if p_resp.status_code == 200:
                    for sg in p_resp.json().get('stats', []):
                        splits = sg.get('splits', [])
                        if splits:
                            stat = splits[0].get('stat', {})
                            era_val = stat.get('era')
                            gp = int(stat.get('gamesPlayed', 0) or 0)
                            if era_val and gp >= 5:
                                bullpen_era[team_name] = round(float(era_val) * 1.08, 2)
            except Exception: pass
    except Exception: pass
    return rpg, bullpen_era

@st.cache_data(ttl=3600)
def fetch_live_sp_era(pitcher_name):
    if not pitcher_name or pitcher_name == 'TBD':
        return LEAGUE_AVG_ERA, 'default'
    try:
        results = statsapi.lookup_player(pitcher_name)
        if not results: raise ValueError("Not found")
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
                        era_val = round(float(era), 2)
                        # ERA regression: if ERA < threshold and IP < min, floor it
                        if era_val < ERA_REGRESSION_THRESHOLD and ip < ERA_REGRESSION_MIN_IP:
                            era_val = ERA_REGRESSION_FLOOR
                        return era_val, 'live'
    except Exception: pass
    era_fb = None
    for key in PITCHER_ERA_FALLBACK:
        if key.lower() in pitcher_name.lower() or pitcher_name.lower() in key.lower():
            era_fb = PITCHER_ERA_FALLBACK[key]
            break
    if era_fb is not None:
        # Also apply regression floor to fallback values
        if era_fb < ERA_REGRESSION_THRESHOLD:
            era_fb = ERA_REGRESSION_FLOOR
        return era_fb, 'fallback'
    return LEAGUE_AVG_ERA, 'default'

@st.cache_data(ttl=3600)
def fetch_recent_era(pitcher_name):
    if not pitcher_name or pitcher_name == 'TBD': return None
    try:
        results = statsapi.lookup_player(pitcher_name)
        if not results: return None
        player_id = results[0]['id']
        logs = statsapi.player_stat_data(player_id, group='pitching', type='gameLog', sportId=1)
        if not logs or 'stats' not in logs: return None
        starts = [g for g in logs['stats'] if g.get('gamesStarted', 0) >= 1][-3:]
        if not starts: return None
        total_er = sum(float(g.get('earnedRuns', 0)) for g in starts)
        total_ip = sum(float(g.get('inningsPitched', 0)) for g in starts)
        if total_ip < 3: return None
        recent = round((total_er / total_ip) * 9, 2)
        # Apply regression floor to recent ERA too
        if recent < ERA_REGRESSION_THRESHOLD and total_ip < ERA_REGRESSION_MIN_IP:
            recent = ERA_REGRESSION_FLOOR
        return recent
    except Exception: return None

WIND_DIR_LABELS = {
    0: "N", 23: "NNE", 45: "NE", 68: "ENE", 90: "E", 113: "ESE",
    135: "SE", 158: "SSE", 180: "S", 203: "SSW", 225: "SW", 248: "WSW",
    270: "W", 293: "WNW", 315: "NW", 338: "NNW", 360: "N"
}

def deg_to_label(deg):
    if deg is None: return ""
    return WIND_DIR_LABELS[min(WIND_DIR_LABELS.keys(), key=lambda x: abs(x - deg))]

def wind_direction_label(wind_dir_deg, home_team):
    orient = None
    for key, val in STADIUM_ORIENTATION.items():
        if key.lower() in home_team.lower() or home_team.lower() in key.lower():
            orient = val
            break
    if orient is None: return None
    cf, lf, rf = orient["cf"], orient["lf"], orient["rf"]

    def angle_diff(a, b):
        diff = abs(a - b) % 360
        return min(diff, 360 - diff)

    home_plate = (cf + 180) % 360
    THRESHOLD = 35

    if angle_diff(wind_dir_deg, cf) <= THRESHOLD: return "Out to CF"
    if angle_diff(wind_dir_deg, lf) <= THRESHOLD: return "Out to LF"
    if angle_diff(wind_dir_deg, rf) <= THRESHOLD: return "Out to RF"
    if angle_diff(wind_dir_deg, home_plate) <= THRESHOLD: return "In from CF"
    if angle_diff(wind_dir_deg, (lf + 180) % 360) <= THRESHOLD: return "In from LF"
    if angle_diff(wind_dir_deg, (rf + 180) % 360) <= THRESHOLD: return "In from RF"

    lf_side = (lf + cf) / 2 % 360
    rf_side = (rf + cf) / 2 % 360
    if angle_diff(wind_dir_deg, lf_side) < angle_diff(wind_dir_deg, rf_side):
        return "L→R"
    return "R→L"

@st.cache_data(ttl=1800)
def fetch_stadium_weather(home_team, game_hour_utc=None):
    coords = STADIUM_COORDS.get(home_team)
    if coords is None: return {"dome": True}
    lat, lon = coords
    try:
        resp = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon,
            "hourly": "temperature_2m,windspeed_10m,winddirection_10m,precipitation_probability",
            "temperature_unit": "fahrenheit", "windspeed_unit": "mph",
            "forecast_days": 1, "timezone": "auto",
        }, timeout=8)
        if resp.status_code != 200: return None
        hourly = resp.json().get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        wspeeds = hourly.get("windspeed_10m", [])
        wdirs = hourly.get("winddirection_10m", [])
        precip_probs = hourly.get("precipitation_probability", [])
        if not times: return None
        target_hour = game_hour_utc if game_hour_utc else datetime.utcnow().hour
        best_idx = 0
        for i, t in enumerate(times):
            try:
                if int(t.split("T")[1][:2]) <= target_hour:
                    best_idx = i
            except Exception: continue
        temp = temps[best_idx] if temps else None
        wspeed = wspeeds[best_idx] if wspeeds else
