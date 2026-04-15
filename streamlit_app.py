import streamlit as st
import statsapi
import pandas as pd
import requests
from datetime import datetime, timedelta
from supabase import create_client
from datetime import timezone

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
    <div class="mph-badge">V4.33</div>
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

# ── V4.33 #1: Early season ERA blend — 50/50 recent vs season ────────────────
SEASON_ERA_WEIGHT = 0.50
RECENT_ERA_WEIGHT = 0.50
# RPG blend — 60/40 (recent team form matters but season sample larger)
SEASON_RPG_WEIGHT = 0.60
RECENT_RPG_WEIGHT = 0.40

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

HOME_ADVANTAGE_RUNS = 0.20
HOME_ADVANTAGE_F5 = 0.10

# ── V4.33 #5: Team home/away RPG splits — 2025 baseline ─────────────────────
TEAM_HOME_AWAY_SPLITS = {
    "Los Angeles Dodgers":   (5.4, 4.8), "Atlanta Braves":        (5.2, 4.8),
    "New York Yankees":      (5.0, 4.4), "Philadelphia Phillies": (5.1, 4.7),
    "Houston Astros":        (4.9, 4.3), "New York Mets":         (4.9, 4.5),
    "Boston Red Sox":        (4.9, 4.5), "Toronto Blue Jays":     (5.0, 4.6),
    "Minnesota Twins":       (4.7, 4.3), "Detroit Tigers":        (4.6, 4.2),
    "Cleveland Guardians":   (4.5, 4.1), "Kansas City Royals":    (4.5, 4.1),
    "Seattle Mariners":      (4.4, 4.0), "San Diego Padres":      (4.6, 4.2),
    "Arizona Diamondbacks":  (4.9, 4.5), "Colorado Rockies":      (5.0, 4.0),
    "Cincinnati Reds":       (4.6, 4.2), "Chicago Cubs":          (4.6, 4.2),
    "Milwaukee Brewers":     (4.5, 4.1), "St. Louis Cardinals":   (4.4, 4.0),
    "Pittsburgh Pirates":    (4.2, 3.8), "Baltimore Orioles":     (4.7, 4.3),
    "Tampa Bay Rays":        (4.3, 3.9), "Texas Rangers":         (4.6, 4.2),
    "Los Angeles Angels":    (4.1, 3.7), "Oakland Athletics":     (3.9, 3.5),
    "Athletics":             (3.9, 3.5), "Chicago White Sox":     (3.8, 3.4),
    "Miami Marlins":         (4.0, 3.6), "Washington Nationals":  (4.3, 3.9),
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

# ── V4.33 #3: Team offensive splits vs LHP/RHP — 2025 baseline ──────────────
# (runs_vs_RHP_factor, runs_vs_LHP_factor)
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

# ── V4.33 #4: Pitcher rest days ERA adjustment ────────────────────────────────
REST_ERA_ADJ = {
    3: +0.40, 4: +0.15, 5: 0.00, 6: +0.10, 7: +0.20, 8: +0.30,
}

@st.cache_data(ttl=3600)
def get_rest_adj(pitcher_name, game_date_str=None):
    if not pitcher_name or pitcher_name == 'TBD':
        return 0.0, None
    try:
        results = statsapi.lookup_player(pitcher_name)
        if not results:
            return 0.0, None
        player_id = results[0]['id']
        logs = statsapi.player_stat_data(player_id, group='pitching', type='gameLog', sportId=1)
        if not logs or 'stats' not in logs:
            return 0.0, None
        starts = [g for g in logs['stats'] if g.get('gamesStarted', 0) >= 1]
        if not starts:
            return 0.0, None
        last_date_str = starts[-1].get('date', '')
        if not last_date_str:
            return 0.0, None
        last_date = datetime.strptime(last_date_str, '%Y-%m-%d')
        today = datetime.strptime(game_date_str, '%Y-%m-%d') if game_date_str else datetime.now()
        days_rest = min((today - last_date).days, 8)
        return REST_ERA_ADJ.get(days_rest, 0.0), days_rest
    except Exception:
        return 0.0, None

# ── V4.33 Umpire factor — now wired into calculations ────────────────────────
UMPIRE_RUN_FACTOR = {
    "Angel Hernandez": 1.08, "CB Bucknor": 1.06, "Joe West": 1.05,
    "Dan Iassogna": 1.04, "Adrian Johnson": 1.04, "Laz Diaz": 1.03,
    "Mark Carlson": 1.02, "Phil Cuzzi": 1.02, "Jim Reynolds": 1.01,
    "Bill Miller": 1.00, "John Tumpane": 1.00, "Todd Tichenor": 1.00,
    "Vic Carapazza": 0.99, "Brian Gorman": 0.99, "Mike Everitt": 0.99,
    "Larry Vanover": 0.98, "Tim Timmons": 0.98, "Chris Guccione": 0.97,
    "Marvin Hudson": 0.97, "Doug Eddings": 0.96, "James Hoye": 0.96,
    "Bob Davidson": 0.95, "Mike DiMuro": 0.95, "Jeff Kellogg": 0.95,
    "Jerry Meals": 0.94, "Tom Hallion": 0.94, "Sam Holbrook": 0.93,
    "Ted Barrett": 0.93, "Mark Wegner": 0.92, "Lance Barrett": 0.92,
    "Junior Valentine": 1.05, "Alex MacKay": 1.03, "Nestor Ceja": 1.02,
    "Ryan Additon": 0.98, "Brennan Miller": 0.97, "Jeremie Rehak": 0.96,
    "Clint Vondrak": 0.99, "David Rackley": 1.01, "Nate Tomlinson": 1.00,
    "Stu Scheurwater": 0.98,
}

def get_umpire_factor(ump_name):
    if not ump_name:
        return 1.0
    for key in UMPIRE_RUN_FACTOR:
        if key.lower() in ump_name.lower() or ump_name.lower() in key.lower():
            return UMPIRE_RUN_FACTOR[key]
    return 1.0

@st.cache_data(ttl=3600)
def fetch_todays_umpires():
    import requests as _req
    result = {}
    try:
        today = today_et()
        resp = _req.get(
            f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}"
            f"&hydrate=officials&gameType=R", timeout=8)
        if resp.status_code != 200:
            return result
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

STADIUM_CF_BEARING = {
    "Atlanta Braves": 22, "Baltimore Orioles": 90, "Boston Red Sox": 95,
    "Chicago Cubs": 180, "Cincinnati Reds": 355, "Cleveland Guardians": 225,
    "Colorado Rockies": 292, "Detroit Tigers": 352, "Kansas City Royals": 30,
    "Los Angeles Angels": 225, "Los Angeles Dodgers": 315, "Minnesota Twins": 105,
    "New York Mets": 355, "New York Yankees": 225, "Oakland Athletics": 225,
    "Athletics": 225, "Philadelphia Phillies": 55, "Pittsburgh Pirates": 125,
    "San Diego Padres": 315, "San Francisco Giants": 115, "St. Louis Cardinals": 105,
    "Washington Nationals": 45,
}

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
    "Logan Webb": 3.12, "Corbin Burnes": 3.22, "Max Fried": 3.25,
    "Zack Wheeler": 3.18, "Framber Valdez": 3.66, "Freddy Peralta": 3.40,
    "Dylan Cease": 3.38, "Luis Castillo": 3.50, "Kevin Gausman": 3.45,
    "Hunter Brown": 3.18, "George Kirby": 3.60, "Michael King": 3.75,
    "MacKenzie Gore": 3.90, "Ranger Suarez": 3.80, "Sandy Alcantara": 3.50,
    "Roki Sasaki": 3.70, "Joe Ryan": 3.85, "Bailey Ober": 3.90,
    "Logan Gilbert": 3.40, "Nick Pivetta": 2.87, "Paul Skenes": 3.50,
    "Cole Ragans": 3.50, "Tanner Bibee": 4.24, "Zac Gallen": 3.85,
    "Gavin Williams": 3.92, "Shane Bieber": 3.60, "Luis Severino": 4.88,
    "Andrew Abbott": 3.42, "Reese Olson": 4.15, "Jared Jones": 4.20,
    "Nestor Cortes": 4.20, "Edward Cabrera": 4.20, "Parker Messick": 4.20,
    "Emerson Hancock": 4.50, "Kyle Harrison": 4.30, "Nick Martinez": 4.40,
    "Eric Lauer": 4.35, "Chris Paddack": 4.55, "Walker Buehler": 4.80,
    "Braxton Garrett": 4.30, "Matthew Liberatore": 4.40, "Robbie Ray": 4.80,
    "Jake Irvin": 4.60, "Carlos Rodon": 4.50, "Kyle Freeland": 4.65,
    "Patrick Corbin": 5.20, "Konnor Griffin": 3.90, "Simeon Woods Richardson": 4.40,
    "Jared Bubic": 4.50, "Jesus Luzardo": 4.10, "Jose Suarez": 4.70,
    "Aaron Civale": 4.50, "Bryce Miller": 4.20, "Tylor Megill": 4.30,
    "Jose Quintana": 4.50, "Charlie Morton": 4.40, "Dane Dunning": 4.60,
    "Graham Ashcraft": 4.55, "Hayden Wesneski": 4.40, "Yu Darvish": 3.80,
    "Mitch Keller": 3.91, "Jameson Taillon": 3.68, "Shane McClanahan": 3.86,
    "Sonny Gray": 3.80, "Spencer Schwellenbach": 3.00, "Cade Horton": 2.67,
    "Yusei Kikuchi": 6.76, "Ryne Nelson": 4.20, "Javier Assad": 3.20,
    "Mike Burrows": 4.20, "Janson Junk": 4.80, "Casey Mize": 4.30,
    "Keider Montero": 4.50, "Jack Kochanowicz": 4.40, "Brandon Williamson": 4.20,
    "Jacob Lopez": 4.60, "Erick Fedde": 4.40, "Michael Wacha": 4.10,
    "Foster Griffin": 4.70, "Kyle Leahy": 4.50, "Chris Bassitt": 4.00,
    "Shane Baz": 4.20, "Slade Cecconi": 4.40, "Davis Martin": 4.60,
    "Kris Bubic": 4.20, "Chad Patrick": 4.50, "Connelly Early": 4.80,
    "Dustin May": 4.30, "Ryan Feltner": 4.70, "German Marquez": 5.00,
    "Jack Leiter": 3.80, "Emmet Sheehan": 4.20, "Lance McCullers Jr.": 3.90,
    "Brandon Pfaadt": 4.20, "Taijuan Walker": 4.50, "Martin Perez": 4.40,
    "Paul Blackburn": 4.30, "Landen Roupp": 3.80, "Steven Matz": 4.50,
    "J.T. Ginn": 4.20, "Clay Holmes": 3.80, "Kodai Senga": 3.50,
    "Braxton Ashcraft": 4.30, "Miles Mikolas": 6.50, "Aaron Nola": 4.20,
    "Merrill Kelly": 4.10, "Patrick Detmers": 4.60, "Ryan Weathers": 2.81,
    "Spencer Springs": 3.20, "Bryce Elder": 2.50, "Will Warren": 3.07,
    "Cade Cavalli": 2.51, "Jake Abel": 6.08, "Colin Rea": 3.60,
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
    if not hand:
        return 0.0
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

@st.cache_data(ttl=3600)
def fetch_live_team_stats():
    import requests as _req
    rpg = {}
    bullpen_era = {}
    season = datetime.today().year
    try:
        teams_resp = _req.get(
            f"https://statsapi.mlb.com/api/v1/teams?sportId=1&season={season}", timeout=10)
        if teams_resp.status_code != 200:
            return rpg, bullpen_era
        for team in teams_resp.json().get('teams', []):
            team_id = team.get('id')
            team_name = team.get('name', '')
            if not team_id or not team_name:
                continue
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
                                rpg[team_name] = round(runs / gp, 2)
            except Exception:
                pass
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

WIND_DIR_LABELS = {
    0: "N", 23: "NNE", 45: "NE", 68: "ENE", 90: "E", 113: "ESE",
    135: "SE", 158: "SSE", 180: "S", 203: "SSW", 225: "SW", 248: "WSW",
    270: "W", 293: "WNW", 315: "NW", 338: "NNW", 360: "N"
}

def deg_to_label(deg):
    if deg is None: return ""
    closest = min(WIND_DIR_LABELS.keys(), key=lambda x: abs(x - deg))
    return WIND_DIR_LABELS[closest]

@st.cache_data(ttl=1800)
def fetch_stadium_weather(home_team, game_hour_utc=None):
    coords = STADIUM_COORDS.get(home_team)
    if coords is None:
        return {"dome": True}
    lat, lon = coords
    try:
        resp = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon,
            "hourly": "temperature_2m,windspeed_10m,winddirection_10m",
            "temperature_unit": "fahrenheit", "windspeed_unit": "mph",
            "forecast_days": 1, "timezone": "auto",
        }, timeout=8)
        if resp.status_code != 200: return None
        hourly = resp.json().get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        wspeeds = hourly.get("windspeed_10m", [])
        wdirs = hourly.get("winddirection_10m", [])
        if not times: return None
        target_hour = game_hour_utc if game_hour_utc else datetime.utcnow().hour
        best_idx = 0
        for i, t in enumerate(times):
            try:
                if int(t.split("T")[1][:2]) <= target_hour:
                    best_idx = i
            except Exception: continue
        temp = temps[best_idx] if temps else None
        wspeed = wspeeds[best_idx] if wspeeds else 0
        wdir = wdirs[best_idx] if wdirs else 0
        return {
            "dome": False,
            "temp_f": round(temp, 1) if temp else None,
            "wind_speed_mph": round(wspeed, 1) if wspeed else 0,
            "wind_dir_deg": round(wdir) if wdir else 0,
            "wind_dir_label": deg_to_label(wdir),
        }
    except Exception:
        return None

_live_rpg, _live_bullpen = fetch_live_team_stats()
_todays_umps = fetch_todays_umpires()

with st.sidebar:
    st.markdown('<div class="section-header">System Status</div>', unsafe_allow_html=True)
    st.markdown(f"**Supabase:** {'✅ Connected' if supabase_connected else '❌ Not connected'}")
    _odds_key = get_secret("ODDS_API_KEY")
    st.markdown(f"**Odds API:** {'✅ Loaded' if _odds_key else '❌ Missing'}")
    if _odds_key:
        st.caption(f"Prefix: {_odds_key[:6]}…")
    st.markdown("**Weather:** ✅ Open-Meteo (free)")
    st.markdown(f"**Umpires fetched:** {'✅' if _todays_umps else '⚠️'} {len(_todays_umps)} games")
    st.markdown("---")
    rpg_count = len(_live_rpg)
    bp_count = len(_live_bullpen)
    st.markdown(f"**Live RPG:** {'✅' if rpg_count >= 20 else '⚠️'} {rpg_count} teams")
    st.markdown(f"**Live Bullpen ERA:** {'✅' if bp_count >= 20 else '⚠️'} {bp_count} teams")
    st.caption("Live stats kick in after ≥5 games played.")
    st.markdown("---")
    st.markdown("**V4.33 Improvements:**")
    st.caption("✅ 50/50 ERA blend (early season)")
    st.caption("✅ Team vs LHP/RHP splits")
    st.caption("✅ Pitcher rest days wired in")
    st.caption("✅ Umpire factor wired in")
    st.caption("✅ Home/away team splits")

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
    # V4.33 #1: 50/50 blend early season
    return round(season_era * SEASON_ERA_WEIGHT + recent * RECENT_ERA_WEIGHT, 2), recent, src

@st.cache_data(ttl=3600)
def fetch_recent_team_rpg(team_name, n_games=10):
    import requests as _req
    try:
        season = datetime.today().year
        teams_resp = _req.get(
            f"https://statsapi.mlb.com/api/v1/teams?sportId=1&season={season}", timeout=8)
        if teams_resp.status_code != 200: return None
        team_id = None
        for t in teams_resp.json().get('teams', []):
            name = t.get('name', '')
            if name.lower() in team_name.lower() or team_name.lower() in name.lower():
                team_id = t['id']
                break
        if not team_id: return None
        start = (datetime.today() - timedelta(days=20)).strftime('%Y-%m-%d')
        sched_resp = _req.get(
            f"https://statsapi.mlb.com/api/v1/schedule?teamId={team_id}"
            f"&startDate={start}&endDate={today_et()}&sportId=1&gameType=R", timeout=8)
        if sched_resp.status_code != 200: return None
        games = [g for d in sched_resp.json().get('dates', [])
                 for g in d.get('games', [])
                 if g.get('status', {}).get('abstractGameState') == 'Final']
        if len(games) < 3: return None
        total_runs, count = 0, 0
        for game in games[-n_games:]:
            gid = game.get('gamePk')
            if not gid: continue
            try:
                box_resp = _req.get(
                    f"https://statsapi.mlb.com/api/v1/game/{gid}/linescore", timeout=5)
                if box_resp.status_code == 200:
                    ls = box_resp.json()
                    home_id = game.get('teams', {}).get('home', {}).get('team', {}).get('id')
                    side = 'home' if home_id == team_id else 'away'
                    total_runs += ls.get('teams', {}).get(side, {}).get('runs', 0) or 0
                    count += 1
            except Exception: continue
        return round(total_runs / count, 2) if count >= 3 else None
    except Exception:
        return None

def wind_out_factor(wind_dir_deg, home_team):
    import math
    cf_bearing = STADIUM_CF_BEARING.get(home_team)
    if cf_bearing is None: return 0.0
    angle = (wind_dir_deg - cf_bearing + 180) % 360 - 180
    return round(math.cos(math.radians(angle)), 3)

def weather_adjs(weather, home_team, scale=1.0):
    if not weather or weather.get("dome"):
        return 0.0, 0.0, None
    import math
    wspeed = weather.get("wind_speed_mph") or 0
    wdir = weather.get("wind_dir_deg") or 0
    w_adj, w_label = 0.0, None
    # V4.33: wind effect threshold raised to 8mph (was 5mph)
    if wspeed and wspeed >= 8:
        factor = wind_out_factor(wdir, home_team)
        w_adj = round(factor * (wspeed / 10) * 0.3 * scale, 2)
        if factor > 0.3: w_label = "🌬️ Blowing OUT"
        elif factor < -0.3: w_label = "🌬️ Blowing IN"
        else: w_label = "💨 Crosswind"
    temp = weather.get("temp_f")
    t_adj = 0.0
    # V4.33: temp effect starts at 60°F (was 50°F), scales more gradually
    if temp and temp < 60:
        t_adj = round((60 - temp) * -0.015 * scale, 2)
    return w_adj, t_adj, w_label

def calc_f5(away, home, away_pitcher, home_pitcher, pf, weather, game_id=None, game_date=None):
    # V4.33 #5: Use home/away specific splits instead of flat home advantage
    away_season_rpg = get_team_away_rpg(away)
    home_season_rpg = get_team_home_rpg(home)
    away_recent_rpg = fetch_recent_team_rpg(away)
    home_recent_rpg = fetch_recent_team_rpg(home)
    away_rpg_blended = (away_season_rpg * SEASON_RPG_WEIGHT + away_recent_rpg * RECENT_RPG_WEIGHT) if away_recent_rpg else away_season_rpg
    home_rpg_blended = (home_season_rpg * SEASON_RPG_WEIGHT + home_recent_rpg * RECENT_RPG_WEIGHT) if home_recent_rpg else home_season_rpg
    away_rpg = away_rpg_blended * (F5_INNINGS / TOTAL_INNINGS)
    home_rpg = home_rpg_blended * (F5_INNINGS / TOTAL_INNINGS)
    base = round(away_rpg + home_rpg, 2)

    away_era, away_recent, away_src = blend_era(away_pitcher)
    home_era, home_recent, home_src = blend_era(home_pitcher)

    # V4.33 #4: Rest days adjustment
    away_rest_adj, away_days_rest = get_rest_adj(away_pitcher, game_date)
    home_rest_adj, home_days_rest = get_rest_adj(home_pitcher, game_date)

    # Platoon adj
    away_platoon = platoon_adj(away_pitcher, home)
    home_platoon = platoon_adj(home_pitcher, away)

    # V4.33 #3: Handedness offensive splits
    away_hand = PITCHER_HAND.get(away_pitcher, "R")
    home_hand = PITCHER_HAND.get(home_pitcher, "R")
    home_bat_vs_away_pitcher = get_handedness_factor(home, away_hand)
    away_bat_vs_home_pitcher = get_handedness_factor(away, home_hand)

    away_era_adj = away_era + away_platoon + away_rest_adj
    home_era_adj = home_era + home_platoon + home_rest_adj
    away_sp_adj = round(((away_era_adj - LEAGUE_AVG_ERA) / 9) * F5_INNINGS * 0.5, 2)
    home_sp_adj = round(((home_era_adj - LEAGUE_AVG_ERA) / 9) * F5_INNINGS * 0.5, 2)

    # Apply handedness offensive factor to base RPG
    away_rpg_final = away_rpg * away_bat_vs_home_pitcher
    home_rpg_final = home_rpg * home_bat_vs_away_pitcher
    base_adj = round(away_rpg_final + home_rpg_final, 2)

    w_adj, t_adj, w_label = weather_adjs(weather, home, scale=F5_INNINGS / TOTAL_INNINGS)

    # V4.33 Umpire factor
    ump_name = _todays_umps.get(str(game_id), "") if game_id else ""
    ump_factor = get_umpire_factor(ump_name)

    raw = (base_adj + away_sp_adj + home_sp_adj + w_adj + t_adj) * ump_factor
    return {
        "total": round(raw * pf, 1), "base": base,
        "away_era": away_era, "away_recent": away_recent, "away_src": away_src,
        "home_era": home_era, "home_recent": home_recent, "home_src": home_src,
        "away_sp_adj": away_sp_adj, "home_sp_adj": home_sp_adj,
        "away_platoon": away_platoon, "home_platoon": home_platoon,
        "away_hand": away_hand, "home_hand": home_hand,
        "away_rest_adj": away_rest_adj, "away_days_rest": away_days_rest,
        "home_rest_adj": home_rest_adj, "home_days_rest": home_days_rest,
        "ump_name": ump_name, "ump_factor": ump_factor,
        "wind_adj": w_adj, "temp_adj": t_adj, "wind_label": w_label,
    }

def calc_fg(away, home, away_pitcher, home_pitcher, pf, weather, game_id=None, game_date=None):
    # V4.33 #5: Home/away splits
    away_season_rpg = get_team_away_rpg(away)
    home_season_rpg = get_team_home_rpg(home)
    away_recent_rpg = fetch_recent_team_rpg(away)
    home_recent_rpg = fetch_recent_team_rpg(home)
    away_rpg_blended = (away_season_rpg * SEASON_RPG_WEIGHT + away_recent_rpg * RECENT_RPG_WEIGHT) if away_recent_rpg else away_season_rpg
    home_rpg_blended = (home_season_rpg * SEASON_RPG_WEIGHT + home_recent_rpg * RECENT_RPG_WEIGHT) if home_recent_rpg else home_season_rpg
    base = round(away_rpg_blended + home_rpg_blended, 1)

    away_era, away_recent, away_src = blend_era(away_pitcher)
    home_era, home_recent, home_src = blend_era(home_pitcher)

    # V4.33 #4: Rest days
    away_rest_adj, away_days_rest = get_rest_adj(away_pitcher, game_date)
    home_rest_adj, home_days_rest = get_rest_adj(home_pitcher, game_date)

    away_platoon = platoon_adj(away_pitcher, home)
    home_platoon = platoon_adj(home_pitcher, away)

    # V4.33 #3: Handedness splits
    away_hand = PITCHER_HAND.get(away_pitcher, "R")
    home_hand = PITCHER_HAND.get(home_pitcher, "R")
    home_bat_vs_away_pitcher = get_handedness_factor(home, away_hand)
    away_bat_vs_home_pitcher = get_handedness_factor(away, home_hand)

    away_era_adj = away_era + away_platoon + away_rest_adj
    home_era_adj = home_era + home_platoon + home_rest_adj
    away_sp_adj = round(((away_era_adj - LEAGUE_AVG_ERA) / 9) * SP_INNINGS * 0.5, 2)
    home_sp_adj = round(((home_era_adj - LEAGUE_AVG_ERA) / 9) * SP_INNINGS * 0.5, 2)

    away_bp_era = get_bullpen_era(away)
    home_bp_era = get_bullpen_era(home)
    bp_inn = TOTAL_INNINGS - SP_INNINGS
    away_bp_adj = round(((away_bp_era - LEAGUE_AVG_BULLPEN_ERA) / 9) * bp_inn, 2)
    home_bp_adj = round(((home_bp_era - LEAGUE_AVG_BULLPEN_ERA) / 9) * bp_inn, 2)

    # Apply handedness offensive factor
    away_rpg_final = away_rpg_blended * away_bat_vs_home_pitcher
    home_rpg_final = home_rpg_blended * home_bat_vs_away_pitcher
    base_adj = round(away_rpg_final + home_rpg_final, 1)

    w_adj, t_adj, w_label = weather_adjs(weather, home, scale=1.0)

    # V4.33 Umpire factor
    ump_name = _todays_umps.get(str(game_id), "") if game_id else ""
    ump_factor = get_umpire_factor(ump_name)

    raw = (base_adj + away_sp_adj + home_sp_adj + away_bp_adj + home_bp_adj + w_adj + t_adj) * ump_factor
    return {
        "total": round(raw * pf, 1), "base": base,
        "away_era": away_era, "away_recent": away_recent, "away_src": away_src,
        "home_era": home_era, "home_recent": home_recent, "home_src": home_src,
        "away_sp_adj": away_sp_adj, "home_sp_adj": home_sp_adj,
        "away_bp_era": away_bp_era, "home_bp_era": home_bp_era,
        "away_bp_adj": away_bp_adj, "home_bp_adj": home_bp_adj,
        "away_rest_adj": away_rest_adj, "away_days_rest": away_days_rest,
        "home_rest_adj": home_rest_adj, "home_days_rest": home_days_rest,
        "ump_name": ump_name, "ump_factor": ump_factor,
        "wind_adj": w_adj, "temp_adj": t_adj, "wind_label": w_label,
    }

@st.cache_data(ttl=3600)
def poisson_over_prob(lam, line):
    import math
    k_max = int(line)
    cdf = sum((math.exp(-lam) * (lam ** k)) / math.factorial(k) for k in range(k_max + 1))
    return max(0.10, min(0.90, 1.0 - cdf))

@st.cache_data(ttl=300)
def monte_carlo_prob(model_total, line, era_uncertainty=0.40, rpg_uncertainty=0.25, n_sims=5000):
    import random
    over_count = 0
    for _ in range(n_sims):
        sim_total = max(2.0, model_total + random.gauss(0, era_uncertainty * 0.3) + random.gauss(0, rpg_uncertainty))
        if random.random() < poisson_over_prob(sim_total, line):
            over_count += 1
    return over_count / n_sims

def model_to_prob(model_total, line):
    p_final = 0.60 * monte_carlo_prob(model_total, line) + 0.40 * poisson_over_prob(model_total, line)
    return int(round(max(15, min(85, p_final * 100))))

def model_to_prob_detail(model_total, line):
    p_poisson = poisson_over_prob(model_total, line)
    p_mc = monte_carlo_prob(model_total, line)
    p_final = max(0.15, min(0.85, 0.60 * p_mc + 0.40 * p_poisson))
    return {
        "poisson": round(p_poisson * 100, 1),
        "monte_carlo": round(p_mc * 100, 1),
        "final": round(p_final * 100, 1),
    }

def calc_kelly(edge):
    bet_pct = min((edge / 1.0) * KELLY_FRACTION, MAX_BET_PCT)
    return round(bet_pct * 100, 1), round(BANKROLL * bet_pct, 2)

def signal_boxes(model_total, line, price_cents, game_id, prefix, away, home,
                 away_pitcher, home_pitcher, market_type, today):
    # V4.32: Default line protection
    _is_default = (market_type == "full" and line == DEFAULT_FG_LINE and not odds_lines) or \
                  (market_type == "f5" and line == DEFAULT_F5_LINE and not odds_lines)
    if _is_default:
        st.warning(f"⚠️ **Default line ({line}) — Odds API unavailable.** No signals until real Vegas line loads.")
        return 0.0, 0.0

    prob_detail = model_to_prob_detail(model_total, line)
    auto_prob = int(prob_detail["final"])
    implied = price_cents / 100
    over_edge = (auto_prob / 100) - implied
    under_edge = (1 - auto_prob / 100) - (1 - implied)

    st.caption(
        f"🎲 Model: {prob_detail['final']}% OVER | "
        f"Poisson: {prob_detail['poisson']}% | "
        f"MC: {prob_detail['monte_carlo']}% | "
        f"Implied: {round(implied * 100, 1)}%"
    )

    col_o, col_u = st.columns(2)
    with col_o:
        e = round(over_edge * 100, 1)
        if over_edge >= EDGE_THRESHOLD:
            _, bet_amt = calc_kelly(over_edge)
            st.success(f"🟢 **OVER** | Edge: +{e}% | Kelly: ${bet_amt}")
            if supabase_connected:
                placed = st.checkbox("📍 Placed on Kalshi", key=f"placed_{prefix}_over_{game_id}")
                real_amt = None
                if placed:
                    real_amt = st.number_input("Real $ amount", min_value=1.0, max_value=500.0,
                        value=float(bet_amt), step=1.0, key=f"real_{prefix}_over_{game_id}")
                if st.button(f"📝 Log {prefix} OVER", key=f"log_{prefix}_over_{game_id}"):
                    if save_bet(today, away, home, away_pitcher, home_pitcher,
                                model_total, line, price_cents, auto_prob, auto_prob,
                                over_edge, "OVER", bet_amt, market_type, game_id):
                        st.success("Logged!")
        else:
            st.info(f"⚪ **OVER** | Edge: {e}%")
    with col_u:
        e = round(under_edge * 100, 1)
        if under_edge >= EDGE_THRESHOLD:
            _, bet_amt = calc_kelly(under_edge)
            st.success(f"🔴 **UNDER** | Edge: +{e}% | Kelly: ${bet_amt}")
            if supabase_connected:
                placed = st.checkbox("📍 Placed on Kalshi", key=f"placed_{prefix}_under_{game_id}")
                real_amt = None
                if placed:
                    real_amt = st.number_input("Real $ amount", min_value=1.0, max_value=500.0,
                        value=float(bet_amt), step=1.0, key=f"real_{prefix}_under_{game_id}")
                if st.button(f"📝 Log {prefix} UNDER", key=f"log_{prefix}_under_{game_id}"):
                    if save_bet(today, away, home, away_pitcher, home_pitcher,
                                model_total, line, price_cents, auto_prob, auto_prob,
                                under_edge, "UNDER", bet_amt, market_type, game_id):
                        st.success("Logged!")
        else:
            st.info(f"⚪ **UNDER** | Edge: {e}%")
    return over_edge, under_edge

def save_bet(game_date, away, home, away_pitcher, home_pitcher, model_total,
             kalshi_line, kalshi_over_price, model_prob, your_prob, edge,
             direction, bet_amt, market_type="full", game_id=None,
             placed_on_kalshi=False, real_amount=None):
    try:
        supabase.table("mlb_settlements").insert({
            "game_date": game_date, "away_team": away, "home_team": home,
            "away_pitcher": away_pitcher, "home_pitcher": home_pitcher,
            "model_total": model_total, "kalshi_line": kalshi_line,
            "kalshi_over_price": kalshi_over_price, "model_prob": model_prob,
            "your_prob": your_prob, "edge": round(edge, 4),
            "bet_direction": direction, "bet_amount": bet_amt,
            "market_type": market_type, "game_id": game_id,
            "placed_on_kalshi": placed_on_kalshi,
            "real_amount": real_amount if placed_on_kalshi else None,
        }).execute()
        return True
    except Exception as e:
        st.error(f"Save error: {e}")
        return False

def fetch_final_score(game_id=None, game_date=None, away_team=None, home_team=None):
    try:
        games = statsapi.schedule(game_id=int(game_id), sportId=1) if game_id else \
                statsapi.schedule(date=game_date, sportId=1)
        if not games: return None
        for g in games:
            if not game_id:
                if not (away_team and away_team.lower() in g.get('away_name','').lower()): continue
                if not (home_team and home_team.lower() in g.get('home_name','').lower()): continue
            if not any(s.lower() in g.get('status','').lower() for s in ['final','game over','completed']):
                return None
            ar, hr = g.get('away_score'), g.get('home_score')
            if ar is None or hr is None: return None
            return int(ar), int(hr), int(ar) + int(hr)
        return None
    except Exception:
        return None

def settle_result(actual_total, kalshi_line, bet_direction, bet_amount, kalshi_over_price):
    if actual_total == kalshi_line: return "PUSH", 0.0
    won = actual_total > kalshi_line if bet_direction == "OVER" else actual_total < kalshi_line
    price = kalshi_over_price / 100 if bet_direction == "OVER" else 1 - (kalshi_over_price / 100)
    return ("WIN", round(bet_amount * ((1 / price) - 1), 2)) if won else ("LOSS", -round(bet_amount, 2))

def run_auto_settlement():
    if not supabase_connected: return None
    try:
        rows = (supabase.table("mlb_settlements").select("*")
                .is_("actual_total", "null").lt("game_date", today_et()).execute().data or [])
        if not rows: return None
        settled, skipped = 0, 0
        for row in rows:
            score = fetch_final_score(game_id=row.get("game_id"), game_date=row.get("game_date"),
                                       away_team=row.get("away_team"), home_team=row.get("home_team"))
            if not score: skipped += 1; continue
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
            except Exception: skipped += 1
        msg = f"✅ Auto-settlement: {settled} settled"
        if skipped: msg += f", {skipped} skipped"
        return msg
    except Exception: return None

@st.cache_data(ttl=60)
def fetch_kalshi_lines():
    if not supabase_connected:
        return {"**error**": "Supabase not connected"}
    try:
        today = today_et()
        rows = supabase.table("kalshi_lines").select("*").eq("game_date", today).execute().data or []
        result = {}
        for row in rows:
            away = (row.get("away_team") or "").lower()
            home = (row.get("home_team") or "").lower()
            mtype = (row.get("market_type") or "full").lower()
            if not away or not home: continue
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
        if not api_key: return {}
        resp = requests.get("https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/",
            params={"apiKey": api_key, "regions": "us", "markets": "totals",
                    "oddsFormat": "american", "dateFormat": "iso"}, timeout=10)
        if resp.status_code != 200: return {}
        data = resp.json()
        if not isinstance(data, list): return {}
        result = {}
        for game in data:
            away = game.get("away_team", "").lower()
            home = game.get("home_team", "").lower()
            totals = []
            for bm in game.get("bookmakers", []):
                for mkt in bm.get("markets", []):
                    if mkt.get("key") != "totals": continue
                    for oc in mkt.get("outcomes", []):
                        if oc.get("name") == "Over":
                            totals.append({"total": oc.get("point"), "odds": oc.get("price")})
            if totals:
                m = sorted(totals, key=lambda x: x["total"])[len(totals) // 2]
                result[(away, home)] = {"total": m["total"], "over_odds": m["odds"]}
        return result
    except Exception: return {}

def match_kalshi(away, home, lines, mtype="full"):
    for (ka, kh, kt), data in lines.items():
        if kt != mtype: continue
        if (ka in away.lower() or away.lower() in ka) and (kh in home.lower() or home.lower() in kh):
            return data
    return None

def match_odds(away, home, lines):
    for (ka, kh), data in lines.items():
        if (ka in away.lower() or away.lower() in ka) and (kh in home.lower() or home.lower() in kh):
            return data
    return None

_settlement_msg = run_auto_settlement()
kalshi_lines = fetch_kalshi_lines()
odds_lines = fetch_odds_lines()

_kalshi_error = kalshi_lines.pop("**error**", None) if isinstance(kalshi_lines, dict) else None
full_ct = sum(1 for k in kalshi_lines if k[2] == "full") if kalshi_lines else 0
f5_ct = sum(1 for k in kalshi_lines if k[2] == "f5") if kalshi_lines else 0
kalshi_status = (f"✅ Kalshi: {full_ct} full game, {f5_ct} F5 loaded"
                 if kalshi_lines else f"⚠️ Kalshi: {_kalshi_error or 'unavailable'}")
odds_status = f"✅ Odds API: {len(odds_lines)} game(s)" if odds_lines else "⚠️ Odds API unavailable"

tab1, tab2, tab3 = st.tabs(["Today's Games", "Settlement Tracker", "📊 Calibration"])

with tab1:
    if _settlement_msg:
        st.success(_settlement_msg)
    try:
        today = today_et()
        schedule = statsapi.schedule(date=today)
        if not schedule:
            st.warning("No games scheduled today.")
        else:
            rows = []
            for g in schedule:
                try:
                    _home, _away = g['home_name'], g['away_name']
                    _hp = g.get('home_probable_pitcher', 'TBD')
                    _ap = g.get('away_probable_pitcher', 'TBD')
                    _et = (datetime.strptime(g['game_datetime'], '%Y-%m-%dT%H:%M:%SZ')
                           - timedelta(hours=4)).strftime('%I:%M %p')
                    _game_id = str(g['game_id'])
                    _game_date = today
                    _pf = get_park_factor(_home)
                    _game_utc_hour = datetime.strptime(g['game_datetime'], '%Y-%m-%dT%H:%M:%SZ').hour
                    _wx = fetch_stadium_weather(_home, game_hour_utc=_game_utc_hour)
                    _f5 = calc_f5(_away, _home, _ap, _hp, _pf, _wx, _game_id, _game_date)
                    _fg = calc_fg(_away, _home, _ap, _hp, _pf, _wx, _game_id, _game_date)
                    _kf = match_kalshi(_away, _home, kalshi_lines, "full")
                    _k5 = match_kalshi(_away, _home, kalshi_lines, "f5")
                    _fg_line = _kf["line"] if _kf else DEFAULT_FG_LINE
                    _f5_line = _k5["line"] if _k5 else DEFAULT_F5_LINE
                    _odds = match_odds(_away, _home, odds_lines)
                    _pf_str = f"{_pf:.2f} {'🏔️' if _pf>=1.04 else '⬆️' if _pf>1.0 else '➡️' if _pf==1.0 else '⬇️'}"
                    _f5d = round(_f5["total"] - _f5_line, 1)
                    _fgd = round(_fg["total"] - _fg_line, 1)

                    def _signal(diff, edge, line, mtype):
                        blocked = (mtype == "full" and line == DEFAULT_FG_LINE and not odds_lines) or \
                                  (mtype == "f5" and line == DEFAULT_F5_LINE and not odds_lines)
                        if blocked: return "⛔ DEFAULT LINE", "⚪"
                        lean = "OVER" if diff > 0.3 else "UNDER" if diff < -0.3 else "EVEN"
                        if lean == "EVEN" or abs(edge) < EDGE_THRESHOLD: return "⚪ NO EDGE", "⚪"
                        ep = round(abs(edge) * 100, 1)
                        tier = "🔥 HIGH" if ep >= 12 else "💪 STRONG" if ep >= 8 else "👍 LEAN"
                        direction = "🟢 OVER" if lean == "OVER" else "🔴 UNDER"
                        return tier, direction

                    _k5_price = _k5["over_price_cents"] if _k5 else 50
                    _kf_price = _kf["over_price_cents"] if _kf else 50
                    _f5_prob = model_to_prob(_f5["total"], _f5_line) / 100
                    _fg_prob = model_to_prob(_fg["total"], _fg_line) / 100
                    _f5_lean = "OVER" if _f5d > 0.3 else "UNDER" if _f5d < -0.3 else "EVEN"
                    _fg_lean = "OVER" if _fgd > 0.3 else "UNDER" if _fgd < -0.3 else "EVEN"
                    _f5_edge = (_f5_prob - _k5_price/100) if _f5_lean == "OVER" else ((1-_f5_prob) - (1-_k5_price/100))
                    _fg_edge = (_fg_prob - _kf_price/100) if _fg_lean == "OVER" else ((1-_fg_prob) - (1-_kf_price/100))
                    _f5_tier, _f5_dir = _signal(_f5d, _f5_edge, _f5_line, "f5")
                    _fg_tier, _fg_dir = _signal(_fgd, _fg_edge, _fg_line, "full")

                    def abbrev_team(n): parts = n.split(); return parts[-1] if parts else n
                    def abbrev_pitcher(n):
                        if not n or n == "TBD": return "TBD"
                        p = n.split(); return f"{p[0][0]}. {p[-1]}" if len(p) >= 2 else n

                    # Umpire display
                    _ump = _f5.get("ump_name", "")
                    _ump_factor = _f5.get("ump_factor", 1.0)
                    _ump_str = f"{_ump} ({_ump_factor:.2f})" if _ump else "Unknown"

                    rows.append({
                        "Time": _et, "Matchup": f"{abbrev_team(_away)}@{abbrev_team(_home)}",
                        "Mkt": "F5", "Model": _f5["total"],
                        "Line": f"{_f5_line}{'✅' if _k5 else '~'}",
                        "Signal": f"{_f5_dir} {_f5_tier}", "Vegas": "—",
                        "Away SP": _ap if _ap != "TBD" else "❓",
                        "Home SP": _hp if _hp != "TBD" else "❓",
                        "Park": _pf_str, "Ump": _ump_str,
                    })
                    rows.append({
                        "Time": "", "Matchup": "", "Mkt": "FG", "Model": _fg["total"],
                        "Line": f"{_fg_line}{'✅' if _kf else '~'}",
                        "Signal": f"{_fg_dir} {_fg_tier}",
                        "Vegas": f"{_odds['total']}" if _odds else "—",
                        "Away SP": "", "Home SP": "", "Park": "", "Ump": "",
                    })
                except Exception:
                    continue

            if rows:
                st.markdown("<div class='section-header'>📋 Today's Slate</div>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    st.success(kalshi_status) if kalshi_lines else st.warning(kalshi_status)
                with c2:
                    st.success(odds_status) if odds_lines else st.warning(odds_status)
                if not odds_lines:
                    st.error("⛔ Odds API unavailable — default lines in use. No bets will fire.")

                view_type = st.radio("Table view", ["📱 Mobile", "🖥️ Desktop"],
                                     horizontal=True, label_visibility="collapsed")
                df_all = pd.DataFrame(rows)
                if view_type == "📱 Mobile":
                    st.dataframe(df_all[["Time","Matchup","Mkt","Model","Line","Signal"]],
                                 use_container_width=True, hide_index=True)
                else:
                    st.dataframe(df_all[["Time","Matchup","Away SP","Home SP","Park","Ump",
                                         "Mkt","Model","Line","Vegas","Signal"]],
                                 use_container_width=True, hide_index=True)
                st.markdown("---")

            for game in schedule:
                try:
                    home, away = game['home_name'], game['away_name']
                    hp = game.get('home_probable_pitcher', 'TBD')
                    ap = game.get('away_probable_pitcher', 'TBD')
                    et = (datetime.strptime(game['game_datetime'], '%Y-%m-%dT%H:%M:%SZ')
                          - timedelta(hours=4)).strftime('%I:%M %p ET')
                    game_id = str(game['game_id'])
                    game_date = today
                    pf = get_park_factor(home)
                    _g_utc_hour = datetime.strptime(game['game_datetime'], '%Y-%m-%dT%H:%M:%SZ').hour
                    wx = fetch_stadium_weather(home, game_hour_utc=_g_utc_hour)
                    f5 = calc_f5(away, home, ap, hp, pf, wx, game_id, game_date)
                    fg = calc_fg(away, home, ap, hp, pf, wx, game_id, game_date)

                    with st.expander(f"**{away} @ {home}** — {et}"):
                        away_src = '🟢' if f5['away_src'] == 'live' else '🟡'
                        home_src = '🟢' if f5['home_src'] == 'live' else '🟡'

                        # Pitcher info with rest days
                        away_rest_str = f" | Rest: {f5['away_days_rest']}d ({f5['away_rest_adj']:+.2f} ERA)" if f5['away_days_rest'] else ""
                        home_rest_str = f" | Rest: {f5['home_days_rest']}d ({f5['home_rest_adj']:+.2f} ERA)" if f5['home_days_rest'] else ""
                        away_plat_str = f" | Platoon: {f5['away_platoon']:+.2f}" if f5['away_platoon'] != 0.0 else ""
                        home_plat_str = f" | Platoon: {f5['home_platoon']:+.2f}" if f5['home_platoon'] != 0.0 else ""

                        st.markdown(
                            f"**Away SP:** {ap} ({f5['away_hand']}HP) | ERA: {f5['away_era']} {away_src}{away_plat_str}{away_rest_str}  \n"
                            f"**Home SP:** {hp} ({f5['home_hand']}HP) | ERA: {f5['home_era']} {home_src}{home_plat_str}{home_rest_str}"
                        )

                        # Umpire display
                        ump_name = f5.get("ump_name", "")
                        ump_factor = f5.get("ump_factor", 1.0)
                        if ump_name:
                            ump_label = "🔼 Run inflator" if ump_factor > 1.01 else "🔽 Run suppressor" if ump_factor < 0.99 else "➡️ Neutral"
                            st.caption(f"👤 HP Ump: **{ump_name}** | Factor: {ump_factor:.2f} {ump_label}")
                        else:
                            st.caption("👤 HP Ump: Not yet announced")

                        # Weather
                        if wx is None: wx_str = "⚠️ Weather unavailable"
                        elif wx.get("dome"): wx_str = "🏟️ Dome — weather N/A"
                        else:
                            temp = wx.get("temp_f")
                            ws = wx.get("wind_speed_mph", 0)
                            wd = wx.get("wind_dir_label", "")
                            w_label = fg.get("wind_label") or f5.get("wind_label") or ""
                            wx_str = f"🌡️ {temp}°F | 💨 {ws}mph {wd} {w_label}" if temp else "⚠️ No temp data"

                        cA, cB = st.columns(2)
                        with cA:
                            park_label = 'Hitter' if pf > 1.0 else 'Pitcher' if pf < 1.0 else 'Neutral'
                            st.metric("🏟️ Park", pf, delta=park_label)
                        with cB:
                            st.info(wx_str)

                        st.markdown('<hr class="mph-divider">', unsafe_allow_html=True)

                        st.markdown('<div class="section-header">⚾ First 5 Innings</div>', unsafe_allow_html=True)
                        cF1, cF2 = st.columns(2)
                        with cF1:
                            st.metric("F5 Model", f5["total"])
                        with cF2:
                            st.metric(f"Away ERA ({ap})", f5["away_era"],
                                      delta=f"Recent: {f5['away_recent']}" if f5["away_recent"] else "Season only")
                        st.metric(f"Home ERA ({hp})", f5["home_era"],
                                  delta=f"Recent: {f5['home_recent']}" if f5["home_recent"] else "Season only")

                        _k5 = match_kalshi(away, home, kalshi_lines, "f5")
                        _f5_line = float(_k5["line"]) if _k5 else DEFAULT_F5_LINE
                        _f5_price = int(_k5["over_price_cents"]) if _k5 else 50
                        if _k5: st.success(f"✅ Kalshi F5: {_f5_line} | Over: {_f5_price}¢")
                        else: st.caption("F5 Kalshi line not loaded — using default 4.5")

                        f5_line_in = st.number_input("F5 Line", 0.0, 15.0, _f5_line, 0.5, key=f"f5l_{game_id}")
                        f5_price_in = st.number_input("F5 Over Price (¢)", 1, 99, _f5_price, 1, key=f"f5p_{game_id}")
                        signal_boxes(f5["total"], f5_line_in, f5_price_in, game_id,
                                     "F5", away, home, ap, hp, "f5", today)

                        st.markdown('<hr class="mph-divider">', unsafe_allow_html=True)

                        st.markdown('<div class="section-header">🏟️ Full Game</div>', unsafe_allow_html=True)
                        cG1, cG2 = st.columns(2)
                        with cG1:
                            st.metric("FG Model", fg["total"])
                        with cG2:
                            st.metric("Away Bullpen", fg["away_bp_era"],
                                      delta=f"Adj: {fg['away_bp_adj']:+.2f}")
                        st.metric("Home Bullpen", fg["home_bp_era"],
                                  delta=f"Adj: {fg['home_bp_adj']:+.2f}")

                        _kf = match_kalshi(away, home, kalshi_lines, "full")
                        _fg_line = float(_kf["line"]) if _kf else DEFAULT_FG_LINE
                        _fg_price = int(_kf["over_price_cents"]) if _kf else 50
                        _game_odds = match_odds(away, home, odds_lines)
                        if _game_odds:
                            st.info(f"📊 Vegas: {_game_odds['total']} | Over odds: {_game_odds['over_odds']}")
                        if _kf: st.success(f"✅ Kalshi FG: {_fg_line} | Over: {_fg_price}¢")
                        else: st.caption("Full game Kalshi line not loaded — using default 8.5")

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
    st.markdown('<div class="section-header">📊 Settlement Tracker</div>', unsafe_allow_html=True)
    if supabase_connected:
        try:
            data = supabase.table("mlb_settlements").select("*").order("game_date", desc=True).execute()
            if data.data:
                df = pd.DataFrame(data.data)
                view_mode = st.radio("View", ["All Model Bets", "Real Kalshi Bets Only"], horizontal=True)
                if view_mode == "Real Kalshi Bets Only":
                    if "placed_on_kalshi" in df.columns:
                        df = df[df["placed_on_kalshi"] == True]
                    else:
                        st.info("No real Kalshi bets logged yet.")
                if df.empty:
                    st.info("No bets in this view yet.")
                else:
                    settled = df[df["result"].notna()]
                    if not settled.empty:
                        wins = (settled["result"] == "WIN").sum()
                        losses = (settled["result"] == "LOSS").sum()
                        pushes = (settled["result"] == "PUSH").sum()
                        wp = round(wins / (wins + losses) * 100, 1) if (wins + losses) > 0 else 0
                        if view_mode == "Real Kalshi Bets Only" and "real_amount" in settled.columns:
                            real_pnl = 0.0
                            for _, row in settled.iterrows():
                                real_amt = row.get("real_amount") or row.get("bet_amount") or 0
                                model_amt = row.get("bet_amount") or 25
                                model_pnl = row.get("profit_loss") or 0
                                if model_amt and model_amt > 0:
                                    real_pnl += round(model_pnl * (real_amt / model_amt), 2)
                            pnl = round(real_pnl, 2)
                        else:
                            pnl = settled["profit_loss"].sum()
                        m1, m2, m3, m4, m5 = st.columns(5)
                        m1.metric("Total Bets", len(settled))
                        m2.metric("Record", f"{wins}W-{losses}L-{pushes}P")
                        m3.metric("Win %", f"{wp}%")
                        m4.metric("Total P&L", f"${pnl:+.2f}")
                        m5.metric("Unsettled", len(df[df["result"].isna()]))
                        st.markdown('<hr class="mph-divider">', unsafe_allow_html=True)

                    base_cols = ["game_date","away_team","home_team","market_type",
                                 "model_total","kalshi_line","bet_direction","bet_amount"]
                    if view_mode == "Real Kalshi Bets Only":
                        base_cols.append("real_amount")
                        if all(c in df.columns for c in ["real_amount","profit_loss","bet_amount"]):
                            df = df.copy()
                            def calc_real_pnl(row):
                                real = row.get("real_amount") or row.get("bet_amount") or 0
                                model = row.get("bet_amount") or 25
                                pnl = row.get("profit_loss") or 0
                                return round(pnl * (real / model), 2) if model > 0 else pnl
                            df["real_P&L"] = df.apply(calc_real_pnl, axis=1)
                            base_cols.append("real_P&L")
                    base_cols += ["actual_total","result","profit_loss","settled_at"]
                    display_cols = [c for c in base_cols if c in df.columns]

                    def highlight_result(row):
                        if row.get("result") == "WIN": return ["background-color: #1a3a2a"] * len(row)
                        elif row.get("result") == "LOSS": return ["background-color: #3a1a1a"] * len(row)
                        return [""] * len(row)

                    st.dataframe(df[display_cols].style.apply(highlight_result, axis=1),
                                 use_container_width=True)
            else:
                st.info("No bets logged yet.")
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Supabase not connected.")

with tab3:
    st.markdown('<div class="section-header">📊 Model Calibration Analysis</div>', unsafe_allow_html=True)
    if supabase_connected:
        try:
            data = supabase.table("mlb_settlements").select("*").execute()
            if data.data:
                df_cal = pd.DataFrame(data.data)
                settled = df_cal[df_cal["result"].notna()].copy()
                if len(settled) < 5:
                    st.info("Need at least 5 settled bets for calibration analysis.")
                else:
                    st.markdown('<div class="section-header">Overall Performance</div>', unsafe_allow_html=True)
                    wins = (settled["result"] == "WIN").sum()
                    losses = (settled["result"] == "LOSS").sum()
                    total = wins + losses
                    actual_win_rate = round(wins / total * 100, 1) if total > 0 else 0
                    if "model_prob" in settled.columns:
                        avg_model_prob = round(settled["model_prob"].mean(), 1)
                        calibration_gap = round(actual_win_rate - avg_model_prob, 1)
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Actual Win Rate", f"{actual_win_rate}%")
                        c2.metric("Avg Model Prob", f"{avg_model_prob}%")
                        c3.metric("Calibration Gap", f"{calibration_gap:+.1f}%",
                                  delta="Underconfident ✅" if calibration_gap > 2
                                  else "Overconfident ⚠️" if calibration_gap < -2 else "Well calibrated ✅")
                        c4.metric("Total Settled", total)
                    else:
                        c1, c2 = st.columns(2)
                        c1.metric("Actual Win Rate", f"{actual_win_rate}%")
                        c2.metric("Total Settled", total)
                    st.markdown('<hr class="mph-divider">', unsafe_allow_html=True)

                    st.markdown('<div class="section-header">Performance by Edge %</div>', unsafe_allow_html=True)
                    if "edge" in settled.columns:
                        settled["edge_tier"] = pd.cut(
                            settled["edge"] * 100, bins=[0, 5, 8, 12, 100],
                            labels=["LEAN (5-8%)", "STRONG (8-12%)", "HIGH (12%+)", "UNKNOWN"])
                        tier_stats = settled.groupby("edge_tier").apply(
                            lambda x: pd.Series({
                                "Bets": len(x), "Wins": (x["result"] == "WIN").sum(),
                                "Win%": f"{round((x['result']=='WIN').sum()/len(x)*100,1)}%",
                                "Avg Edge": f"{round(x['edge'].mean()*100,1)}%",
                            })
                        ).reset_index()
                        st.dataframe(tier_stats, use_container_width=True, hide_index=True)
                    st.markdown('<hr class="mph-divider">', unsafe_allow_html=True)

                    st.markdown('<div class="section-header">F5 vs Full Game</div>', unsafe_allow_html=True)
                    if "market_type" in settled.columns:
                        for mtype in ["f5", "full"]:
                            subset = settled[settled["market_type"] == mtype]
                            if len(subset) > 0:
                                w = (subset["result"] == "WIN").sum()
                                l = (subset["result"] == "LOSS").sum()
                                wr = round(w/(w+l)*100, 1) if (w+l) > 0 else 0
                                label = "First 5 Innings" if mtype == "f5" else "Full Game"
                                st.markdown(f"**{label}:** {w}W-{l}L ({wr}% win rate)")
                    st.markdown('<hr class="mph-divider">', unsafe_allow_html=True)

                    st.markdown('<div class="section-header">OVER vs UNDER</div>', unsafe_allow_html=True)
                    if "bet_direction" in settled.columns:
                        for direction in ["OVER", "UNDER"]:
                            subset = settled[settled["bet_direction"] == direction]
                            if len(subset) > 0:
                                w = (subset["result"] == "WIN").sum()
                                l = (subset["result"] == "LOSS").sum()
                                wr = round(w/(w+l)*100, 1) if (w+l) > 0 else 0
                                st.markdown(f"**{direction}:** {w}W-{l}L ({wr}% win rate)")
                    st.markdown('<hr class="mph-divider">', unsafe_allow_html=True)

                    st.markdown('<div class="section-header">Kelly Sizing</div>', unsafe_allow_html=True)
                    if actual_win_rate > 60:
                        st.success(f"✅ {actual_win_rate}% win rate — consider increasing allocation slightly")
                    elif actual_win_rate > 55:
                        st.info(f"📊 {actual_win_rate}% — solid, maintain Half Kelly")
                    elif actual_win_rate > 50:
                        st.warning(f"⚠️ {actual_win_rate}% — marginal, don't increase sizing yet")
                    else:
                        st.error(f"❌ {actual_win_rate}% — below 50%, review model inputs")
                    if len(settled) < 30:
                        st.caption(f"⚠️ Only {len(settled)} settled bets — need 30+ for meaningful calibration")
            else:
                st.info("No settled bets yet.")
        except Exception as e:
            st.error(f"Calibration error: {e}")
    else:
        st.warning("Supabase not connected.")
