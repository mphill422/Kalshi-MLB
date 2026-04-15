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
    <div class="mph-badge">V4.32</div>
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

# ── Default line values — if Kalshi line matches these AND Odds API is down,
#    skip the bet entirely. This protects against false edge on default lines.
DEFAULT_FG_LINE = 8.5
DEFAULT_F5_LINE = 4.5

try:
    supabase = create_client(
        st.secrets["supabase"]["url"],
