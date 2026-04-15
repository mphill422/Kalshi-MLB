import streamlit as st
import streamlit.components.v1 as components
import statsapi
import pandas as pd
import requests
from datetime import datetime, timedelta
from supabase import create_client

# ── Always use Eastern Time for dates (MLB runs on ET) ───────────────────────
from datetime import timezone
ET_OFFSET = timezone(timedelta(hours=-4))  # EDT (EST is -5, EDT is -4)

def today_et():
    return datetime.now(ET_OFFSET).strftime('%Y-%m-%d')

def now_et():
    return datetime.now(ET_OFFSET)

st.set_page_config(page_title="MPH MLB Model", layout="wide", page_icon="⚾")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

html, body, .stApp {
    background-color: #080c14 !important;
    font-family: 'Inter', sans-serif !important;
}

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

.section-header {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase; color: #1e90ff;
    border-bottom: 1px solid #1e90ff22; padding-bottom: 6px;
    margin: 1.2rem 0 0.8rem 0;
}

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

.sig-fire   { color: #ff6b35; font-weight: 700; }
.sig-strong { color: #ffd700; font-weight: 700; }
.sig-lean   { color: #00cc88; font-weight: 700; }
.sig-none   { color: #3a4a60; }

.mph-divider {
    border: none; border-top: 1px solid #1e3a5f;
    margin: 1rem 0;
}

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

div[data-testid="stAlert"] {
    border-radius: 6px !important;
    font-size: 0.85rem !important;
}

.stDataFrame {
    border-radius: 8px !important;
    border: 1px solid #1e3a5f !important;
    overflow: hidden !important;
}

section[data-testid="stSidebar"] {
    background: #080c14 !important;
    border-right: 1px solid #1e3a5f !important;
}
section[data-testid="stSidebar"] .stMarkdown {
    font-size: 0.85rem !important;
}

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

st.markdown(f"""
<div class="mph-header">
  <div>
    <div class="mph-title">⚾ MPH <span>MLB</span> Model</div>
    <div class="mph-sub">Run Totals · First 5 Innings · Full Game &nbsp;
      <span class="pill-live">● LIVE</span>
    </div>
  </div>
  <div style="text-align:right">
    <div class="mph-badge">V4.31</div>
    <div class="mph-sub" style="margin-top:4px">{now_et().strftime('%b %d, %Y')}</div>
  </div>
</div>
""", unsafe_allow_html=True)

BANKROLL = 500
EDGE_THRESHOLD = 0.08   # ← V4.31: raised from 0.05 to 0.08
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

STADIUM_CF_BEARING = {
    "Atlanta Braves":        22,
    "Baltimore Orioles":     90,
    "Boston Red Sox":        95,
    "Chicago Cubs":          180,
    "Cincinnati Reds":       355,
    "Cleveland Guardians":   225,
    "Colorado Rockies":      292,
    "Detroit Tigers":        352,
    "Kansas City Royals":    30,
    "Los Angeles Angels":    225,
    "Los Angeles Dodgers":   315,
    "Minnesota Twins":       105,
    "New York Mets":         355,
    "New York Yankees":      225,
    "Oakland Athletics":     225,
    "Athletics":             225,
    "Philadelphia Phillies": 55,
    "Pittsburgh Pirates":    125,
    "San Diego Padres":      315,
    "San Francisco Giants":  115,
    "St. Louis Cardinals":   105,
    "Washington Nationals":  45,
}

STADIUM_COORDS = {
    "Arizona Diamondbacks":  None,
    "Atlanta Braves":        (33.8908, -84.4678),
    "Baltimore Orioles":     (39.2838, -76.6216),
    "Boston Red Sox":        (42.3467, -71.0972),
    "Chicago Cubs":          (41.9484, -87.6553),
    "Chicago White Sox":     None,
    "Cincinnati Reds":       (39.0979, -84.5082),
    "Cleveland Guardians":   (41.4962, -81.6852),
    "Colorado Rockies":      (39.7559, -104.9942),
    "Detroit Tigers":        (42.3390, -83.0485),
    "Houston Astros":        None,
    "Kansas City Royals":    (39.0517, -94.4803),
    "Los Angeles Angels":    (33.8003, -117.8827),
    "Los Angeles Dodgers":   (34.0739, -118.2400),
    "Miami Marlins":         None,
    "Milwaukee Brewers":     None,
    "Minnesota Twins":       (44.9817, -93.2778),
    "New York Mets":         (40.7571, -73.8458),
    "New York Yankees":      (40.8296, -73.9262),
    "Oakland Athletics":     (38.5803, -121.4994),
    "Athletics":             (38.5803, -121.4994),
    "Philadelphia Phillies": (39.9061, -75.1665),
    "Pittsburgh Pirates":    (40.4469, -80.0057),
    "San Diego Padres":      (32.7073, -117.1566),
    "San Francisco Giants":  (37.7786, -122.3893),
    "Seattle Mariners":      None,
    "St. Louis Cardinals":   (38.6226, -90.1928),
    "Tampa Bay Rays":        None,
    "Texas Rangers":         None,
    "Toronto Blue Jays":     None,
    "Washington Nationals":  (38.8730, -77.0074),
}

# ── Pitcher ERA — updated April 14 2026 ──────────────────────────────────────
# 🟢 = confirmed 2026 ERA  |  🟡 = 2025 baseline / projection
PITCHER_ERA_FALLBACK = {
    # ── Elite / confirmed 2026 ────────────────────────────────────────────────
    "Tarik Skubal": 0.69,           # 🟢 0.69 ERA through early starts (historically regresses — use with caution)
    "Chase Burns": 0.82,            # 🟢 elite — 44% whiff rate
    "Cristopher Sanchez": 1.65,     # 🟢 fantastic 3 starts
    "Rhett Lowder": 1.64,           # 🟢 Reds
    "Cam Schlittler": 1.62,         # 🟢 Yankees breakout, 1.47 xERA
    "Trevor Rogers": 1.89,          # 🟢 Orioles ace — 1.89 ERA 2025 2nd half carried into 2026
    "Bryan Woo": 1.50,              # 🟢 1.50 ERA, 1.95 xERA — strong early
    "Garrett Crochet": 2.59,        # 🟢 200 IP, 2.59 ERA in 2025 — elite
    "Yoshinobu Yamamoto": 2.49,     # 🟡 2025 baseline
    "Logan Webb": 3.12,             # 🟡 workhorse
    "Corbin Burnes": 3.22,          # 🟡 Giants ace
    "Max Fried": 3.25,              # 🟡 Yankees
    "Zack Wheeler": 3.18,           # 🟡
    "Framber Valdez": 3.66,         # 🟢 3.66 ERA 2025 with Tigers — updated from 3.00
    "Freddy Peralta": 3.40,         # 🟡 Mets
    "Dylan Cease": 3.38,            # 🟡 Padres
    "Luis Castillo": 3.50,          # 🟡 Mariners
    "Kevin Gausman": 3.45,          # 🟡 Blue Jays
    "Hunter Brown": 3.18,           # 🟡 Astros
    "George Kirby": 3.60,           # 🟡 Mariners
    "Michael King": 3.75,           # 🟡 Padres
    "MacKenzie Gore": 3.90,         # 🟡 Nationals — strong early K rate
    "Ranger Suarez": 3.80,          # 🟡 Phillies
    "Sandy Alcantara": 3.50,        # 🟡 Marlins
    "Roki Sasaki": 3.70,            # 🟡 Dodgers
    "Joe Ryan": 3.85,               # 🟡 Twins
    "Bailey Ober": 3.90,            # 🟡 Twins
    "Logan Gilbert": 3.40,          # 🟢 Mariners — Opening Day starter, strong 2025
    "Nick Pivetta": 2.87,           # 🟢 Padres — career best 2025, 2.87 ERA
    "Paul Skenes": 3.50,            # 🟢 NL Cy Young 2025 (1.97) — regressing to mean projection
    "Cole Ragans": 3.50,            # 🟡 Royals
    # ── Mid tier ─────────────────────────────────────────────────────────────
    "Tanner Bibee": 4.24,           # 🟡 Guardians
    "Zac Gallen": 3.85,             # 🟡 Diamondbacks
    "Gavin Williams": 3.92,         # 🟡 Guardians
    "Shane Bieber": 3.60,           # 🟡 Red Sox
    "Luis Severino": 4.88,          # 🟢 still struggling with walks
    "Andrew Abbott": 3.42,          # 🟢 updated — career 3.42 ERA/WHIP baseline
    "Reese Olson": 4.15,            # 🟡 Tigers
    "Jared Jones": 4.20,            # 🟡 Pirates
    "Nestor Cortes": 4.20,          # 🟡 Brewers
    "Edward Cabrera": 4.20,         # 🟡 Marlins
    "Parker Messick": 4.20,         # 🟡
    "Emerson Hancock": 4.50,        # 🟡
    "Kyle Harrison": 4.30,          # 🟡 Giants
    "Nick Martinez": 4.40,          # 🟡
    "Eric Lauer": 4.35,             # 🟡
    "Chris Paddack": 4.55,          # 🟡
    "Walker Buehler": 4.80,         # 🟡 Dodgers
    "Braxton Garrett": 4.30,        # 🟡
    "Matthew Liberatore": 4.40,     # 🟡 Cardinals
    "Trevor Rogers": 1.89,          # 🟢 Orioles
    "Robbie Ray": 4.80,             # 🟡
    "Jake Irvin": 4.60,             # 🟡 Nationals
    "Carlos Rodon": 4.50,           # 🟡 Giants
    "Kyle Freeland": 4.65,
