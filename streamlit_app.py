import streamlit as st
import statsapi
import pandas as pd
import requests
from datetime import datetime, timedelta
from supabase import create_client
from datetime import timezone
import math
import random

ET_OFFSET = timezone(timedelta(hours=-4))

def today_et():
    return datetime.now(ET_OFFSET).strftime('%Y-%m-%d')

def now_et():
    return datetime.now(ET_OFFSET)

st.set_page_config(page_title="MPH MLB Model", layout="wide", page_icon="⚾")

# ── Password Gate ──
def _check_app_password():
    try:
        correct_pw = st.secrets.get('app_password', None)
    except Exception:
        correct_pw = None
    if not correct_pw:
        return True
    if st.session_state.get('_app_authed') is True:
        return True
    st.markdown("""
    <style>
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    #MainMenu, footer, header {visibility: hidden;}
    .mph-login-wrap { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 70vh; }
    .mph-login-title { font-size: 2.4rem; font-weight: 700; background: linear-gradient(135deg, #00ff88 0%, #00d4ff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 0.25rem; }
    .mph-login-sub { color: #888; font-size: 0.95rem; margin-bottom: 2rem; }
    .mph-login-badge { display: inline-block; padding: 0.2rem 0.7rem; background: rgba(0,255,136,0.12); border: 1px solid rgba(0,255,136,0.4); border-radius: 999px; color: #00ff88; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.05em; margin-left: 0.5rem; }
    </style>
    <div class="mph-login-wrap">
      <div class="mph-login-title">⚾ MPH MLB Model <span class="mph-login-badge">Private</span></div>
      <div class="mph-login-sub">Private — enter access password to continue</div>
    </div>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        pw = st.text_input('Access password', type='password', key='_app_pw_input',
                           label_visibility='collapsed', placeholder='Enter password')
        if pw:
            if pw == correct_pw:
                st.session_state['_app_authed'] = True
                st.rerun()
            else:
                st.error('Incorrect password.')
    st.stop()

_check_app_password()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
html, body, .stApp { background-color: #05080f !important; font-family: 'Inter', sans-serif !important; }
.mph-header { background: linear-gradient(135deg, #0a1628 0%, #0d1f3c 50%, #071020 100%); border-bottom: 1px solid #1e90ff44; padding: 16px 24px 14px 24px; margin: -1rem -1rem 1.5rem -1rem; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 24px #1e90ff11; }
.mph-title { font-size: 1.5rem; font-weight: 900; letter-spacing: -1px; color: #ffffff; }
.mph-title span { color: #3b9eff; }
.mph-badge { background: linear-gradient(135deg, #1e90ff22, #7c3aed22); border: 1px solid #3b9eff55; color: #3b9eff; font-size: 0.65rem; font-weight: 800; padding: 3px 10px; border-radius: 20px; letter-spacing: 2px; text-transform: uppercase; }
.mph-sub { color: #3a5070; font-size: 0.75rem; margin-top: 3px; }
.pill-live { display: inline-block; background: #00ff8811; border: 1px solid #00ff8844; color: #00ff88; font-size: 0.6rem; font-weight: 800; padding: 2px 8px; border-radius: 20px; letter-spacing: 2px; text-transform: uppercase; margin-left: 8px; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.5; } }
.section-header { font-size: 0.65rem; font-weight: 800; letter-spacing: 3px; text-transform: uppercase; color: #3b9eff; border-bottom: 1px solid #1e90ff22; padding-bottom: 6px; margin: 1.5rem 0 1rem 0; }
div[data-testid="metric-container"] { background: linear-gradient(135deg, #0d1a2d, #0a1422) !important; border: 1px solid #1e3a5f !important; border-radius: 10px !important; padding: 12px 16px !important; transition: all 0.2s; box-shadow: 0 2px 12px #00000044; }
div[data-testid="metric-container"]:hover { border-color: #3b9eff66 !important; box-shadow: 0 4px 20px #1e90ff11 !important; transform: translateY(-1px); }
div[data-testid="metric-container"] label { color: #3a5070 !important; font-size: 0.65rem !important; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600 !important; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #e8f4ff !important; font-size: 1.4rem !important; font-weight: 800 !important; }
details { background: linear-gradient(135deg, #0d1a2d, #0a1422) !important; border: 1px solid #1a3050 !important; border-radius: 10px !important; margin-bottom: 8px !important; transition: all 0.2s; box-shadow: 0 2px 12px #00000033; }
details:hover { border-color: #3b9eff44 !important; }
details summary { font-weight: 700 !important; color: #c8d8f0 !important; padding: 12px 16px !important; }
details[open] { border-color: #3b9eff55 !important; box-shadow: 0 4px 20px #1e90ff0a !important; }
.mph-divider { border: none; border-top: 1px solid #1a3050; margin: 1rem 0; }
.stButton > button { background: linear-gradient(135deg, #0d1a2d, #0a1422) !important; border: 1px solid #3b9eff44 !important; color: #3b9eff !important; border-radius: 8px !important; font-weight: 700 !important; font-size: 0.82rem !important; width: 100% !important; transition: all 0.2s !important; letter-spacing: 0.5px; }
.stButton > button:hover { background: linear-gradient(135deg, #1e90ff18, #7c3aed11) !important; border-color: #3b9eff !important; box-shadow: 0 4px 16px #1e90ff22 !important; }
div[data-testid="stAlert"] { border-radius: 8px !important; font-size: 0.82rem !important; }
.stDataFrame { border-radius: 10px !important; border: 1px solid #1a3050 !important; overflow: hidden !important; box-shadow: 0 4px 24px #00000044 !important; }
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #080c18, #05080f) !important; border-right: 1px solid #1a3050 !important; }
section[data-testid="stSidebar"] .stMarkdown { font-size: 0.82rem !important; }
.stTabs [data-baseweb="tab-list"] { background: #0d1a2d !important; border-radius: 10px !important; padding: 4px !important; gap: 4px !important; border: 1px solid #1a3050 !important; }
.stTabs [data-baseweb="tab"] { color: #3a5070 !important; font-weight: 700 !important; border-radius: 8px !important; font-size: 0.82rem !important; letter-spacing: 0.5px; }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg, #1e90ff22, #7c3aed22) !important; color: #3b9eff !important; border: 1px solid #3b9eff33 !important; }
@media (max-width: 768px) { .mph-title { font-size: 1.1rem !important; } div[data-testid="metric-container"] { padding: 8px 10px !important; } div[data-testid="metric-container"] div[data-testid="stMetricValue"] { font-size: 1.1rem !important; } .stDataFrame { font-size: 0.7rem !important; } details summary { font-size: 0.82rem !important; padding: 10px 14px !important; } }
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="mph-header">
  <div>
    <div class="mph-title">⚾ MPH <span>MLB</span> Model</div>
    <div class="mph-sub">Vegas-Anchored &middot; First 5 Innings &middot; Full Game &nbsp;<span class="pill-live">&#9679; LIVE</span></div>
  </div>
  <div style="text-align:right">
    <div class="mph-badge">V5.0</div>
    <div class="mph-sub" style="margin-top:4px">{now_et().strftime('%b %d, %Y &middot; %-I:%M %p ET')}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Constants ──
BANKROLL = 500
EDGE_THRESHOLD = 0.10
KELLY_FRACTION = 0.5
MAX_BET_PCT = 0.05
LEAGUE_AVG_ERA = 4.20
LEAGUE_AVG_BULLPEN_ERA = 4.10
SP_INNINGS = 5.0
TOTAL_INNINGS = 9.0
F5_INNINGS = 5.0
DEFAULT_FG_LINE = 8.5
DEFAULT_F5_LINE = 4.5
MAX_TEAM_RPG = 6.5
ERA_REGRESSION_FLOOR = 3.00
ERA_REGRESSION_THRESHOLD = 2.00
ERA_REGRESSION_MIN_IP = 10.0

# ── Supabase ──
try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    supabase_connected = True
except:
    supabase_connected = False

def get_secret(key):
    try:
        val = st.secrets["api_keys"][key]
        if val: return str(val)
    except: pass
    try:
        val = st.secrets[key]
        if val: return str(val)
    except: pass
    return ""

# ── Team Abbreviations ──
TEAM_ABBREV = {
    "Arizona Diamondbacks": "ARI", "Atlanta Braves": "ATL", "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS", "Chicago Cubs": "CHC", "Chicago White Sox": "CWS",
    "Cincinnati Reds": "CIN", "Cleveland Guardians": "CLE", "Colorado Rockies": "COL",
    "Detroit Tigers": "DET", "Houston Astros": "HOU", "Kansas City Royals": "KC",
    "Los Angeles Angels": "LAA", "Los Angeles Dodgers": "LAD", "Miami Marlins": "MIA",
    "Milwaukee Brewers": "MIL", "Minnesota Twins": "MIN", "New York Mets": "NYM",
    "New York Yankees": "NYY", "Oakland Athletics": "OAK", "Athletics": "OAK",
    "Philadelphia Phillies": "PHI", "Pittsburgh Pirates": "PIT", "San Diego Padres": "SD",
    "San Francisco Giants": "SF", "Seattle Mariners": "SEA", "St. Louis Cardinals": "STL",
    "Tampa Bay Rays": "TB", "Texas Rangers": "TEX", "Toronto Blue Jays": "TOR",
    "Washington Nationals": "WSH",
}

def abbrev_team(name):
    for key, abbr in TEAM_ABBREV.items():
        if key.lower() in name.lower() or name.lower() in key.lower():
            return abbr
    parts = name.split()
    return parts[-1][:4] if parts else name

# ── Dome Teams ──
DOME_TEAMS = {
    "Arizona Diamondbacks", "Chicago White Sox", "Houston Astros", "Miami Marlins",
    "Milwaukee Brewers", "Seattle Mariners", "Tampa Bay Rays", "Texas Rangers",
    "Toronto Blue Jays",
}

def is_dome(home_team):
    for d in DOME_TEAMS:
        if d.lower() in home_team.lower() or home_team.lower() in d.lower():
            return True
    return False

# ── Park Factors ──
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

def get_park_factor(home_team):
    for key in PARK_FACTORS:
        if key.lower() in home_team.lower() or home_team.lower() in key.lower():
            return PARK_FACTORS[key]
    return 1.0

# ── Pitcher ERA Fallbacks ──
PITCHER_ERA_FALLBACK = {
    "Tarik Skubal": 1.50, "Chase Burns": 1.80, "Cristopher Sanchez": 2.20,
    "Rhett Lowder": 2.10, "Garrett Crochet": 2.59, "Yoshinobu Yamamoto": 2.80,
    "Jacob deGrom": 2.29, "Bubba Chandler": 3.15, "Kumar Rocker": 3.80,
    "Bryan Woo": 2.50, "Cam Schlittler": 2.80, "Trevor Rogers": 2.90,
    "Bryce Elder": 2.80, "Spencer Schwellenbach": 3.00, "Cade Horton": 2.90,
    "Nick Pivetta": 3.10, "Ryan Weathers": 3.00, "Spencer Springs": 3.20,
    "Javier Assad": 3.20, "Logan Webb": 3.12, "Will Warren": 3.07,
    "Corbin Burnes": 3.22, "Max Fried": 3.25, "Zack Wheeler": 3.18,
    "Hunter Brown": 3.18, "Framber Valdez": 3.66, "Freddy Peralta": 3.40,
    "Logan Gilbert": 3.40, "Andrew Abbott": 3.42, "Dylan Cease": 3.38,
    "Luis Castillo": 3.50, "Kevin Gausman": 3.45, "Paul Skenes": 2.80,
    "Kodai Senga": 3.50, "Cole Ragans": 3.50, "Sandy Alcantara": 3.50,
    "George Kirby": 3.60, "Shane Bieber": 3.60, "Colin Rea": 3.60,
    "Roki Sasaki": 3.70, "Mitch Keller": 3.91, "Jameson Taillon": 3.68,
    "Michael King": 3.75, "Joe Ryan": 3.85, "Zac Gallen": 3.85,
    "Shane McClanahan": 3.86, "Landen Roupp": 3.80, "Clay Holmes": 3.80,
    "Yu Darvish": 3.80, "Jack Leiter": 3.80, "Sonny Gray": 3.80,
    "Ranger Suarez": 3.80, "MacKenzie Gore": 3.90, "Bailey Ober": 3.90,
    "Konnor Griffin": 3.90, "Lance McCullers Jr.": 3.90, "Carmen Mlodzinski": 3.50,
    "Chris Bassitt": 4.00, "Jesus Luzardo": 4.10, "Michael Wacha": 4.10,
    "Merrill Kelly": 4.10, "Tanner Bibee": 4.24, "Gavin Williams": 3.92,
    "Reese Olson": 4.15, "Jared Jones": 4.20, "Nestor Cortes": 4.20,
    "Edward Cabrera": 4.20, "Parker Messick": 4.20, "Ryne Nelson": 4.20,
    "Bryce Miller": 4.20, "Aaron Nola": 4.20, "Brandon Pfaadt": 4.20,
    "Emmet Sheehan": 4.20, "Mike Burrows": 4.20, "Brandon Williamson": 4.20,
    "Kris Bubic": 4.20, "Shane Baz": 4.20, "Jacob Lopez": 4.20,
    "Tylor Megill": 4.30, "Braxton Garrett": 4.30, "Paul Blackburn": 4.30,
    "Dustin May": 4.30, "Braxton Ashcraft": 3.90, "Kyle Harrison": 4.30,
    "Casey Mize": 4.30, "Nick Martinez": 4.40, "Matthew Liberatore": 4.40,
    "Hayden Wesneski": 4.40, "Erick Fedde": 4.40, "Jack Kochanowicz": 4.40,
    "Simeon Woods Richardson": 4.40, "Slade Cecconi": 4.40, "Martin Perez": 4.40,
    "Charlie Morton": 4.40, "Eric Lauer": 4.35, "Emerson Hancock": 4.50,
    "Chris Paddack": 4.55, "Jose Quintana": 4.50, "Aaron Civale": 4.50,
    "Carlos Rodon": 4.50, "Taijuan Walker": 4.50, "Steven Matz": 4.50,
    "Graham Ashcraft": 4.55, "Patrick Detmers": 4.60, "Jake Irvin": 4.60,
    "Dane Dunning": 4.60, "Kyle Freeland": 4.65, "Ryan Feltner": 4.70,
    "Jose Suarez": 4.70, "Walker Buehler": 4.80, "Robbie Ray": 4.80,
    "Janson Junk": 4.80, "Luis Severino": 4.88, "Patrick Corbin": 5.20,
    "German Marquez": 5.00, "Miles Mikolas": 5.50, "Yusei Kikuchi": 5.50,
    "Andrew Painter": 3.60, "David Peterson": 4.10, "Justin Wrobleski": 4.20,
    "Nolan McLean": 4.50, "Cade Cavalli": 3.80, "J.T. Ginn": 4.20,
    "Chad Patrick": 4.50, "Kyle Leahy": 4.50, "Keider Montero": 4.50,
    "Davis Martin": 4.60, "Foster Griffin": 4.70, "Connelly Early": 4.80,
    "Frankie Montas": 4.80, "Jeffrey Springs": 3.80, "MacKenzie Gore": 3.90,
}

PITCHER_HAND = {
    "Paul Skenes": "R", "Tarik Skubal": "L", "Yoshinobu Yamamoto": "R",
    "Cristopher Sanchez": "L", "Chase Burns": "R", "Garrett Crochet": "L",
    "Jacob deGrom": "R", "Bubba Chandler": "R", "Kumar Rocker": "R",
    "Logan Webb": "R", "Corbin Burnes": "R", "Max Fried": "L",
    "Zack Wheeler": "R", "Framber Valdez": "L", "Freddy Peralta": "R",
    "Dylan Cease": "R", "Luis Castillo": "R", "Kevin Gausman": "R",
    "Hunter Brown": "R", "George Kirby": "R", "Bryan Woo": "R",
    "Michael King": "R", "MacKenzie Gore": "L", "Ranger Suarez": "L",
    "Sandy Alcantara": "R", "Roki Sasaki": "R", "Joe Ryan": "R",
    "Bailey Ober": "R", "Tanner Bibee": "R", "Zac Gallen": "R",
    "Gavin Williams": "R", "Shane Bieber": "R", "Luis Severino": "R",
    "Andrew Abbott": "L", "Reese Olson": "R", "Jared Jones": "R",
    "Nestor Cortes": "L", "Edward Cabrera": "R", "Emerson Hancock": "R",
    "Kyle Harrison": "L", "Nick Martinez": "R", "Eric Lauer": "L",
    "Chris Paddack": "R", "Walker Buehler": "R", "Braxton Garrett": "L",
    "Matthew Liberatore": "L", "Trevor Rogers": "L", "Robbie Ray": "L",
    "Jake Irvin": "R", "Carlos Rodon": "L", "Kyle Freeland": "L",
    "Jesus Luzardo": "L", "Jose Suarez": "L", "Aaron Civale": "R",
    "Bryce Miller": "R", "Tylor Megill": "R", "Jose Quintana": "L",
    "Charlie Morton": "R", "Dane Dunning": "R", "Graham Ashcraft": "R",
    "Hayden Wesneski": "R", "Yu Darvish": "R", "Mitch Keller": "R",
    "Jameson Taillon": "R", "Shane McClanahan": "L", "Sonny Gray": "R",
    "Will Warren": "R", "Yusei Kikuchi": "L", "Ryne Nelson": "R",
    "Javier Assad": "R", "Mike Burrows": "R", "Janson Junk": "R",
    "Casey Mize": "R", "Brandon Williamson": "L", "Erick Fedde": "R",
    "Michael Wacha": "R", "Chris Bassitt": "R", "Brandon Pfaadt": "R",
    "Taijuan Walker": "R", "Landen Roupp": "R", "Bryce Elder": "R",
    "Jack Leiter": "R", "Lance McCullers Jr.": "R", "Kodai Senga": "R",
    "Clay Holmes": "R", "Braxton Ashcraft": "R", "Jacob Lopez": "R",
    "Martin Perez": "L", "Paul Blackburn": "R", "Steven Matz": "L",
    "Simeon Woods Richardson": "R", "Logan Gilbert": "R", "Nick Pivetta": "R",
    "Cole Ragans": "L", "Spencer Schwellenbach": "R", "Cade Horton": "R",
    "Miles Mikolas": "R", "Aaron Nola": "R", "Merrill Kelly": "R",
    "Patrick Detmers": "L", "Ryan Weathers": "L", "Colin Rea": "R",
    "Carmen Mlodzinski": "R", "Andrew Painter": "R", "David Peterson": "L",
    "Justin Wrobleski": "L", "Jeffrey Springs": "L", "Cade Cavalli": "R",
    "Frankie Montas": "R", "Foster Griffin": "L",
}

# ── Umpire Data (2026 updated) ──
UMPIRE_DATA = {
    "Junior Valentine": {"factor": 1.06, "zone": "Loose"},
    "Dan Iassogna":     {"factor": 1.05, "zone": "Loose"},
    "Adrian Johnson":   {"factor": 1.04, "zone": "Loose"},
    "Laz Diaz":         {"factor": 1.04, "zone": "Loose"},
    "CB Bucknor":       {"factor": 1.03, "zone": "Loose"},
    "Alan Porter":      {"factor": 1.04, "zone": "Loose"},
    "Brennan Miller":   {"factor": 1.03, "zone": "Loose"},
    "Alex MacKay":      {"factor": 1.02, "zone": "Average"},
    "Nestor Ceja":      {"factor": 1.02, "zone": "Average"},
    "Mark Carlson":     {"factor": 1.01, "zone": "Average"},
    "Phil Cuzzi":       {"factor": 1.01, "zone": "Average"},
    "Jim Reynolds":     {"factor": 1.01, "zone": "Average"},
    "David Rackley":    {"factor": 1.00, "zone": "Average"},
    "Nate Tomlinson":   {"factor": 1.00, "zone": "Average"},
    "John Tumpane":     {"factor": 1.00, "zone": "Average"},
    "Todd Tichenor":    {"factor": 1.00, "zone": "Average"},
    "Bill Miller":      {"factor": 1.00, "zone": "Average"},
    "Clint Vondrak":    {"factor": 0.99, "zone": "Average"},
    "Roberto Ortiz":    {"factor": 1.00, "zone": "Average"},
    "Jim Wolf":         {"factor": 1.00, "zone": "Average"},
    "Ryan Additon":     {"factor": 0.99, "zone": "Average"},
    "Vic Carapazza":    {"factor": 0.98, "zone": "Tight"},
    "Brian Gorman":     {"factor": 0.98, "zone": "Tight"},
    "Mike Everitt":     {"factor": 0.98, "zone": "Tight"},
    "Stu Scheurwater":  {"factor": 0.97, "zone": "Tight"},
    "Tim Timmons":      {"factor": 0.97, "zone": "Tight"},
    "Chris Guccione":   {"factor": 0.97, "zone": "Tight"},
    "Marvin Hudson":    {"factor": 0.96, "zone": "Tight"},
    "Doug Eddings":     {"factor": 0.96, "zone": "Tight"},
    "James Hoye":       {"factor": 0.96, "zone": "Tight"},
    "Jeremie Rehak":    {"factor": 0.95, "zone": "Tight"},
    "Mike DiMuro":      {"factor": 0.95, "zone": "Tight"},
    "Jerry Meals":      {"factor": 0.94, "zone": "Tight"},
    "Sam Holbrook":     {"factor": 0.94, "zone": "Tight"},
    "Mark Wegner":      {"factor": 0.93, "zone": "Tight"},
    "Lance Barrett":    {"factor": 0.93, "zone": "Tight"},
    "Larry Vanover":    {"factor": 0.97, "zone": "Tight"},
}

def get_umpire_data(ump_name):
    if not ump_name: return 1.0, "Average"
    for key, val in UMPIRE_DATA.items():
        if key.lower() in ump_name.lower() or ump_name.lower() in key.lower():
            return val["factor"], val["zone"]
    return 1.0, "Average"

# ── Stadium Orientation for Wind ──
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

# ── Rest adjustment ──
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

def apply_era_regression(era_val, ip):
    if era_val < ERA_REGRESSION_THRESHOLD and ip < ERA_REGRESSION_MIN_IP:
        return ERA_REGRESSION_FLOOR
    return era_val

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
                        return round(apply_era_regression(float(era), ip), 2), 'live'
    except Exception:
        pass
    for key in PITCHER_ERA_FALLBACK:
        if key.lower() in pitcher_name.lower() or pitcher_name.lower() in key.lower():
            return apply_era_regression(PITCHER_ERA_FALLBACK[key], 0), 'fallback'
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
        return apply_era_regression(round((total_er / total_ip) * 9, 2), total_ip)
    except Exception:
        return None

def blend_era(pitcher_name):
    season_era, src = fetch_live_sp_era(pitcher_name)
    recent = fetch_recent_era(pitcher_name)
    if recent is None:
        return season_era, None, src
    return round(season_era * 0.50 + recent * 0.50, 2), recent, src

@st.cache_data(ttl=3600)
def fetch_live_bullpen_era(team_name):
    import requests as _req
    season = datetime.today().year
    try:
        teams_resp = _req.get(f"https://statsapi.mlb.com/api/v1/teams?sportId=1&season={season}", timeout=8)
        if teams_resp.status_code != 200: return None
        team_id = None
        for t in teams_resp.json().get('teams', []):
            name = t.get('name', '')
            if name.lower() in team_name.lower() or team_name.lower() in name.lower():
                team_id = t['id']
                break
        if not team_id: return None
        p_resp = _req.get(
            f"https://statsapi.mlb.com/api/v1/teams/{team_id}/stats"
            f"?stats=season&group=pitching&season={season}&sportId=1", timeout=8)
        if p_resp.status_code != 200: return None
        for sg in p_resp.json().get('stats', []):
            splits = sg.get('splits', [])
            if splits:
                stat = splits[0].get('stat', {})
                era_val = stat.get('era')
                gp = int(stat.get('gamesPlayed', 0) or 0)
                if era_val and gp >= 5:
                    return round(float(era_val) * 1.08, 2)
    except Exception:
        pass
    return None

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

def get_bullpen_era(team_name):
    live = fetch_live_bullpen_era(team_name)
    if live: return live
    for key in TEAM_BULLPEN_FALLBACK:
        if key.lower() in team_name.lower() or team_name.lower() in key.lower():
            return TEAM_BULLPEN_FALLBACK[key]
    return LEAGUE_AVG_BULLPEN_ERA

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
    THRESHOLD = 35
    if angle_diff(wind_dir_deg, cf) <= THRESHOLD: return "Out CF"
    if angle_diff(wind_dir_deg, lf) <= THRESHOLD: return "Out LF"
    if angle_diff(wind_dir_deg, rf) <= THRESHOLD: return "Out RF"
    if angle_diff(wind_dir_deg, (cf + 180) % 360) <= THRESHOLD: return "In CF"
    if angle_diff(wind_dir_deg, (lf + 180) % 360) <= THRESHOLD: return "In LF"
    if angle_diff(wind_dir_deg, (rf + 180) % 360) <= THRESHOLD: return "In RF"
    lf_side = (lf + cf) / 2 % 360
    rf_side = (rf + cf) / 2 % 360
    if angle_diff(wind_dir_deg, lf_side) < angle_diff(wind_dir_deg, rf_side): return "L->R"
    return "R->L"

def wind_out_factor(wind_dir_deg, home_team):
    cf_bearing = STADIUM_CF_BEARING.get(home_team)
    if cf_bearing is None: return 0.0
    angle = (wind_dir_deg - cf_bearing + 180) % 360 - 180
    return round(math.cos(math.radians(angle)), 3)

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
            except: continue
        temp = temps[best_idx] if temps else None
        wspeed = wspeeds[best_idx] if wspeeds else 0
        wdir = wdirs[best_idx] if wdirs else 0
        precip = precip_probs[best_idx] if precip_probs else 0
        return {
            "dome": False, "temp_f": round(temp, 1) if temp else None,
            "wind_speed_mph": round(wspeed, 1) if wspeed else 0,
            "wind_dir_deg": round(wdir) if wdir else 0,
            "wind_dir_label": deg_to_label(wdir),
            "precip_pct": int(precip) if precip else 0,
        }
    except Exception:
        return None

# ══════════════════════════════════════════════════════════════════════
# V5.0 CORE: VEGAS-ANCHORED ADJUSTMENT MODEL
# ══════════════════════════════════════════════════════════════════════

def calc_sp_era_adj(pitcher_name, opposing_team, game_date, innings):
    """
    Calculate SP ERA adjustment vs league average.
    Positive = pitcher worse than avg (adds runs), Negative = pitcher better (removes runs).
    """
    era, recent, src = blend_era(pitcher_name)
    rest_adj, days_rest = get_rest_adj(pitcher_name, game_date)
    hand = PITCHER_HAND.get(pitcher_name, "R")
    era_with_rest = era + rest_adj
    # Adjustment = how many runs above/below league avg over innings pitched
    adj = round(((era_with_rest - LEAGUE_AVG_ERA) / 9) * innings * 0.5, 2)
    return adj, era, recent, src, rest_adj, days_rest, hand

def calc_bullpen_adj(team_name, innings):
    """Bullpen ERA adjustment vs league average for given innings."""
    bp_era = get_bullpen_era(team_name)
    adj = round(((bp_era - LEAGUE_AVG_BULLPEN_ERA) / 9) * innings, 2)
    return adj, bp_era

def calc_park_adj(home_team, vegas_line):
    """Park factor run adjustment — how many runs the park adds/removes."""
    pf = get_park_factor(home_team)
    # Convert multiplicative park factor to additive run adjustment
    adj = round((pf - 1.0) * vegas_line, 2)
    return adj, pf

def calc_weather_adj(weather, home_team, scale=1.0):
    """Weather run adjustment."""
    if not weather or weather.get("dome"): return 0.0, 0.0, None
    wspeed = weather.get("wind_speed_mph") or 0
    wdir = weather.get("wind_dir_deg") or 0
    w_adj, w_label = 0.0, None
    if wspeed and wspeed >= 8:
        factor = wind_out_factor(wdir, home_team)
        w_adj = round(factor * (wspeed / 10) * 0.3 * scale, 2)
        dir_label = wind_direction_label(wdir, home_team)
        if factor > 0.3: w_label = f"Out {dir_label}" if dir_label else "Out"
        elif factor < -0.3: w_label = f"In {dir_label}" if dir_label else "In"
        else: w_label = f"{dir_label}" if dir_label else "Cross"
    temp = weather.get("temp_f")
    t_adj = 0.0
    if temp and temp < 60:
        t_adj = round((60 - temp) * -0.015 * scale, 2)
    return w_adj, t_adj, w_label

def calc_ump_factor(game_id):
    ump_name = _todays_umps.get(str(game_id), "") if game_id else ""
    factor, zone = get_umpire_data(ump_name)
    return factor, zone, ump_name

def calc_adjusted_total_fg(away, home, away_pitcher, home_pitcher, vegas_line, weather, game_id, game_date):
    """
    V5.0 Vegas-anchored FG model.
    Start with Vegas line, apply our adjustments, return adjusted total.
    """
    if not vegas_line: return None, {}

    # SP adjustments (both pitchers affect runs scored by opposing team)
    away_sp_adj, away_era, away_recent, away_src, away_rest, away_days_rest, away_hand = \
        calc_sp_era_adj(away_pitcher, home, game_date, SP_INNINGS)
    home_sp_adj, home_era, home_recent, home_src, home_rest, home_days_rest, home_hand = \
        calc_sp_era_adj(home_pitcher, away, game_date, SP_INNINGS)

    # Bullpen adjustments (4 innings each)
    bp_inn = TOTAL_INNINGS - SP_INNINGS
    away_bp_adj, away_bp_era = calc_bullpen_adj(away, bp_inn)
    home_bp_adj, home_bp_era = calc_bullpen_adj(home, bp_inn)

    # Park adjustment
    park_adj, pf = calc_park_adj(home, vegas_line)

    # Weather adjustment
    w_adj, t_adj, w_label = calc_weather_adj(weather, home, scale=1.0)

    # Umpire
    ump_factor, ump_zone, ump_name = calc_ump_factor(game_id)

    # Total adjustment (sum of all factors)
    total_adj = away_sp_adj + home_sp_adj + away_bp_adj + home_bp_adj + park_adj + w_adj + t_adj
    # Apply umpire as a multiplier on the adjustments
    total_adj = round(total_adj * ump_factor, 2)

    # Adjusted total = Vegas line + our adjustments
    adjusted = round(vegas_line + total_adj, 1)

    detail = {
        "vegas_line": vegas_line, "adjusted_total": adjusted, "total_adj": total_adj,
        "away_era": away_era, "away_recent": away_recent, "away_src": away_src,
        "home_era": home_era, "home_recent": home_recent, "home_src": home_src,
        "away_sp_adj": away_sp_adj, "home_sp_adj": home_sp_adj,
        "away_bp_era": away_bp_era, "home_bp_era": home_bp_era,
        "away_bp_adj": away_bp_adj, "home_bp_adj": home_bp_adj,
        "park_adj": park_adj, "pf": pf,
        "wind_adj": w_adj, "temp_adj": t_adj, "wind_label": w_label,
        "ump_factor": ump_factor, "ump_zone": ump_zone, "ump_name": ump_name,
        "away_hand": away_hand, "home_hand": home_hand,
        "away_rest": away_rest, "away_days_rest": away_days_rest,
        "home_rest": home_rest, "home_days_rest": home_days_rest,
    }
    return adjusted, detail

def calc_adjusted_total_f5(away, home, away_pitcher, home_pitcher, vegas_f5_line, vegas_fg_line, weather, game_id, game_date):
    """
    V5.0 Vegas-anchored F5 model.
    Uses F5 Vegas line if available, otherwise derives from FG Vegas line.
    """
    # If no F5 Vegas line, derive from FG (F5 ≈ FG * 0.52)
    if not vegas_f5_line:
        if not vegas_fg_line: return None, {}
        vegas_f5_line = round(vegas_fg_line * 0.52, 1)
        derived = True
    else:
        derived = False

    away_sp_adj, away_era, away_recent, away_src, away_rest, away_days_rest, away_hand = \
        calc_sp_era_adj(away_pitcher, home, game_date, F5_INNINGS)
    home_sp_adj, home_era, home_recent, home_src, home_rest, home_days_rest, home_hand = \
        calc_sp_era_adj(home_pitcher, away, game_date, F5_INNINGS)

    park_adj, pf = calc_park_adj(home, vegas_f5_line)
    w_adj, t_adj, w_label = calc_weather_adj(weather, home, scale=F5_INNINGS/TOTAL_INNINGS)
    ump_factor, ump_zone, ump_name = calc_ump_factor(game_id)

    total_adj = away_sp_adj + home_sp_adj + park_adj + w_adj + t_adj
    total_adj = round(total_adj * ump_factor, 2)
    adjusted = round(vegas_f5_line + total_adj, 1)

    detail = {
        "vegas_line": vegas_f5_line, "adjusted_total": adjusted, "total_adj": total_adj,
        "derived_f5": derived,
        "away_era": away_era, "away_recent": away_recent, "away_src": away_src,
        "home_era": home_era, "home_recent": home_recent, "home_src": home_src,
        "away_sp_adj": away_sp_adj, "home_sp_adj": home_sp_adj,
        "park_adj": park_adj, "pf": pf,
        "wind_adj": w_adj, "temp_adj": t_adj, "wind_label": w_label,
        "ump_factor": ump_factor, "ump_zone": ump_zone, "ump_name": ump_name,
        "away_hand": away_hand, "home_hand": home_hand,
        "away_rest": away_rest, "away_days_rest": away_days_rest,
        "home_rest": home_rest, "home_days_rest": home_days_rest,
    }
    return adjusted, detail

# ── Probability ──
@st.cache_data(ttl=3600)
def poisson_over_prob(lam, line):
    k_max = int(line)
    cdf = sum((math.exp(-lam) * (lam ** k)) / math.factorial(k) for k in range(k_max + 1))
    return max(0.25, min(0.75, 1.0 - cdf))

@st.cache_data(ttl=300)
def monte_carlo_prob(model_total, line, n_sims=5000):
    over_count = 0
    for _ in range(n_sims):
        sim_total = max(2.0, model_total + random.gauss(0, 0.8))
        if random.random() < poisson_over_prob(sim_total, line):
            over_count += 1
    return over_count / n_sims

def model_to_prob_detail(model_total, line):
    p_poisson = poisson_over_prob(model_total, line)
    p_mc = monte_carlo_prob(model_total, line)
    p_final = max(0.25, min(0.75, 0.60 * p_mc + 0.40 * p_poisson))
    return {
        "poisson": round(p_poisson * 100, 1),
        "monte_carlo": round(p_mc * 100, 1),
        "final": round(p_final * 100, 1),
    }

def calc_kelly(edge):
    bet_pct = min((edge / 1.0) * KELLY_FRACTION, MAX_BET_PCT)
    return round(bet_pct * 100, 1), round(BANKROLL * bet_pct, 2)

def abbrev_pitcher(name, days_rest=None):
    if not name or name == "TBD": return "TBD"
    p = name.split()
    abbr = f"{p[0][0]}.{p[-1]}" if len(p) >= 2 else name
    if days_rest is not None and days_rest <= 3:
        abbr = f"!{abbr}"
    return abbr

# ── Odds API ──
@st.cache_data(ttl=300)
def fetch_odds_lines():
    try:
        api_key = get_secret("ODDS_API_KEY")
        if not api_key: return {}, {}
        resp = requests.get("https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/",
            params={"apiKey": api_key, "regions": "us", "markets": "totals",
                    "oddsFormat": "american", "dateFormat": "iso"}, timeout=10)
        if resp.status_code != 200: return {}, {}
        data = resp.json()
        if not isinstance(data, list): return {}, {}
        fg_result = {}
        event_ids = {}
        for game in data:
            away = game.get("away_team", "").lower()
            home = game.get("home_team", "").lower()
            event_id = game.get("id", "")
            if event_id: event_ids[(away, home)] = event_id
            fg_totals = []
            for bm in game.get("bookmakers", []):
                for mkt in bm.get("markets", []):
                    if mkt.get("key") != "totals": continue
                    for oc in mkt.get("outcomes", []):
                        if oc.get("name") == "Over":
                            fg_totals.append({"total": oc.get("point"), "odds": oc.get("price")})
            if fg_totals:
                m = sorted(fg_totals, key=lambda x: x["total"])[len(fg_totals) // 2]
                fg_result[(away, home)] = {"total": m["total"], "over_odds": m["odds"]}
        f5_result = {}
        for (away, home), event_id in event_ids.items():
            try:
                f5_resp = requests.get(
                    f"https://api.the-odds-api.com/v4/sports/baseball_mlb/events/{event_id}/odds",
                    params={"apiKey": api_key, "regions": "us",
                            "markets": "totals_1st_5_innings",
                            "oddsFormat": "american", "dateFormat": "iso"}, timeout=8)
                if f5_resp.status_code != 200: continue
                f5_data = f5_resp.json()
                f5_totals = []
                for bm in f5_data.get("bookmakers", []):
                    for mkt in bm.get("markets", []):
                        if mkt.get("key") != "totals_1st_5_innings": continue
                        for oc in mkt.get("outcomes", []):
                            if oc.get("name") == "Over":
                                point = oc.get("point")
                                if point and 3.0 <= float(point) <= 7.0:
                                    f5_totals.append({"total": point, "odds": oc.get("price")})
                if f5_totals:
                    m = sorted(f5_totals, key=lambda x: x["total"])[len(f5_totals) // 2]
                    f5_result[(away, home)] = {"total": m["total"], "over_odds": m["odds"]}
            except Exception:
                continue
        return fg_result, f5_result
    except Exception:
        return {}, {}

def match_odds(away, home, lines):
    for (ka, kh), data in lines.items():
        if (ka in away.lower() or away.lower() in ka) and (kh in home.lower() or home.lower() in kh):
            return data
    return None

# ── Kalshi Lines ──
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
            return {"**error**": f"No lines for {today}"}
        return result
    except Exception as e:
        return {"**error**": str(e)}

def match_kalshi(away, home, lines, mtype="full"):
    for (ka, kh, kt), data in lines.items():
        if kt != mtype: continue
        if (ka in away.lower() or away.lower() in ka) and (kh in home.lower() or home.lower() in kh):
            return data
    return None

# ── Settlement ──
def _team_match(stored, api_name):
    if not stored or not api_name: return False
    s, a = stored.lower().strip(), api_name.lower().strip()
    s_last = s.split()[-1] if s.split() else s
    a_last = a.split()[-1] if a.split() else a
    return s in a or a in s or s_last == a_last

def fetch_final_score(game_id=None, game_date=None, away_team=None, home_team=None):
    try:
        if game_id:
            try:
                games = statsapi.schedule(game_id=int(game_id), sportId=1)
                if games:
                    g = games[0]
                    if any(s.lower() in g.get('status', '').lower() for s in ['final', 'game over', 'completed']):
                        ar, hr = g.get('away_score'), g.get('home_score')
                        if ar is not None and hr is not None:
                            return int(ar), int(hr), int(ar) + int(hr)
            except Exception:
                pass
        if game_date:
            try:
                games = statsapi.schedule(date=game_date, sportId=1)
                if not games: return None
                for g in games:
                    if not (_team_match(away_team, g.get('away_name', '')) and
                            _team_match(home_team, g.get('home_name', ''))): continue
                    if not any(s.lower() in g.get('status', '').lower() for s in ['final', 'game over', 'completed']):
                        return None
                    ar, hr = g.get('away_score'), g.get('home_score')
                    if ar is None or hr is None: return None
                    return int(ar), int(hr), int(ar) + int(hr)
            except Exception:
                pass
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
            score = fetch_final_score(
                game_id=row.get("game_id"), game_date=row.get("game_date"),
                away_team=row.get("away_team"), home_team=row.get("home_team"))
            if not score:
                skipped += 1
                continue
            ar, hr, actual = score
            result, pnl = settle_result(
                actual, row.get("kalshi_line"), row.get("bet_direction"),
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
        msg = f"Auto-settlement: {settled} settled"
        if skipped: msg += f", {skipped} skipped"
        return msg
    except Exception:
        return None

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

# ── Signal Logic ──
def calc_signal(adjusted_total, kalshi_line, kalshi_price_cents, vegas_line=None):
    """
    V5.0 signal: compare adjusted total to Kalshi line.
    Requires Vegas line to be present for FG.
    Returns (lean, edge, prob_detail).
    """
    if not kalshi_line: return "EVEN", 0.0, {}
    prob_detail = model_to_prob_detail(adjusted_total, kalshi_line)
    model_prob = prob_detail["final"] / 100
    implied = kalshi_price_cents / 100
    over_edge = model_prob - implied
    under_edge = (1 - model_prob) - (1 - implied)
    if over_edge > under_edge and over_edge > 0:
        return "OVER", over_edge, prob_detail
    elif under_edge > over_edge and under_edge > 0:
        return "UNDER", under_edge, prob_detail
    return "EVEN", 0.0, prob_detail

def signal_label(lean, edge, require_vegas=False, has_vegas=False):
    if lean == "EVEN" or abs(edge) < EDGE_THRESHOLD: return "—", ""
    if require_vegas and not has_vegas: return "—", ""
    direction = "🟢 OVR" if lean == "OVER" else "🔴 UND"
    e = min(abs(edge) * 100, 20.0)
    if e >= 15: return "🔥 HOT", direction
    if e >= 10: return "⚡ EDGE", direction
    return "—", ""

def fmt_edge(edge, has_signal):
    if not has_signal: return "—"
    val = min(abs(edge) * 100, 20.0)
    sign = "+" if edge > 0 else ""
    suffix = "!" if abs(edge) * 100 > 20 else ""
    return f"{sign}{round(val, 1)}%{suffix}"

# ── Signal boxes in expander ──
def signal_boxes(adjusted_total, kalshi_line, price_cents, game_id, prefix,
                 away, home, ap, hp, market_type, today, vegas_line=None):
    if not kalshi_line:
        st.warning("No Kalshi line loaded.")
        return
    lean, edge, prob_detail = calc_signal(adjusted_total, kalshi_line, price_cents, vegas_line)
    auto_prob = int(prob_detail.get("final", 50))
    implied = price_cents / 100
    over_edge = (auto_prob / 100) - implied
    under_edge = (1 - auto_prob / 100) - (1 - implied)
    st.caption(
        f"Model: {prob_detail.get('final', 0)}% OVER | "
        f"Poisson: {prob_detail.get('poisson', 0)}% | "
        f"MC: {prob_detail.get('monte_carlo', 0)}% | "
        f"Implied: {round(implied * 100, 1)}%"
    )
    col_o, col_u = st.columns(2)
    with col_o:
        e = round(over_edge * 100, 1)
        if over_edge >= EDGE_THRESHOLD:
            _, bet_amt = calc_kelly(over_edge)
            st.success(f"OVER | Edge: +{e}% | Kelly: ${bet_amt}")
            if supabase_connected:
                placed = st.checkbox("Placed on Kalshi", key=f"placed_{prefix}_over_{game_id}")
                if placed:
                    real_amt = st.number_input("Real $ amount", min_value=1.0, max_value=500.0,
                        value=float(bet_amt), step=1.0, key=f"real_{prefix}_over_{game_id}")
                else:
                    real_amt = None
                if st.button(f"Log {prefix} OVER", key=f"log_{prefix}_over_{game_id}"):
                    if save_bet(today, away, home, ap, hp, adjusted_total, kalshi_line,
                                price_cents, auto_prob, auto_prob, over_edge, "OVER",
                                bet_amt, market_type, game_id, placed, real_amt):
                        st.success("Logged!")
        else:
            st.info(f"OVER | Edge: {e}%")
    with col_u:
        e = round(under_edge * 100, 1)
        if under_edge >= EDGE_THRESHOLD:
            _, bet_amt = calc_kelly(under_edge)
            st.success(f"UNDER | Edge: +{e}% | Kelly: ${bet_amt}")
            if supabase_connected:
                placed = st.checkbox("Placed on Kalshi", key=f"placed_{prefix}_under_{game_id}")
                if placed:
                    real_amt = st.number_input("Real $ amount", min_value=1.0, max_value=500.0,
                        value=float(bet_amt), step=1.0, key=f"real_{prefix}_under_{game_id}")
                else:
                    real_amt = None
                if st.button(f"Log {prefix} UNDER", key=f"log_{prefix}_under_{game_id}"):
                    if save_bet(today, away, home, ap, hp, adjusted_total, kalshi_line,
                                price_cents, auto_prob, auto_prob, under_edge, "UNDER",
                                bet_amt, market_type, game_id, placed, real_amt):
                        st.success("Logged!")
        else:
            st.info(f"UNDER | Edge: {e}%")

# ── Initialize live data ──
_todays_umps = fetch_todays_umpires()
_settlement_msg = run_auto_settlement()
kalshi_lines = fetch_kalshi_lines()
odds_lines, odds_f5_lines = fetch_odds_lines()

_kalshi_error = kalshi_lines.pop("**error**", None) if isinstance(kalshi_lines, dict) else None
full_ct = sum(1 for k in kalshi_lines if k[2] == "full") if kalshi_lines else 0
f5_ct = sum(1 for k in kalshi_lines if k[2] == "f5") if kalshi_lines else 0
kalshi_status = (f"Kalshi: {full_ct} full game, {f5_ct} F5 loaded"
                 if kalshi_lines else f"Kalshi: {_kalshi_error or 'unavailable'}")
odds_status = f"Odds API: {len(odds_lines)} FG, {len(odds_f5_lines)} F5" if odds_lines else "Odds API unavailable"

# ── Sidebar ──
with st.sidebar:
    st.markdown('<div class="section-header">System Status</div>', unsafe_allow_html=True)
    st.markdown(f"**Supabase:** {'✅ Connected' if supabase_connected else '❌ Not connected'}")
    _odds_key = get_secret("ODDS_API_KEY")
    st.markdown(f"**Odds API:** {'✅ Loaded' if _odds_key else '❌ Missing'}")
    if _odds_key: st.caption(f"Prefix: {_odds_key[:6]}...")
    st.markdown("**Weather:** Open-Meteo (free)")
    st.markdown(f"**Umpires:** {'✅' if _todays_umps else '⚠️'} {len(_todays_umps)} games")
    st.markdown("---")
    st.markdown("**V5.0 — Vegas-Anchored Model**")
    st.caption("Starts from Vegas line, applies ERA/bullpen/park/weather adjustments")
    st.caption("FG requires Vegas to signal")
    st.caption("F5 signals without Vegas when unavailable")
    st.caption(f"Edge threshold: {int(EDGE_THRESHOLD*100)}%")

# ── Tabs ──
tab1, tab2, tab3 = st.tabs(["Today's Games", "Settlement Tracker", "Calibration"])

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
            _row_errors = []

            for g in schedule:
                try:
                    if g.get('game_type', 'R') not in ('R', 'F', 'D', 'L', 'W'):
                        continue
                    home, away = g['home_name'], g['away_name']
                    hp = g.get('home_probable_pitcher', 'TBD')
                    ap = g.get('away_probable_pitcher', 'TBD')
                    et = (datetime.strptime(g['game_datetime'], '%Y-%m-%dT%H:%M:%SZ')
                          - timedelta(hours=4)).strftime('%I:%M %p')
                    game_id = str(g['game_id'])
                    game_date = today
                    dome = is_dome(home)
                    g_utc_hour = datetime.strptime(g['game_datetime'], '%Y-%m-%dT%H:%M:%SZ').hour
                    wx = fetch_stadium_weather(home, game_hour_utc=g_utc_hour)

                    # Get Vegas lines
                    _odds = match_odds(away, home, odds_lines)
                    _odds_f5 = match_odds(away, home, odds_f5_lines)
                    vegas_fg = float(_odds["total"]) if _odds else None
                    vegas_f5 = float(_odds_f5["total"]) if _odds_f5 else None
                    vegas_fg_str = str(vegas_fg) if vegas_fg else "-"
                    vegas_f5_str = str(vegas_f5) if vegas_f5 else "-"

                    # Get Kalshi lines
                    _kf = match_kalshi(away, home, kalshi_lines, "full")
                    _k5 = match_kalshi(away, home, kalshi_lines, "f5")
                    kalshi_fg_line = float(_kf["line"]) if _kf else None
                    kalshi_f5_line = float(_k5["line"]) if _k5 else None
                    kalshi_fg_price = int(_kf["over_price_cents"]) if _kf else 50
                    kalshi_f5_price = int(_k5["over_price_cents"]) if _k5 else 50

                    # V5.0: Calculate adjusted totals from Vegas anchor
                    adj_fg, fg_detail = calc_adjusted_total_fg(
                        away, home, ap, hp, vegas_fg, wx, game_id, game_date)
                    adj_f5, f5_detail = calc_adjusted_total_f5(
                        away, home, ap, hp, vegas_f5, vegas_fg, wx, game_id, game_date)

                    # Signals
                    fg_lean, fg_edge, fg_prob = calc_signal(adj_fg, kalshi_fg_line, kalshi_fg_price, vegas_fg)
                    f5_lean, f5_edge, f5_prob = calc_signal(adj_f5, kalshi_f5_line, kalshi_f5_price, vegas_f5)

                    # FG requires Vegas; F5 can fire without
                    fg_sig, fg_dir = signal_label(fg_lean, fg_edge, require_vegas=True, has_vegas=bool(vegas_fg))
                    f5_sig, f5_dir = signal_label(f5_lean, f5_edge, require_vegas=False, has_vegas=bool(vegas_f5))

                    fg_has_sig = fg_sig != "—"
                    f5_has_sig = f5_sig != "—"

                    # Conditions column
                    if dome:
                        cond = "Dome"
                    else:
                        pf = fg_detail.get("pf", 1.0) if fg_detail else 1.0
                        pf_icon = "Hit+" if pf >= 1.04 else "Hit" if pf > 1.0 else "Neu" if pf == 1.0 else "Pit"
                        cond = pf_icon
                        if wx and not wx.get("dome"):
                            wspeed = wx.get("wind_speed_mph", 0)
                            wdir = wx.get("wind_dir_deg", 0)
                            precip = wx.get("precip_pct", 0)
                            temp = wx.get("temp_f")
                            if wspeed and wspeed >= 5:
                                dir_label = wind_direction_label(wdir, home) or ""
                                cond += f" | {dir_label} {int(wspeed)}mph"
                            if precip and precip >= 20:
                                cond += f" Rain{precip}%"
                            if temp and temp < 50:
                                cond += f" {int(temp)}F"

                    ap_abbr = abbrev_pitcher(ap, f5_detail.get("away_days_rest") if f5_detail else None)
                    hp_abbr = abbrev_pitcher(hp, f5_detail.get("home_days_rest") if f5_detail else None)

                    # F5 row
                    f5_model_str = str(adj_f5) if adj_f5 else "-"
                    f5_line_str = f"{kalshi_f5_line}{'v' if _k5 else '~'}" if kalshi_f5_line else "-"
                    f5_sig_str = "—" if f5_sig == "—" else f"{f5_dir} {f5_sig}"
                    rows.append({
                        "Time": et, "Game": f"{abbrev_team(away)}@{abbrev_team(home)}",
                        "Away": ap_abbr, "Home": hp_abbr, "Cond": cond,
                        "Mkt": "F5", "Adj": f5_model_str,
                        "Kalshi": f5_line_str, "Vegas": vegas_f5_str,
                        "Edge": fmt_edge(f5_edge, f5_has_sig),
                        "Sig": f5_sig_str,
                    })

                    # FG row
                    fg_model_str = str(adj_fg) if adj_fg else "-"
                    fg_line_str = f"{kalshi_fg_line}{'v' if _kf else '~'}" if kalshi_fg_line else "-"
                    fg_sig_str = "—" if fg_sig == "—" else f"{fg_dir} {fg_sig}"
                    rows.append({
                        "Time": "", "Game": "", "Away": "", "Home": "", "Cond": "",
                        "Mkt": "FG", "Adj": fg_model_str,
                        "Kalshi": fg_line_str, "Vegas": vegas_fg_str,
                        "Edge": fmt_edge(fg_edge, fg_has_sig),
                        "Sig": fg_sig_str,
                    })

                except Exception as e:
                    _row_errors.append(f"{g.get('away_name','?')}@{g.get('home_name','?')}: {e}")
                    continue

            if _row_errors:
                with st.expander("⚠️ Row errors"):
                    for err in _row_errors:
                        st.caption(err)

            if rows:
                st.markdown("<div class='section-header'>Today's Slate</div>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    if kalshi_lines: st.success(kalshi_status)
                    else: st.warning(kalshi_status)
                with c2:
                    if odds_lines: st.success(odds_status)
                    else: st.warning(odds_status)

                view_type = st.radio("View", ["Mobile", "Desktop"], horizontal=True, label_visibility="collapsed")
                df_all = pd.DataFrame(rows)

                col_cfg = {
                    "Time":   st.column_config.TextColumn("Time", width="small"),
                    "Game":   st.column_config.TextColumn("Game", width="small"),
                    "Away":   st.column_config.TextColumn("Away SP", width="small"),
                    "Home":   st.column_config.TextColumn("Home SP", width="small"),
                    "Cond":   st.column_config.TextColumn("Cond", width="medium"),
                    "Mkt":    st.column_config.TextColumn("Mkt", width="small"),
                    "Adj":    st.column_config.TextColumn("Adj", width="small"),
                    "Kalshi": st.column_config.TextColumn("Kalshi", width="small"),
                    "Vegas":  st.column_config.TextColumn("Vegas", width="small"),
                    "Edge":   st.column_config.TextColumn("Edge", width="small"),
                    "Sig":    st.column_config.TextColumn("Sig", width="small"),
                }

                if view_type == "Mobile":
                    mob_cols = ["Time", "Game", "Mkt", "Adj", "Kalshi", "Vegas", "Edge", "Sig"]
                    st.dataframe(df_all[mob_cols].style.set_properties(**{'text-align': 'center'}),
                                 use_container_width=True, hide_index=True,
                                 column_config={k: col_cfg[k] for k in mob_cols})
                else:
                    desk_cols = ["Time", "Game", "Away", "Home", "Cond", "Mkt", "Adj", "Kalshi", "Vegas", "Edge", "Sig"]
                    st.dataframe(df_all[desk_cols].style.set_properties(**{'text-align': 'center'}),
                                 use_container_width=True, hide_index=True,
                                 column_config={k: col_cfg[k] for k in desk_cols})

                st.markdown("---")

            # ── Game Expanders ──
            for g in schedule:
                try:
                    if g.get('game_type', 'R') not in ('R', 'F', 'D', 'L', 'W'):
                        continue
                    home, away = g['home_name'], g['away_name']
                    hp = g.get('home_probable_pitcher', 'TBD')
                    ap = g.get('away_probable_pitcher', 'TBD')
                    et = (datetime.strptime(g['game_datetime'], '%Y-%m-%dT%H:%M:%SZ')
                          - timedelta(hours=4)).strftime('%I:%M %p ET')
                    game_id = str(g['game_id'])
                    game_date = today
                    g_utc_hour = datetime.strptime(g['game_datetime'], '%Y-%m-%dT%H:%M:%SZ').hour
                    wx = fetch_stadium_weather(home, game_hour_utc=g_utc_hour)

                    _odds = match_odds(away, home, odds_lines)
                    _odds_f5 = match_odds(away, home, odds_f5_lines)
                    vegas_fg = float(_odds["total"]) if _odds else None
                    vegas_f5 = float(_odds_f5["total"]) if _odds_f5 else None

                    _kf = match_kalshi(away, home, kalshi_lines, "full")
                    _k5 = match_kalshi(away, home, kalshi_lines, "f5")
                    kalshi_fg_line = float(_kf["line"]) if _kf else None
                    kalshi_f5_line = float(_k5["line"]) if _k5 else None
                    kalshi_fg_price = int(_kf["over_price_cents"]) if _kf else 50
                    kalshi_f5_price = int(_k5["over_price_cents"]) if _k5 else 50

                    adj_fg, fg_detail = calc_adjusted_total_fg(
                        away, home, ap, hp, vegas_fg, wx, game_id, game_date)
                    adj_f5, f5_detail = calc_adjusted_total_f5(
                        away, home, ap, hp, vegas_f5, vegas_fg, wx, game_id, game_date)

                    with st.expander(f"**{away} @ {home}** — {et}"):
                        # SP Info
                        a_src = 'LIVE' if f5_detail.get('away_src') == 'live' else 'FB'
                        h_src = 'LIVE' if f5_detail.get('home_src') == 'live' else 'FB'
                        a_rest = f" | Rest: {f5_detail.get('away_days_rest')}d ({f5_detail.get('away_rest',0):+.2f})" if f5_detail.get('away_days_rest') else ""
                        h_rest = f" | Rest: {f5_detail.get('home_days_rest')}d ({f5_detail.get('home_rest',0):+.2f})" if f5_detail.get('home_days_rest') else ""
                        st.markdown(
                            f"**Away SP:** {ap} ({f5_detail.get('away_hand','R')}HP) | ERA: {f5_detail.get('away_era','?')} [{a_src}]{a_rest}  \n"
                            f"**Home SP:** {hp} ({f5_detail.get('home_hand','R')}HP) | ERA: {f5_detail.get('home_era','?')} [{h_src}]{h_rest}"
                        )

                        # Umpire
                        ump = f5_detail.get('ump_name', '')
                        if ump:
                            zone = f5_detail.get('ump_zone', 'Average')
                            factor = f5_detail.get('ump_factor', 1.0)
                            st.caption(f"Ump: {ump} | Zone: {zone} | Factor: {factor:.2f}")
                        else:
                            st.caption("Ump: Not yet announced")

                        # Weather
                        if wx is None: wx_str = "Weather unavailable"
                        elif wx.get("dome"): wx_str = "Dome - weather N/A"
                        else:
                            temp = wx.get("temp_f")
                            wspeed = wx.get("wind_speed_mph", 0)
                            wdir = wx.get("wind_dir_deg", 0)
                            precip = wx.get("precip_pct", 0)
                            dir_label = wind_direction_label(wdir, home) or wx.get("wind_dir_label", "")
                            wx_str = f"{temp}F | {int(wspeed)}mph {dir_label}" if temp else "No temp data"
                            if precip and precip >= 20: wx_str += f" | Rain: {precip}%"

                        cA, cB = st.columns(2)
                        with cA:
                            pf = fg_detail.get("pf", 1.0) if fg_detail else 1.0
                            pf_label = "Hitter+" if pf >= 1.04 else "Hitter" if pf > 1.0 else "Neutral" if pf == 1.0 else "Pitcher"
                            st.metric("Park", f"{pf:.2f}", delta=pf_label)
                        with cB:
                            st.info(wx_str)

                        st.markdown("---")

                        # ── F5 Section ──
                        st.markdown("**First 5 Innings**")
                        if adj_f5:
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                derived_note = " (derived)" if f5_detail.get("derived_f5") else ""
                                st.metric("Vegas F5", f"{f5_detail.get('vegas_line','?')}{derived_note}")
                            with c2:
                                st.metric("Adj Total", adj_f5)
                            with c3:
                                st.metric("Adjustment", f"{f5_detail.get('total_adj',0):+.2f}")
                            with st.expander("F5 adjustment breakdown"):
                                st.caption(f"Away SP ({ap}): ERA {f5_detail.get('away_era','?')} → adj {f5_detail.get('away_sp_adj',0):+.2f}")
                                st.caption(f"Home SP ({hp}): ERA {f5_detail.get('home_era','?')} → adj {f5_detail.get('home_sp_adj',0):+.2f}")
                                st.caption(f"Park factor {f5_detail.get('pf',1.0):.2f} → adj {f5_detail.get('park_adj',0):+.2f}")
                                if f5_detail.get('wind_adj', 0) != 0:
                                    st.caption(f"Wind ({f5_detail.get('wind_label','')}) → adj {f5_detail.get('wind_adj',0):+.2f}")
                                if f5_detail.get('temp_adj', 0) != 0:
                                    st.caption(f"Temp → adj {f5_detail.get('temp_adj',0):+.2f}")
                                st.caption(f"Ump factor: {f5_detail.get('ump_factor',1.0):.2f}")

                            if _k5:
                                st.success(f"Kalshi F5: {kalshi_f5_line} | Over: {kalshi_f5_price}c")
                            else:
                                st.caption("F5 Kalshi line not loaded")
                            f5_line_in = st.number_input("F5 Line", 0.0, 15.0,
                                float(kalshi_f5_line or adj_f5 or 4.5), 0.5, key=f"f5l_{game_id}")
                            f5_price_in = st.number_input("F5 Over Price (c)", 1, 99,
                                kalshi_f5_price, 1, key=f"f5p_{game_id}")
                            signal_boxes(adj_f5, f5_line_in, f5_price_in, game_id,
                                        "F5", away, home, ap, hp, "f5", today, vegas_f5)
                        else:
                            st.info("No Vegas line available for F5 model.")

                        st.markdown("---")

                        # ── FG Section ──
                        st.markdown("**Full Game**")
                        if adj_fg:
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                st.metric("Vegas FG", f"{fg_detail.get('vegas_line','?')}")
                            with c2:
                                st.metric("Adj Total", adj_fg)
                            with c3:
                                st.metric("Adjustment", f"{fg_detail.get('total_adj',0):+.2f}")
                            with st.expander("FG adjustment breakdown"):
                                st.caption(f"Away SP ({ap}): ERA {fg_detail.get('away_era','?')} → adj {fg_detail.get('away_sp_adj',0):+.2f}")
                                st.caption(f"Home SP ({hp}): ERA {fg_detail.get('home_era','?')} → adj {fg_detail.get('home_sp_adj',0):+.2f}")
                                st.caption(f"Away bullpen ERA {fg_detail.get('away_bp_era','?')} → adj {fg_detail.get('away_bp_adj',0):+.2f}")
                                st.caption(f"Home bullpen ERA {fg_detail.get('home_bp_era','?')} → adj {fg_detail.get('home_bp_adj',0):+.2f}")
                                st.caption(f"Park factor {fg_detail.get('pf',1.0):.2f} → adj {fg_detail.get('park_adj',0):+.2f}")
                                if fg_detail.get('wind_adj', 0) != 0:
                                    st.caption(f"Wind ({fg_detail.get('wind_label','')}) → adj {fg_detail.get('wind_adj',0):+.2f}")
                                if fg_detail.get('temp_adj', 0) != 0:
                                    st.caption(f"Temp → adj {fg_detail.get('temp_adj',0):+.2f}")
                                st.caption(f"Ump factor: {fg_detail.get('ump_factor',1.0):.2f}")

                            if _odds:
                                st.info(f"Vegas: {vegas_fg} | Over odds: {_odds.get('over_odds','?')}")
                            if _kf:
                                st.success(f"Kalshi FG: {kalshi_fg_line} | Over: {kalshi_fg_price}c")
                            else:
                                st.caption("Full game Kalshi line not loaded")
                            fg_line_in = st.number_input("FG Line", 0.0, 20.0,
                                float(kalshi_fg_line or adj_fg or 8.5), 0.5, key=f"fgl_{game_id}")
                            fg_price_in = st.number_input("FG Over Price (c)", 1, 99,
                                kalshi_fg_price, 1, key=f"fgp_{game_id}")
                            signal_boxes(adj_fg, fg_line_in, fg_price_in, game_id,
                                        "FG", away, home, ap, hp, "full", today, vegas_fg)
                        else:
                            st.warning("No Vegas FG line — FG signals require Vegas.")

                except Exception as ge:
                    st.warning(f"Could not load game: {ge}")
                    continue

    except Exception as e:
        st.error(f"Error loading schedule: {e}")

with tab2:
    st.markdown("**Settlement Tracker**")
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
                            pnl = round(settled["profit_loss"].sum(), 2)
                        m1, m2, m3, m4, m5 = st.columns(5)
                        m1.metric("Total Bets", len(settled))
                        m2.metric("Record", f"{wins}W-{losses}L-{pushes}P")
                        m3.metric("Win %", f"{wp}%")
                        m4.metric("Total P&L", f"${pnl:+.2f}")
                        m5.metric("Unsettled", len(df[df["result"].isna()]))
                        st.markdown("---")

                    base_cols = ["game_date", "away_team", "home_team", "market_type",
                                 "model_total", "kalshi_line", "bet_direction", "bet_amount"]
                    if view_mode == "Real Kalshi Bets Only":
                        base_cols.append("real_amount")
                        if all(c in df.columns for c in ["real_amount", "profit_loss", "bet_amount"]):
                            df = df.copy()
                            def calc_real_pnl(row):
                                real = row.get("real_amount") or row.get("bet_amount") or 0
                                model = row.get("bet_amount") or 25
                                pnl = row.get("profit_loss") or 0
                                return round(pnl * (real / model), 2) if model > 0 else pnl
                            df["real_PL"] = df.apply(calc_real_pnl, axis=1)
                            base_cols.append("real_PL")
                    base_cols += ["actual_total", "result", "profit_loss", "settled_at"]
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
    st.markdown("**Model Calibration**")
    if supabase_connected:
        try:
            data = supabase.table("mlb_settlements").select("*").execute()
            if data.data:
                df_cal = pd.DataFrame(data.data)
                settled = df_cal[df_cal["result"].notna()].copy()
                if len(settled) < 5:
                    st.info("Need at least 5 settled bets for calibration.")
                else:
                    wins = (settled["result"] == "WIN").sum()
                    losses = (settled["result"] == "LOSS").sum()
                    total = wins + losses
                    actual_win_rate = round(wins / total * 100, 1) if total > 0 else 0
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Actual Win Rate", f"{actual_win_rate}%")
                    c2.metric("Total Settled", total)
                    c3.metric("Total P&L", f"${round(settled['profit_loss'].sum(), 2):+.2f}")
                    st.markdown("---")

                    if "market_type" in settled.columns:
                        st.markdown("**F5 vs Full Game**")
                        for mtype in ["f5", "full"]:
                            subset = settled[settled["market_type"] == mtype]
                            if len(subset) > 0:
                                w = (subset["result"] == "WIN").sum()
                                l = (subset["result"] == "LOSS").sum()
                                wr = round(w/(w+l)*100, 1) if (w+l) > 0 else 0
                                pnl = round(subset["profit_loss"].sum(), 2)
                                label = "First 5 Innings" if mtype == "f5" else "Full Game"
                                st.markdown(f"**{label}:** {w}W-{l}L ({wr}%) | P&L: ${pnl:+.2f}")
                    st.markdown("---")

                    if "bet_direction" in settled.columns:
                        st.markdown("**OVER vs UNDER**")
                        for direction in ["OVER", "UNDER"]:
                            subset = settled[settled["bet_direction"] == direction]
                            if len(subset) > 0:
                                w = (subset["result"] == "WIN").sum()
                                l = (subset["result"] == "LOSS").sum()
                                wr = round(w/(w+l)*100, 1) if (w+l) > 0 else 0
                                pnl = round(subset["profit_loss"].sum(), 2)
                                st.markdown(f"**{direction}:** {w}W-{l}L ({wr}%) | P&L: ${pnl:+.2f}")
                    st.markdown("---")

                    if actual_win_rate > 58:
                        st.success(f"{actual_win_rate}% — consider increasing sizing")
                    elif actual_win_rate > 53:
                        st.info(f"{actual_win_rate}% — solid, maintain current sizing")
                    elif actual_win_rate > 50:
                        st.warning(f"{actual_win_rate}% — marginal, do not increase sizing")
                    else:
                        st.error(f"{actual_win_rate}% — below 50%, review model inputs")
                    if len(settled) < 50:
                        st.caption(f"Only {len(settled)} settled bets — need 50+ for reliable calibration")
            else:
                st.info("No settled bets yet.")
        except Exception as e:
            st.error(f"Calibration error: {e}")
    else:
        st.warning("Supabase not connected.")
