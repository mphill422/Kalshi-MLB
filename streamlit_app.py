import streamlit as st
import streamlit.components.v1 as components
import statsapi
import pandas as pd
import requests
from datetime import datetime, timedelta
from supabase import create_client

st.set_page_config(page_title="MPH MLB Model", layout="wide", page_icon="⚾")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

/* ── Base ── */
html, body, .stApp {
    background-color: #080c14 !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Top header bar ── */
.mph-header {
    background: linear-gradient(135deg, #0d1f3c 0%, #0a1628 100%);
    border-bottom: 2px solid #1e90ff33;
    padding: 18px 24px 14px 24px;
    margin: -1rem -1rem 1.5rem -1rem;
    display: flex; align-items: center; justify-content: space-between;
}
.mph-title {
    font-size: 1.6rem; font-weight: 800; letter-spacing: -0.5px;
    color: #ffffff;
}
.mph-title span { color: #1e90ff; }
.mph-badge {
    background: #1e90ff18; border: 1px solid #1e90ff44;
    color: #1e90ff; font-size: 0.7rem; font-weight: 700;
    padding: 3px 10px; border-radius: 20px; letter-spacing: 1px;
    text-transform: uppercase;
}
.mph-sub {
    color: #4a6080; font-size: 0.8rem; margin-top: 2px;
}

/* ── Section headers ── */
.section-header {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase; color: #1e90ff;
    border-bottom: 1px solid #1e90ff22; padding-bottom: 6px;
    margin: 1.2rem 0 0.8rem 0;
}

/* ── Metric cards ── */
div[data-testid="metric-container"] {
    background: #0d1a2d !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
    transition: border-color 0.2s;
}
div[data-testid="metric-container"]:hover {
    border-color: #1e90ff66 !important;
}
div[data-testid="metric-container"] label {
    color: #4a6080 !important; font-size: 0.7rem !important;
    text-transform: uppercase; letter-spacing: 1px;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
    color: #e8f0fe !important; font-size: 1.4rem !important; font-weight: 700 !important;
}

/* ── Expanders ── */
details {
    background: #0d1a2d !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 8px !important;
    margin-bottom: 6px !important;
    transition: border-color 0.2s;
}
details:hover { border-color: #1e90ff55 !important; }
details summary {
    font-weight: 600 !important; color: #c8d8f0 !important;
    padding: 10px 14px !important;
}
details[open] { border-color: #1e90ff55 !important; }

/* ── Signal colors ── */
.sig-fire   { color: #ff6b35; font-weight: 700; }
.sig-strong { color: #ffd700; font-weight: 700; }
.sig-lean   { color: #00cc88; font-weight: 700; }
.sig-none   { color: #3a4a60; }

/* ── Divider ── */
.mph-divider {
    border: none; border-top: 1px solid #1e3a5f;
    margin: 1rem 0;
}

/* ── Buttons ── */
.stButton > button {
    background: #0d1a2d !important;
    border: 1px solid #1e90ff55 !important;
    color: #1e90ff !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    width: 100% !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #1e90ff15 !important;
    border-color: #1e90ff !important;
}

/* ── Status pills ── */
.pill-live {
    display: inline-block;
    background: #00cc8822; border: 1px solid #00cc8866;
    color: #00cc88; font-size: 0.65rem; font-weight: 700;
    padding: 2px 8px; border-radius: 20px; letter-spacing: 1px;
    text-transform: uppercase; margin-left: 8px;
}
.pill-warn {
    display: inline-block;
    background: #ff990022; border: 1px solid #ff990066;
    color: #ff9900; font-size: 0.65rem; font-weight: 700;
    padding: 2px 8px; border-radius: 20px; letter-spacing: 1px;
    text-transform: uppercase; margin-left: 8px;
}

/* ── Success/Warning/Info ── */
div[data-testid="stAlert"] {
    border-radius: 6px !important;
    font-size: 0.85rem !important;
}

/* ── Table ── */
.stDataFrame {
    border-radius: 8px !important;
    border: 1px solid #1e3a5f !important;
    overflow: hidden !important;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #080c14 !important;
    border-right: 1px solid #1e3a5f !important;
}
section[data-testid="stSidebar"] .stMarkdown {
    font-size: 0.85rem !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #0d1a2d !important;
    border-radius: 8px !important;
    padding: 4px !important;
    gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    color: #4a6080 !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
}
.stTabs [aria-selected="true"] {
    background: #1e90ff22 !important;
    color: #1e90ff !important;
}

/* ── Mobile ── */
@media (max-width: 768px) {
    .mph-title { font-size: 1.2rem !important; }
    div[data-testid="metric-container"] { padding: 8px 10px !important; }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        font-size: 1.1rem !important;
    }
    .stDataFrame { font-size: 0.72rem !important; }
    details summary { font-size: 0.85rem !important; padding: 8px 12px !important; }
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="mph-header">
  <div>
    <div class="mph-title">⚾ MPH <span>MLB</span> Model</div>
    <div class="mph-sub">Run Totals · First 5 Innings · Full Game &nbsp;
      <span class="pill-live">● LIVE</span>
    </div>
  </div>
  <div style="text-align:right">
    <div class="mph-badge">V4.21</div>
    <div class="mph-sub" style="margin-top:4px">{datetime.today().strftime('%b %d, %Y')}</div>
  </div>
</div>
""", unsafe_allow_html=True)

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

# Sidebar rendered after live stats load (see below)

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

# ── Stadium center field orientation — degrees from home plate toward CF ────
# Wind blowing FROM this direction = blowing OUT (increases scoring)
# Wind blowing TOWARD this direction = blowing IN (suppresses scoring)
STADIUM_CF_BEARING = {
    "Atlanta Braves":        22,    # Truist Park — CF faces NNE
    "Baltimore Orioles":     90,    # Camden Yards — CF faces E
    "Boston Red Sox":        95,    # Fenway Park — CF faces roughly E
    "Chicago Cubs":          180,   # Wrigley Field — CF faces S
    "Cincinnati Reds":       355,   # Great American — CF faces N
    "Cleveland Guardians":   225,   # Progressive Field — CF faces SW
    "Colorado Rockies":      292,   # Coors Field — CF faces WNW
    "Detroit Tigers":        352,   # Comerica Park — CF faces N
    "Kansas City Royals":    30,    # Kauffman — CF faces NNE
    "Los Angeles Angels":    225,   # Angel Stadium — CF faces SW
    "Los Angeles Dodgers":   315,   # Dodger Stadium — CF faces NW
    "Minnesota Twins":       105,   # Target Field — CF faces ESE
    "New York Mets":         355,   # Citi Field — CF faces N
    "New York Yankees":      225,   # Yankee Stadium — CF faces SW
    "Oakland Athletics":     225,   # Sutter Health — CF faces SW
    "Athletics":             225,
    "Philadelphia Phillies": 55,    # Citizens Bank — CF faces NE
    "Pittsburgh Pirates":    125,   # PNC Park — CF faces SE
    "San Diego Padres":      315,   # Petco Park — CF faces NW
    "San Francisco Giants":  115,   # Oracle Park — CF faces ESE
    "St. Louis Cardinals":   105,   # Busch Stadium — CF faces ESE
    "Washington Nationals":  45,    # Nationals Park — CF faces NE
}

# ── Stadium coordinates (lat, lon) — None = dome ─────────────────────────────
STADIUM_COORDS = {
    "Arizona Diamondbacks":  None,                    # Chase Field — dome
    "Atlanta Braves":        (33.8908, -84.4678),     # Truist Park
    "Baltimore Orioles":     (39.2838, -76.6216),     # Camden Yards
    "Boston Red Sox":        (42.3467, -71.0972),     # Fenway Park
    "Chicago Cubs":          (41.9484, -87.6553),     # Wrigley Field
    "Chicago White Sox":     None,                    # Guaranteed Rate — dome
    "Cincinnati Reds":       (39.0979, -84.5082),     # Great American Ball Park
    "Cleveland Guardians":   (41.4962, -81.6852),     # Progressive Field
    "Colorado Rockies":      (39.7559, -104.9942),    # Coors Field
    "Detroit Tigers":        (42.3390, -83.0485),     # Comerica Park
    "Houston Astros":        None,                    # Minute Maid — dome
    "Kansas City Royals":    (39.0517, -94.4803),     # Kauffman Stadium
    "Los Angeles Angels":    (33.8003, -117.8827),    # Angel Stadium
    "Los Angeles Dodgers":   (34.0739, -118.2400),    # Dodger Stadium
    "Miami Marlins":         None,                    # loanDepot Park — dome
    "Milwaukee Brewers":     None,                    # American Family — dome
    "Minnesota Twins":       (44.9817, -93.2778),     # Target Field (open air)
    "New York Mets":         (40.7571, -73.8458),     # Citi Field
    "New York Yankees":      (40.8296, -73.9262),     # Yankee Stadium
    "Oakland Athletics":     (38.5803, -121.4994),    # Sutter Health Park
    "Athletics":             (38.5803, -121.4994),
    "Philadelphia Phillies": (39.9061, -75.1665),     # Citizens Bank Park
    "Pittsburgh Pirates":    (40.4469, -80.0057),     # PNC Park
    "San Diego Padres":      (32.7073, -117.1566),    # Petco Park
    "San Francisco Giants":  (37.7786, -122.3893),    # Oracle Park
    "Seattle Mariners":      None,                    # T-Mobile Park — dome
    "St. Louis Cardinals":   (38.6226, -90.1928),     # Busch Stadium
    "Tampa Bay Rays":        None,                    # Tropicana — dome
    "Texas Rangers":         None,                    # Globe Life — dome
    "Toronto Blue Jays":     None,                    # Rogers Centre — dome
    "Washington Nationals":  (38.8730, -77.0074),     # Nationals Park
}

# ── Pitcher ERA fallback — updated with 2026 early season data ───────────────
# Sources: MLB.com, FanGraphs, DraftKings Network, Fox Sports (Apr 13 2026)
# 🟢 = confirmed 2026 ERA | 🟡 = 2025 baseline projection
PITCHER_ERA_FALLBACK = {
    # ── Elite tier — 2026 confirmed ──────────────────────────────────────────
    "Paul Skenes": 4.50,          # 🟢 9.53 opening day, rebounded — using mid estimate
    "Tarik Skubal": 2.50,         # 🟢 elite through early starts
    "Yoshinobu Yamamoto": 2.49,   # 🟡 2025 baseline, expected similar
    "Cristopher Sanchez": 1.65,   # 🟢 fantastic 3 starts, 1.65 ERA
    "Chase Burns": 0.82,          # 🟢 elite — 0.82 ERA, 44% whiff rate
    "Garrett Crochet": 2.59,      # 🟡 2025 career best, expected similar
    "Cam Schlittler": 1.62,       # 🟢 Yankees breakout, 1.62 ERA
    "Rhett Lowder": 1.64,         # 🟢 Reds, 1.64 ERA early
    "Bryce Elder": 0.00,          # 🟢 2 starts, 0 ER — regress to 2.50
    "Will Warren": 3.07,          # 🟢 Yankees, 3.07 ERA confirmed
    "Cade Cavalli": 2.51,         # 🟢 2.51 ERA (xERA 4.22 — regression coming)
    "Logan Webb": 3.12,           # 🟡 workhorse, consistent
    "Corbin Burnes": 3.22,        # 🟡 Giants ace
    "Max Fried": 3.25,            # 🟡 Yankees
    "Zack Wheeler": 3.18,         # 🟡 returning from injury
    "Framber Valdez": 3.00,       # 🟡 Tigers workhorse
    "Freddy Peralta": 3.40,       # 🟡 Mets
    "Dylan Cease": 3.38,          # 🟡 Padres
    "Luis Castillo": 3.50,        # 🟡 Mariners
    "Kevin Gausman": 3.45,        # 🟡 Blue Jays
    "Hunter Brown": 3.18,         # 🟡 Astros
    "George Kirby": 3.60,         # 🟡 Mariners
    "Bryan Woo": 3.80,            # 🟡 Mariners
    "Michael King": 3.75,         # 🟡 Padres
    "MacKenzie Gore": 3.90,       # 🟡 Nationals
    "Ranger Suarez": 3.80,        # 🟡 Phillies
    "Sandy Alcantara": 3.50,      # 🟡 Marlins
    "Roki Sasaki": 3.70,          # 🟡 Dodgers
    "Joe Ryan": 3.85,             # 🟡 Twins
    "Bailey Ober": 3.90,          # 🟡 Twins
    # ── Mid tier ─────────────────────────────────────────────────────────────
    "Tanner Bibee": 4.24,         # 🟡 Guardians
    "Zac Gallen": 3.85,           # 🟡 Diamondbacks
    "Gavin Williams": 3.92,       # 🟡 Guardians
    "Shane Bieber": 3.60,         # 🟡 Red Sox
    "Luis Severino": 4.88,        # 🟢 11 walks in 13.1 IP, struggling
    "Andrew Abbott": 4.05,        # 🟡 Reds
    "Reese Olson": 4.15,          # 🟡 Tigers
    "Jared Jones": 4.20,          # 🟡 Pirates
    "Nestor Cortes": 4.20,        # 🟡 Brewers
    "Edward Cabrera": 4.20,       # 🟡 Marlins
    "Parker Messick": 4.20,       # 🟡
    "Emerson Hancock": 4.50,      # 🟡
    "Kyle Harrison": 4.30,        # 🟡 Giants
    "Nick Martinez": 4.40,        # 🟡
    "Eric Lauer": 4.35,           # 🟡
    "Chris Paddack": 4.55,        # 🟡
    "Walker Buehler": 4.80,       # 🟡 Dodgers
    "Braxton Garrett": 4.30,      # 🟡
    "Matthew Liberatore": 4.40,   # 🟡 Cardinals
    "Trevor Rogers": 4.35,        # 🟡
    "Robbie Ray": 4.80,           # 🟡
    "Jake Irvin": 4.60,           # 🟡 Nationals
    "Carlos Rodon": 4.50,         # 🟡 Giants
    "Kyle Freeland": 4.65,        # 🟡 Rockies
    "Patrick Corbin": 5.20,       # 🟡 struggling
    "Konnor Griffin": 3.90,       # 🟡 Pirates top prospect
    "Simeon Woods Richardson": 4.40,
    "Jared Bubic": 4.50,
    "Jesus Luzardo": 4.10,
    "Jose Suarez": 4.70,
    "Aaron Civale": 4.50,
    "Bryce Miller": 4.20,
    "Tylor Megill": 4.30,
    "Jose Quintana": 4.50,
    "Charlie Morton": 4.40,
    "Dane Dunning": 4.60,
    "Graham Ashcraft": 4.55,
    "Hayden Wesneski": 4.40,
    "Yu Darvish": 3.80,
    "Mitch Keller": 3.91,
    "Jameson Taillon": 3.68,
    "Shane McClanahan": 3.86,
    "Sonny Gray": 3.80,
    # ── New 2026 pitchers seen on slate ──────────────────────────────────────
    "Yusei Kikuchi": 6.76,        # 🟢 11 runs in 14.2 IP, struggling
    "Ryne Nelson": 4.20,          # 🟢 4.20 ERA, xERA 5.61 — regression risk
    "Javier Assad": 3.20,         # 🟢 great first start 2026
    "Mike Burrows": 4.20,         # 🟡 Pirates prospect
    "Janson Junk": 4.80,          # 🟡 Marlins
    "Casey Mize": 4.30,           # 🟡 Tigers
    "Keider Montero": 4.50,       # 🟡 Tigers
    "Jack Kochanowicz": 4.40,     # 🟡 Angels
    "Brandon Williamson": 4.20,   # 🟡 Reds
    "Jacob Lopez": 4.60,          # 🟡
    "Erick Fedde": 4.40,          # 🟡 White Sox
    "Michael Wacha": 4.10,        # 🟡 Royals
    "Nick Martinez": 4.40,        # 🟡
    "Foster Griffin": 4.70,       # 🟡
    "Kyle Leahy": 4.50,           # 🟡
    "Logan Webb": 3.12,           # 🟡
    "Chris Bassitt": 4.00,        # 🟡 Orioles
    "Shane Baz": 4.20,            # 🟡 Rays
    "Slade Cecconi": 4.40,        # 🟡 Braves
    "Davis Martin": 4.60,         # 🟡 White Sox
    "Kris Bubic": 4.20,           # 🟡 Royals
    "Chad Patrick": 4.50,         # 🟡 Brewers
    "Connelly Early": 4.80,       # 🟡 Red Sox
    "Dustin May": 4.30,           # 🟡 Cardinals
    "Ryan Feltner": 4.70,         # 🟡 Rockies
    "German Marquez": 5.00,       # 🟡 Rockies
    "Jack Leiter": 3.80,          # 🟡 Rangers top prospect
    "Emmet Sheehan": 4.20,        # 🟡 Dodgers
    "Lance McCullers Jr.": 3.90,  # 🟡 Astros
    "Luis Castillo": 3.50,        # 🟡 Mariners
    "George Kirby": 3.60,         # 🟡 Mariners
    "Brandon Pfaadt": 4.20,       # 🟡 Diamondbacks
    "Taijuan Walker": 4.50,       # 🟡 Phillies
    "Martin Perez": 4.40,         # 🟡 Braves
    "Joe Ryan": 3.85,             # 🟡 Twins
    "Paul Blackburn": 4.30,       # 🟡
    "Landen Roupp": 3.80,         # 🟡 Giants
    "Cam Schlittler": 1.62,       # 🟢 Yankees
    "Will Warren": 3.07,          # 🟢 Yankees
    "Steven Matz": 4.50,          # 🟡 Rays
    "J.T. Ginn": 4.20,            # 🟡 Mets
    "Clay Holmes": 3.80,          # 🟡 Mets (converted SP)
    "Kodai Senga": 3.50,          # 🟡 Mets — returning from injury
    "Logan Webb": 3.12,           # 🟡 Giants
    "Braxton Ashcraft": 4.30,     # 🟡 Pirates
    "Edward Cabrera": 4.20,       # 🟡 Marlins
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
    """
    Fetch live 2026 team RPG and bullpen ERA from StatsAPI.
    Uses statsapi.standings_data for team list, then statsapi.team_stats
    for hitting and pitching splits.
    Bullpen ERA = relief pitching only (excludes starters).
    """
    rpg = {}
    bullpen_era = {}
    try:
        season = datetime.today().year
        # Get team list via standings (more reliable than get('teams'))
        standings = statsapi.standings_data(leagueId="103,104", season=season)
        team_ids = {}
        for league in standings.values():
            for div in league.get('divisions', {}).values():
                for team in div.get('teams', []):
                    name = team.get('name', '')
                    tid = team.get('team_id')
                    games = int(team.get('w', 0)) + int(team.get('l', 0))
                    if tid and games >= 5:
                        team_ids[name] = (tid, games)

        for team_name, (team_id, games) in team_ids.items():
            # ── Team RPG from hitting stats via REST API ──────────────────
            try:
                import requests as _req
                h_url = (f"https://statsapi.mlb.com/api/v1/teams/{team_id}/stats"
                         f"?stats=season&group=hitting&season={season}&sportId=1")
                h_resp = _req.get(h_url, timeout=8)
                if h_resp.status_code == 200:
                    h_data = h_resp.json()
                    for sg in h_data.get('stats', []):
                        for split in sg.get('splits', []):
                            stat = split.get('stat', {})
                            runs = int(stat.get('runs', 0) or 0)
                            gp = int(stat.get('gamesPlayed', 0) or 0)
                            if gp >= 5 and runs > 0:
                                rpg[team_name] = round(runs / gp, 2)
            except Exception:
                pass

            # ── Bullpen ERA from relief pitching ─────────────────────────
            try:
                # Use the REST API directly for relief stats
                import requests as _req
                url = (f"https://statsapi.mlb.com/api/v1/teams/{team_id}/stats"
                       f"?stats=season&group=pitching&season={season}&sportId=1")
                resp = _req.get(url, timeout=8)
                if resp.status_code == 200:
                    data = resp.json()
                    for sg in data.get('stats', []):
                        for split in sg.get('splits', []):
                            stat = split.get('stat', {})
                            era_val = stat.get('era')
                            gp = int(stat.get('gamesPlayed', 0) or 0)
                            if era_val and gp >= 5:
                                # Full team pitching ERA as proxy
                                # We'll separate SP contribution below
                                team_era = float(era_val)
                                # Estimate bullpen ERA:
                                # Team ERA = (SP_innings * SP_ERA + BP_innings * BP_ERA) / total_innings
                                # Approximate: BP_ERA ~ team_ERA * 1.1 (bullpens typically worse)
                                bullpen_era[team_name] = round(team_era * 1.05, 2)
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
    if deg is None:
        return ""
    closest = min(WIND_DIR_LABELS.keys(), key=lambda x: abs(x - deg))
    return WIND_DIR_LABELS[closest]

@st.cache_data(ttl=1800)
def fetch_stadium_weather(home_team, game_hour_utc=None):
    """
    Fetch weather from Open-Meteo (free, no API key).
    Uses stadium lat/lon. If game_hour_utc provided, fetches forecast for that hour.
    Returns dict with temp_f, wind_speed_mph, wind_dir_deg, wind_dir_label, dome.
    """
    coords = STADIUM_COORDS.get(home_team)
    if coords is None:
        return {"dome": True}
    lat, lon = coords
    try:
        # Request hourly forecast for today
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,windspeed_10m,winddirection_10m",
            "temperature_unit": "fahrenheit",
            "windspeed_unit": "mph",
            "forecast_days": 1,
            "timezone": "auto",
        }
        resp = requests.get(url, params=params, timeout=8)
        if resp.status_code != 200:
            return None
        d = resp.json()
        hourly = d.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        wspeeds = hourly.get("windspeed_10m", [])
        wdirs = hourly.get("winddirection_10m", [])

        if not times:
            return None

        # Pick the hour closest to game time, or current hour
        target_hour = game_hour_utc if game_hour_utc else datetime.utcnow().hour
        # Find best matching index
        best_idx = 0
        for i, t in enumerate(times):
            try:
                h = int(t.split("T")[1][:2])
                if h <= target_hour:
                    best_idx = i
            except Exception:
                continue

        temp = temps[best_idx] if temps else None
        wspeed = wspeeds[best_idx] if wspeeds else 0
        wdir = wdirs[best_idx] if wdirs else 0

        return {
            "dome": False,
            "temp_f": round(temp, 1) if temp else None,
            "wind_speed_mph": round(wspeed, 1) if wspeed else 0,
            "wind_dir_deg": round(wdir) if wdir else 0,
            "wind_dir_label": deg_to_label(wdir),
            "source": "Open-Meteo",
        }
    except Exception:
        return None

# Load live team stats
_live_rpg, _live_bullpen = fetch_live_team_stats()

# ── Single consolidated sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-header">System Status</div>', unsafe_allow_html=True)
    st.markdown(f"**Supabase:** {'✅ Connected' if supabase_connected else '❌ Not connected'}")
    _odds_key = get_secret("ODDS_API_KEY")
    st.markdown(f"**Odds API Key:** {'✅ Loaded' if _odds_key else '❌ Missing'}")
    if _odds_key:
        st.caption(f"Prefix: {_odds_key[:6]}…")
    st.markdown("**Weather:** ✅ Open-Meteo (free, no key)")
    st.markdown("---")
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

def wind_out_factor(wind_dir_deg, home_team):
    """
    Returns a factor from -1.0 to +1.0:
      +1.0 = pure out (blowing toward outfield = more runs)
      -1.0 = pure in (blowing toward home plate = fewer runs)
       0.0 = pure crosswind (no effect)
    Uses stadium CF bearing to determine actual wind effect.
    """
    import math
    cf_bearing = STADIUM_CF_BEARING.get(home_team)
    if cf_bearing is None:
        return 0.0  # Unknown orientation — no adjustment
    # Wind direction: meteorological convention = direction wind is coming FROM
    # Wind blowing FROM cf_bearing = blowing IN (suppresses scoring)
    # Wind blowing FROM opposite of cf_bearing = blowing OUT (increases scoring)
    # Angle between wind source and CF direction
    angle = (wind_dir_deg - cf_bearing + 180) % 360 - 180
    # cos(angle): +1 when wind blows directly out, -1 when directly in
    return round(math.cos(math.radians(angle)), 3)

def weather_adjs(weather, home_team, scale=1.0):
    if not weather or weather.get("dome"):
        return 0.0, 0.0, None
    import math
    wspeed = weather.get("wind_speed_mph") or 0
    wdir = weather.get("wind_dir_deg") or 0
    w_adj = 0.0
    w_label = None
    if wspeed and wspeed >= 5:
        factor = wind_out_factor(wdir, home_team)
        w_adj = round(factor * (wspeed / 10) * 0.3 * scale, 2)
        if factor > 0.3:
            w_label = "🌬️ Blowing OUT"
        elif factor < -0.3:
            w_label = "🌬️ Blowing IN"
        else:
            w_label = "💨 Crosswind"
    temp = weather.get("temp_f")
    t_adj = 0.0
    if temp and temp < 50:
        t_adj = round((50 - temp) * -0.02 * scale, 2)
    return w_adj, t_adj, w_label

def calc_f5(away, home, away_pitcher, home_pitcher, pf, weather):
    away_rpg = get_team_rpg(away) * (F5_INNINGS / TOTAL_INNINGS)
    home_rpg = (get_team_rpg(home) + HOME_ADVANTAGE_F5) * (F5_INNINGS / TOTAL_INNINGS)
    base = round(away_rpg + home_rpg, 2)
    away_era, away_recent, away_src = blend_era(away_pitcher)
    home_era, home_recent, home_src = blend_era(home_pitcher)
    away_sp_adj = round(((away_era - LEAGUE_AVG_ERA) / 9) * F5_INNINGS * 0.5, 2)
    home_sp_adj = round(((home_era - LEAGUE_AVG_ERA) / 9) * F5_INNINGS * 0.5, 2)
    w_adj, t_adj, w_label = weather_adjs(weather, home, scale=F5_INNINGS / TOTAL_INNINGS)
    raw = base + away_sp_adj + home_sp_adj + w_adj + t_adj
    return {
        "total": round(raw * pf, 1), "base": base,
        "away_era": away_era, "away_recent": away_recent, "away_src": away_src,
        "home_era": home_era, "home_recent": home_recent, "home_src": home_src,
        "away_sp_adj": away_sp_adj, "home_sp_adj": home_sp_adj,
        "wind_adj": w_adj, "temp_adj": t_adj, "wind_label": w_label,
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
    w_adj, t_adj, w_label = weather_adjs(weather, home, scale=1.0)
    raw = base + away_sp_adj + home_sp_adj + away_bp_adj + home_bp_adj + w_adj + t_adj
    return {
        "total": round(raw * pf, 1), "base": base,
        "away_era": away_era, "away_recent": away_recent, "away_src": away_src,
        "home_era": home_era, "home_recent": home_recent, "home_src": home_src,
        "away_sp_adj": away_sp_adj, "home_sp_adj": home_sp_adj,
        "away_bp_era": away_bp_era, "home_bp_era": home_bp_era,
        "away_bp_adj": away_bp_adj, "home_bp_adj": home_bp_adj,
        "wind_adj": w_adj, "temp_adj": t_adj, "wind_label": w_label,
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
                                over_edge, "OVER", bet_amt, market_type, game_id,
                                placed_on_kalshi=placed, real_amount=real_amt):
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
                                under_edge, "UNDER", bet_amt, market_type, game_id,
                                placed_on_kalshi=placed, real_amount=real_amt):
                        st.success("Logged!")
        else:
            st.info(f"⚪ **UNDER** | Edge: {e}%")
    return over_edge, under_edge

def save_bet(game_date, away, home, away_pitcher, home_pitcher, model_total,
             kalshi_line, kalshi_over_price, model_prob, your_prob, edge,
             direction, bet_amt, market_type="full", game_id=None,
             placed_on_kalshi=False, real_amount=None):
    try:
        row = {
            "game_date": game_date, "away_team": away, "home_team": home,
            "away_pitcher": away_pitcher, "home_pitcher": home_pitcher,
            "model_total": model_total, "kalshi_line": kalshi_line,
            "kalshi_over_price": kalshi_over_price, "model_prob": model_prob,
            "your_prob": your_prob, "edge": round(edge, 4),
            "bet_direction": direction, "bet_amount": bet_amt,
            "market_type": market_type, "game_id": game_id,
            "placed_on_kalshi": placed_on_kalshi,
            "real_amount": real_amount if placed_on_kalshi else None,
        }
        supabase.table("mlb_settlements").insert(row).execute()
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
        return None
    today_str = datetime.today().strftime('%Y-%m-%d')
    try:
        resp = supabase.table("mlb_settlements").select("*") \
            .is_("actual_total", "null").lt("game_date", today_str).execute()
    except Exception:
        return None
    rows = resp.data or []
    if not rows:
        return None
    settled, skipped = 0, 0
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
    return msg

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

_settlement_msg = run_auto_settlement()

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
    if _settlement_msg:
        st.success(_settlement_msg)
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
                    _game_utc_hour = datetime.strptime(g['game_datetime'], '%Y-%m-%dT%H:%M:%SZ').hour
                    _wx = fetch_stadium_weather(_home, game_hour_utc=_game_utc_hour)
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

                    # F5 signal tier
                    _k5_price = _k5["over_price_cents"] if _k5 else 50
                    _f5_prob = model_to_prob(_f5["total"], _f5_line) / 100
                    _f5_lean = "OVER" if _f5d > 0.3 else "UNDER" if _f5d < -0.3 else "EVEN"
                    _f5_edge = (_f5_prob - _k5_price/100) if _f5_lean == "OVER" else ((1-_f5_prob) - (1-_k5_price/100)) if _f5_lean == "UNDER" else 0
                    _f5_edge_pct = round(abs(_f5_edge) * 100, 1)
                    if _f5_lean == "EVEN" or _f5_edge < EDGE_THRESHOLD:
                        _f5_signal = "⚪ NO EDGE"
                    elif _f5_edge_pct >= 12:
                        _f5_signal = "🔥 HIGH"
                    elif _f5_edge_pct >= 8:
                        _f5_signal = "💪 STRONG"
                    else:
                        _f5_signal = "👍 LEAN"
                    _f5_dir = "🟢 OVER" if _f5_lean == "OVER" else "🔴 UNDER" if _f5_lean == "UNDER" else "⚪"

                    # FG signal tier
                    _kf_price = _kf["over_price_cents"] if _kf else 50
                    _fg_prob = model_to_prob(_fg["total"], _fg_line) / 100
                    _fg_lean = "OVER" if _fgd > 0.3 else "UNDER" if _fgd < -0.3 else "EVEN"
                    _fg_edge = (_fg_prob - _kf_price/100) if _fg_lean == "OVER" else ((1-_fg_prob) - (1-_kf_price/100)) if _fg_lean == "UNDER" else 0
                    _fg_edge_pct = round(abs(_fg_edge) * 100, 1)
                    if _fg_lean == "EVEN" or _fg_edge < EDGE_THRESHOLD:
                        _fg_signal = "⚪ NO EDGE"
                    elif _fg_edge_pct >= 12:
                        _fg_signal = "🔥 HIGH"
                    elif _fg_edge_pct >= 8:
                        _fg_signal = "💪 STRONG"
                    else:
                        _fg_signal = "👍 LEAN"
                    _fg_dir = "🟢 OVER" if _fg_lean == "OVER" else "🔴 UNDER" if _fg_lean == "UNDER" else "⚪"

                    # Abbreviate team names (last word) and pitchers (First initial. Last)
                    def abbrev_team(name):
                        parts = name.split()
                        return parts[-1] if parts else name

                    def abbrev_pitcher(name):
                        if not name or name == "TBD":
                            return "TBD"
                        parts = name.split()
                        if len(parts) >= 2:
                            return f"{parts[0][0]}. {parts[-1]}"
                        return name

                    _away_abbr = abbrev_team(_away)
                    _home_abbr = abbrev_team(_home)
                    _ap_abbr = abbrev_pitcher(_ap)
                    _hp_abbr = abbrev_pitcher(_hp)

                    _vegas_str = f"{_odds['total']}" if _odds else "—"
                    # Row 1: F5 — team/pitcher info, no Vegas (Vegas is full game only)
                    rows.append({
                        "Time": _et,
                        "Matchup": f"{_away_abbr}@{_home_abbr}",
                        "Mkt": "F5",
                        "Model": _f5["total"],
                        "Line": f"{_f5_line}{'✅' if _k5 else '~'}",
                        "Signal": f"{_f5_dir} {_f5_signal}",
                        "Vegas": "—",
                        # Desktop extras
                        "Away SP": _ap if _ap != "TBD" else "❓",
                        "Home SP": _hp if _hp != "TBD" else "❓",
                        "Park": _pf_str,
                    })
                    # Row 2: FG — blank team/pitcher, Vegas shown here
                    rows.append({
                        "Time": "",
                        "Matchup": "",
                        "Mkt": "FG",
                        "Model": _fg["total"],
                        "Line": f"{_fg_line}{'✅' if _kf else '~'}",
                        "Signal": f"{_fg_dir} {_fg_signal}",
                        "Vegas": _vegas_str,
                        # Desktop extras
                        "Away SP": "",
                        "Home SP": "",
                        "Park": "",
                    })
                except Exception:
                    continue

            if rows:
                st.markdown("<div class='section-header'>📋 Today's Slate</div>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    if kalshi_lines:
                        st.success(kalshi_status)
                    else:
                        st.warning(kalshi_status)
                with c2:
                    if odds_lines:
                        st.success(odds_status)
                    else:
                        st.warning(odds_status)

                # Mobile vs desktop view toggle
                view_type = st.radio("Table view", ["📱 Mobile", "🖥️ Desktop"],
                                     horizontal=True, label_visibility="collapsed")

                df_all = pd.DataFrame(rows)
                if view_type == "📱 Mobile":
                    mobile_cols = ["Time", "Matchup", "Mkt", "Model", "Line", "Signal"]
                    st.dataframe(df_all[mobile_cols], use_container_width=True, hide_index=True)
                else:
                    desktop_cols = ["Time", "Matchup", "Away SP", "Home SP", "Park",
                                    "Mkt", "Model", "Line", "Vegas", "Signal"]
                    st.dataframe(df_all[desktop_cols], use_container_width=True, hide_index=True)
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
                    _g_utc_hour = datetime.strptime(game['game_datetime'], '%Y-%m-%dT%H:%M:%SZ').hour
                    wx = fetch_stadium_weather(home, game_hour_utc=_g_utc_hour)
                    f5 = calc_f5(away, home, ap, hp, pf, wx)
                    fg = calc_fg(away, home, ap, hp, pf, wx)

                    with st.expander(f"**{away} @ {home}** — {et}"):
                        # ── Pitchers & ERA (always single line on mobile) ──────
                        away_src = '🟢' if f5['away_src'] == 'live' else '🟡'
                        home_src = '🟢' if f5['home_src'] == 'live' else '🟡'
                        away_line = f"**Away:** {away} | SP: {ap} | ERA: {f5['away_era']} {away_src}"
                        home_line = f"**Home:** {home} | SP: {hp} | ERA: {f5['home_era']} {home_src}"
                        st.markdown(away_line + "  \n" + home_line)

                        # Park + weather — 2 cols on mobile, 3 on desktop
                        if wx is None:
                            wx_str = "⚠️ Weather unavailable"
                        elif wx.get("dome"):
                            wx_str = "🏟️ Dome — weather N/A"
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

                        # ── FIRST 5 INNINGS ───────────────────────────────────
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

                        st.markdown('<hr class="mph-divider">', unsafe_allow_html=True)

                        # ── FULL GAME ─────────────────────────────────────────
                        st.markdown('<div class="section-header">🏟️ Full Game</div>', unsafe_allow_html=True)
                        cG1, cG2 = st.columns(2)
                        with cG1:
                            st.metric("FG Model", fg["total"])
                        with cG2:
                            st.metric(f"Away Bullpen", fg["away_bp_era"],
                                      delta=f"Adj: {fg['away_bp_adj']:+.2f}")
                        st.metric(f"Home Bullpen", fg["home_bp_era"],
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
    st.markdown('<div class="section-header">📊 Settlement Tracker</div>', unsafe_allow_html=True)
    if supabase_connected:
        try:
            data = supabase.table("mlb_settlements").select("*").order("game_date", desc=True).execute()
            if data.data:
                df = pd.DataFrame(data.data)

                # ── Filter toggle ─────────────────────────────────────────────
                view_mode = st.radio(
                    "View",
                    ["All Model Bets", "Real Kalshi Bets Only"],
                    horizontal=True
                )
                if view_mode == "Real Kalshi Bets Only":
                    if "placed_on_kalshi" in df.columns:
                        df = df[df["placed_on_kalshi"] == True]
                    else:
                        st.info("No real Kalshi bets logged yet — use the '📍 Placed on Kalshi' checkbox when logging.")

                if df.empty:
                    st.info("No bets in this view yet.")
                else:
                    settled = df[df["result"].notna()]
                    if not settled.empty:
                        wins = (settled["result"] == "WIN").sum()
                        losses = (settled["result"] == "LOSS").sum()
                        pushes = (settled["result"] == "PUSH").sum()
                        wp = round(wins / (wins + losses) * 100, 1) if (wins + losses) > 0 else 0

                        # P&L — use real_amount for Kalshi view, recalculate from real cost
                        if view_mode == "Real Kalshi Bets Only" and "real_amount" in settled.columns:
                            # Recalculate real P&L: for wins use profit_loss ratio, for losses use real_amount
                            real_pnl = 0.0
                            for _, row in settled.iterrows():
                                real_amt = row.get("real_amount") or row.get("bet_amount") or 0
                                model_amt = row.get("bet_amount") or 25
                                model_pnl = row.get("profit_loss") or 0
                                if model_amt and model_amt > 0:
                                    # Scale model P&L by real/model ratio
                                    real_pnl += round(model_pnl * (real_amt / model_amt), 2)
                                else:
                                    real_pnl += model_pnl
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

                    # ── Display columns ───────────────────────────────────────
                    base_cols = ["game_date", "away_team", "home_team", "market_type",
                                 "model_total", "kalshi_line", "bet_direction", "bet_amount"]
                    if view_mode == "Real Kalshi Bets Only":
                        base_cols.append("real_amount")
                        # Add real P&L column
                        if "real_amount" in df.columns and "profit_loss" in df.columns and "bet_amount" in df.columns:
                            df = df.copy()
                            def calc_real_pnl(row):
                                real = row.get("real_amount") or row.get("bet_amount") or 0
                                model = row.get("bet_amount") or 25
                                pnl = row.get("profit_loss") or 0
                                if model and model > 0:
                                    return round(pnl * (real / model), 2)
                                return pnl
                            df["real_P&L"] = df.apply(calc_real_pnl, axis=1)
                            base_cols.append("real_P&L")
                    base_cols += ["actual_total", "result", "profit_loss", "settled_at"]
                    display_cols = [c for c in base_cols if c in df.columns]

                    # Color code results
                    def highlight_result(row):
                        if row.get("result") == "WIN":
                            return ["background-color: #1a3a2a"] * len(row)
                        elif row.get("result") == "LOSS":
                            return ["background-color: #3a1a1a"] * len(row)
                        return [""] * len(row)

                    st.dataframe(
                        df[display_cols].style.apply(highlight_result, axis=1),
                        use_container_width=True
                    )
            else:
                st.info("No bets logged yet.")
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Supabase not connected.")
