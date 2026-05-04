import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
from supabase import create_client
import math
from collections import defaultdict

ET_OFFSET = timezone(timedelta(hours=-4))

def today_et():
    return datetime.now(ET_OFFSET).strftime('%Y-%m-%d')

def now_et():
    return datetime.now(ET_OFFSET)

st.set_page_config(page_title="MPH Tennis Model", layout="wide", page_icon="🎾")

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
      <div class="mph-login-title">🎾 MPH Tennis Model <span class="mph-login-badge">Private</span></div>
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
.mph-header { background: linear-gradient(135deg, #0a2818 0%, #0d3c1f 50%, #071a0e 100%); border-bottom: 1px solid #00ff8844; padding: 16px 24px 14px 24px; margin: -1rem -1rem 1.5rem -1rem; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 24px #00ff8811; }
.mph-title { font-size: 1.5rem; font-weight: 900; letter-spacing: -1px; color: #ffffff; }
.mph-title span { color: #00ff88; }
.mph-badge { background: linear-gradient(135deg, #00ff8822, #00d4ff22); border: 1px solid #00ff8855; color: #00ff88; font-size: 0.65rem; font-weight: 800; padding: 3px 10px; border-radius: 20px; letter-spacing: 2px; text-transform: uppercase; }
.mph-sub { color: #3a7050; font-size: 0.75rem; margin-top: 3px; }
.pill-live { display: inline-block; background: #00ff8811; border: 1px solid #00ff8844; color: #00ff88; font-size: 0.6rem; font-weight: 800; padding: 2px 8px; border-radius: 20px; letter-spacing: 2px; text-transform: uppercase; margin-left: 8px; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.5; } }
.section-header { font-size: 0.65rem; font-weight: 800; letter-spacing: 3px; text-transform: uppercase; color: #00ff88; border-bottom: 1px solid #00ff8822; padding-bottom: 6px; margin: 1.5rem 0 1rem 0; }
div[data-testid="metric-container"] { background: linear-gradient(135deg, #0d2d1a, #0a2214) !important; border: 1px solid #1e5f3a !important; border-radius: 10px !important; padding: 12px 16px !important; transition: all 0.2s; box-shadow: 0 2px 12px #00000044; }
div[data-testid="metric-container"]:hover { border-color: #00ff8866 !important; box-shadow: 0 4px 20px #00ff8811 !important; transform: translateY(-1px); }
div[data-testid="metric-container"] label { color: #3a7050 !important; font-size: 0.65rem !important; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600 !important; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #e8ffe8 !important; font-size: 1.4rem !important; font-weight: 800 !important; }
details { background: linear-gradient(135deg, #0d2d1a, #0a2214) !important; border: 1px solid #1a5030 !important; border-radius: 10px !important; margin-bottom: 8px !important; transition: all 0.2s; box-shadow: 0 2px 12px #00000033; }
details:hover { border-color: #00ff8844 !important; }
details summary { font-weight: 700 !important; color: #c8f0d8 !important; padding: 12px 16px !important; }
details[open] { border-color: #00ff8855 !important; box-shadow: 0 4px 20px #00ff880a !important; }
.stButton > button { background: linear-gradient(135deg, #0d2d1a, #0a2214) !important; border: 1px solid #00ff8844 !important; color: #00ff88 !important; border-radius: 8px !important; font-weight: 700 !important; font-size: 0.82rem !important; width: 100% !important; transition: all 0.2s !important; letter-spacing: 0.5px; }
.stButton > button:hover { background: linear-gradient(135deg, #00ff8818, #00d4ff11) !important; border-color: #00ff88 !important; box-shadow: 0 4px 16px #00ff8822 !important; }
.stDataFrame { border-radius: 10px !important; border: 1px solid #1a5030 !important; overflow: hidden !important; box-shadow: 0 4px 24px #00000044 !important; }
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #080c18, #05080f) !important; border-right: 1px solid #1a5030 !important; }
.stTabs [data-baseweb="tab-list"] { background: #0d2d1a !important; border-radius: 10px !important; padding: 4px !important; gap: 4px !important; border: 1px solid #1a5030 !important; }
.stTabs [data-baseweb="tab"] { color: #3a7050 !important; font-weight: 700 !important; border-radius: 8px !important; font-size: 0.82rem !important; letter-spacing: 0.5px; }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg, #00ff8822, #00d4ff22) !important; color: #00ff88 !important; border: 1px solid #00ff8833 !important; }
@media (max-width: 768px) { .mph-title { font-size: 1.1rem !important; } div[data-testid="metric-container"] { padding: 8px 10px !important; } div[data-testid="metric-container"] div[data-testid="stMetricValue"] { font-size: 1.1rem !important; } .stDataFrame { font-size: 0.7rem !important; } details summary { font-size: 0.82rem !important; padding: 10px 14px !important; } }
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="mph-header">
  <div>
    <div class="mph-title">🎾 MPH <span>Tennis</span> Model</div>
    <div class="mph-sub">Surface Elo + Form + H2H + Shadow Validation &nbsp;<span class="pill-live">&#9679; LIVE</span></div>
  </div>
  <div style="text-align:right">
    <div class="mph-badge">V1.1</div>
    <div class="mph-sub" style="margin-top:4px">{now_et().strftime('%b %d, %Y &middot; %-I:%M %p ET')}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Constants ──
BANKROLL = 500
EDGE_MIN = 0.05
EDGE_MAX = 0.12
KELLY_FRACTION = 0.5
MAX_BET_PCT = 0.05
INITIAL_ELO = 1500
K_FACTOR = 32
SURFACE_WEIGHT = 0.70
RECENT_FORM_WINDOW = 20
CONV_HIGH_MIN = 6
CONV_MED_MIN = 4

# ── Supabase ──
try:
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    supabase_connected = True
except Exception:
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

# ─── NAME NORMALIZATION ───────────────────────────────────────────────────
# Tennis player names are inconsistent across sources:
#   Sackmann: "Jannik Sinner"
#   API-Odds: "jannik sinner" (lowercase)
#   Kalshi:   "Sinner" (last name only) or "Sinner vs Zverev"
# We normalize for matching but preserve display names.

def normalize_name(name):
    """Lowercase, strip whitespace, remove diacritics-ish, single spaces."""
    if not name: return ""
    return " ".join(name.lower().strip().split())

def last_name(name):
    """Extract last name for fuzzy matching."""
    parts = normalize_name(name).split()
    return parts[-1] if parts else ""

def names_match(a, b):
    """True if two names plausibly refer to the same person."""
    if not a or not b: return False
    na, nb = normalize_name(a), normalize_name(b)
    if na == nb: return True
    if na in nb or nb in na: return True
    if last_name(a) == last_name(b) and last_name(a):
        return True
    return False

def display_name(name):
    """Title-case for display."""
    if not name: return ""
    return " ".join(w.capitalize() for w in name.split())

# ─── ELO STATE (loaded from Supabase, cached per session) ──────────────────
@st.cache_data(ttl=300)
def load_player_elos():
    """Load all player Elo ratings. Returns dicts keyed by 'TOUR|name_lower'."""
    if not supabase_connected:
        return {}, {"Hard": {}, "Clay": {}, "Grass": {}}
    try:
        rows = supabase.table("tennis_player_elos").select("*").execute().data or []
        overall = {}
        surface = {"Hard": {}, "Clay": {}, "Grass": {}}
        for r in rows:
            name = r.get("player_name", "")
            tour = r.get("tour", "ATP")
            key = f"{tour}|{normalize_name(name)}"
            overall[key] = float(r.get("elo_overall", INITIAL_ELO))
            surface["Hard"][key] = float(r.get("elo_hard", INITIAL_ELO))
            surface["Clay"][key] = float(r.get("elo_clay", INITIAL_ELO))
            surface["Grass"][key] = float(r.get("elo_grass", INITIAL_ELO))
        return overall, surface
    except Exception:
        return {}, {"Hard": {}, "Clay": {}, "Grass": {}}

@st.cache_data(ttl=300)
def load_recent_form(tour, player_name, n=RECENT_FORM_WINDOW):
    """Load player's last N match results from history. Returns list of 1/0."""
    if not supabase_connected: return []
    try:
        # Two queries: as winner, as loser. Merge by date, take last N.
        wins = (supabase.table("tennis_match_results")
                .select("match_date")
                .eq("tour", tour).eq("winner_name", player_name)
                .order("match_date", desc=True).limit(n).execute().data or [])
        losses = (supabase.table("tennis_match_results")
                  .select("match_date")
                  .eq("tour", tour).eq("loser_name", player_name)
                  .order("match_date", desc=True).limit(n).execute().data or [])
        all_matches = [(r["match_date"], 1) for r in wins] + [(r["match_date"], 0) for r in losses]
        all_matches.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in all_matches[:n]]
    except Exception:
        return []

@st.cache_data(ttl=300)
def load_h2h(tour, p1_name, p2_name):
    """Get head-to-head record between two players. Returns (p1_wins, p2_wins)."""
    if not supabase_connected: return (0, 0)
    try:
        r1 = (supabase.table("tennis_match_results").select("id")
              .eq("tour", tour).eq("winner_name", p1_name).eq("loser_name", p2_name)
              .execute().data or [])
        r2 = (supabase.table("tennis_match_results").select("id")
              .eq("tour", tour).eq("winner_name", p2_name).eq("loser_name", p1_name)
              .execute().data or [])
        return (len(r1), len(r2))
    except Exception:
        return (0, 0)

# ─── PREDICTION ENGINE ────────────────────────────────────────────────────
def get_blended_elo(player_key, surface, overall_elos, surface_elos):
    overall = overall_elos.get(player_key, INITIAL_ELO)
    surf = surface_elos.get(surface, {}).get(player_key, INITIAL_ELO)
    return SURFACE_WEIGHT * surf + (1 - SURFACE_WEIGHT) * overall

def predict_match(tour, p1_display, p2_display, surface, overall_elos, surface_elos):
    """Return (P(p1 beats p2), detail dict). Names handled case-insensitively."""
    p1_key = f"{tour}|{normalize_name(p1_display)}"
    p2_key = f"{tour}|{normalize_name(p2_display)}"

    e1 = get_blended_elo(p1_key, surface, overall_elos, surface_elos)
    e2 = get_blended_elo(p2_key, surface, overall_elos, surface_elos)

    form1 = load_recent_form(tour, p1_display)
    form2 = load_recent_form(tour, p2_display)
    f1_pct = sum(form1) / len(form1) if form1 else 0.5
    f2_pct = sum(form2) / len(form2) if form2 else 0.5
    form_adj = (f1_pct - f2_pct) * 30

    h2h_p1, h2h_p2 = load_h2h(tour, p1_display, p2_display)
    h2h_total = h2h_p1 + h2h_p2
    h2h_adj = (h2h_p1 - h2h_p2) * 8 if h2h_total >= 3 else 0

    diff = (e1 - e2) + form_adj + h2h_adj
    p1_prob = 1 / (1 + 10 ** (-diff / 400))
    return p1_prob, {
        "p1_elo_blended": round(e1, 1),
        "p2_elo_blended": round(e2, 1),
        "p1_elo_overall": overall_elos.get(p1_key, INITIAL_ELO),
        "p2_elo_overall": overall_elos.get(p2_key, INITIAL_ELO),
        "p1_elo_surface": surface_elos.get(surface, {}).get(p1_key, INITIAL_ELO),
        "p2_elo_surface": surface_elos.get(surface, {}).get(p2_key, INITIAL_ELO),
        "elo_diff": round(diff, 1),
        "p1_form": f1_pct,
        "p2_form": f2_pct,
        "p1_form_n": len(form1),
        "p2_form_n": len(form2),
        "form_adj": round(form_adj, 1),
        "h2h_p1": h2h_p1,
        "h2h_p2": h2h_p2,
        "h2h_adj": round(h2h_adj, 1),
        "surface": surface,
        "elo_data_present": (p1_key in overall_elos) and (p2_key in overall_elos),
    }

# ─── CONVICTION ────────────────────────────────────────────────────────────
def score_elo_gap(detail):
    diff = abs(detail.get("elo_diff", 0))
    if diff >= 150: return 2, f"Elo gap: {diff:.0f} (decisive)"
    if diff >= 75: return 1, f"Elo gap: {diff:.0f} (moderate)"
    return 0, f"Elo gap: {diff:.0f} (small)"

def score_surface_specialization(detail):
    if not detail.get("elo_data_present"):
        return 0, "Surface: insufficient Elo data"
    p1_surf = detail.get("p1_elo_surface", INITIAL_ELO)
    p2_surf = detail.get("p2_elo_surface", INITIAL_ELO)
    p1_overall = detail.get("p1_elo_overall", INITIAL_ELO)
    p2_overall = detail.get("p2_elo_overall", INITIAL_ELO)
    surf_diff = p1_surf - p2_surf
    overall_diff = p1_overall - p2_overall
    same_direction = (surf_diff > 0) == (overall_diff > 0)
    surf_stronger = abs(surf_diff) > abs(overall_diff)
    if same_direction and surf_stronger:
        return 2, f"Surface confirms favorite ({detail['surface']})"
    if same_direction:
        return 1, f"Surface aligns with overall ({detail['surface']})"
    return 0, f"Surface conflicts with overall ({detail['surface']})"

def score_form_alignment(detail):
    p1_form_n = detail.get("p1_form_n", 0)
    p2_form_n = detail.get("p2_form_n", 0)
    if p1_form_n < 5 or p2_form_n < 5:
        return 0, "Form: insufficient sample"
    f1, f2 = detail.get("p1_form", 0.5), detail.get("p2_form", 0.5)
    elo_diff = detail.get("elo_diff", 0)
    form_diff = f1 - f2
    same = (elo_diff > 0) == (form_diff > 0)
    if same and abs(form_diff) >= 0.20:
        return 2, f"Form: {f1*100:.0f}% vs {f2*100:.0f}% (strong align)"
    if same:
        return 1, f"Form: {f1*100:.0f}% vs {f2*100:.0f}% (mild align)"
    return 0, f"Form: {f1*100:.0f}% vs {f2*100:.0f}% (conflict)"

def score_h2h(detail):
    h2h_p1 = detail.get("h2h_p1", 0)
    h2h_p2 = detail.get("h2h_p2", 0)
    total = h2h_p1 + h2h_p2
    if total < 3:
        return 0, f"H2H: {h2h_p1}-{h2h_p2} (insufficient)"
    elo_diff = detail.get("elo_diff", 0)
    h2h_diff = h2h_p1 - h2h_p2
    same = (elo_diff > 0) == (h2h_diff > 0)
    if same and total >= 5 and abs(h2h_diff) >= 2:
        return 2, f"H2H: {h2h_p1}-{h2h_p2} (strong align)"
    if same:
        return 1, f"H2H: {h2h_p1}-{h2h_p2} (mild align)"
    return 0, f"H2H: {h2h_p1}-{h2h_p2} (conflict)"

def calc_conviction(detail):
    s1, r1 = score_elo_gap(detail)
    s2, r2 = score_surface_specialization(detail)
    s3, r3 = score_form_alignment(detail)
    s4, r4 = score_h2h(detail)
    total = s1 + s2 + s3 + s4
    if total >= CONV_HIGH_MIN:
        tier, icon, label = "HIGH", "🔵", "🔵 HIGH"
    elif total >= CONV_MED_MIN:
        tier, icon, label = "MED", "🟡", "🟡 MED"
    else:
        tier, icon, label = "LOW", "⚪", "⚪ LOW"
    return {
        "score": total, "max_score": 8, "tier": tier, "icon": icon, "label": label,
        "signals": [
            {"name": "Elo gap magnitude", "points": s1, "detail": r1},
            {"name": "Surface specialization", "points": s2, "detail": r2},
            {"name": "Form alignment", "points": s3, "detail": r3},
            {"name": "Head-to-head", "points": s4, "detail": r4},
        ],
    }

# ─── KALSHI LINES ──────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def fetch_kalshi_tennis_lines():
    """Loads tennis match lines from Supabase (populated by Edge Function)."""
    if not supabase_connected:
        return {"**error**": "Supabase not connected"}
    try:
        today = today_et()
        rows = (supabase.table("tennis_kalshi_lines")
                .select("*").eq("match_date", today).execute().data or [])
        result = {}
        for row in rows:
            tour = (row.get("tour") or "ATP").upper()
            p1 = normalize_name(row.get("player1") or "")
            p2 = normalize_name(row.get("player2") or "")
            if not p1 or not p2: continue
            result[(tour, p1, p2)] = {
                "p1_yes_cents": int(row.get("p1_yes_cents") or 50),
                "p2_yes_cents": int(row.get("p2_yes_cents") or 50),
                "ticker": row.get("ticker", ""),
                "tournament": row.get("tournament", ""),
                "round": row.get("round", ""),
                "surface": row.get("surface", "Hard"),
                "match_time": row.get("match_time", ""),
            }
        if not result:
            return {"**error**": f"No lines for {today}"}
        return result
    except Exception as e:
        return {"**error**": str(e)}

# ─── ODDS API (tennis) — DYNAMIC TOURNAMENT DISCOVERY ─────────────────────
# Tennis sport keys are PER TOURNAMENT and only active during the tournament.
# We discover what's currently active each session.
TENNIS_PREFIXES = ("tennis_atp", "tennis_wta")

def _classify_tour(sport_key):
    if sport_key.startswith("tennis_atp"): return "ATP"
    if sport_key.startswith("tennis_wta"): return "WTA"
    return None

def _infer_surface_from_key(sport_key, sport_title):
    """Best-effort surface inference from tournament name."""
    text = (sport_key + " " + (sport_title or "")).lower()
    clay_keywords = ["french", "roland", "madrid", "rome", "italian", "monte carlo",
                     "barcelona", "hamburg", "estoril", "munich", "buenos_aires",
                     "rio", "houston", "geneva", "lyon", "bastad", "kitzbuhel"]
    grass_keywords = ["wimbledon", "queens", "halle", "stuttgart", "eastbourne",
                      "newport", "hertogenbosch", "majorca"]
    for c in clay_keywords:
        if c.replace("_", " ") in text or c.replace(" ", "_") in text or c in text:
            return "Clay"
    for g in grass_keywords:
        if g in text: return "Grass"
    return "Hard"

@st.cache_data(ttl=600)
def discover_active_tennis_keys():
    """Returns list of (sport_key, tour, surface, sport_title) for active tennis events."""
    api_key = get_secret("ODDS_API_KEY")
    if not api_key: return []
    try:
        resp = requests.get("https://api.the-odds-api.com/v4/sports/",
                            params={"apiKey": api_key}, timeout=10)
        if resp.status_code != 200: return []
        sports = resp.json()
        result = []
        for s in sports:
            key = s.get("key", "")
            if not key.startswith(TENNIS_PREFIXES): continue
            if not s.get("active", False): continue
            tour = _classify_tour(key)
            if not tour: continue
            title = s.get("title", "")
            surface = _infer_surface_from_key(key, title)
            result.append({"key": key, "tour": tour, "surface": surface, "title": title})
        return result
    except Exception:
        return []

@st.cache_data(ttl=300)
def fetch_oddsapi_tennis():
    """Pull tennis odds across all currently active tournaments.
    Returns dict keyed by (tour, p1_lower, p2_lower)."""
    api_key = get_secret("ODDS_API_KEY")
    if not api_key: return {}, []
    active = discover_active_tennis_keys()
    if not active: return {}, []

    result = {}
    for entry in active:
        sport_key = entry["key"]
        tour = entry["tour"]
        surface = entry["surface"]
        tournament = entry["title"]
        try:
            resp = requests.get(
                f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/",
                params={"apiKey": api_key, "regions": "us",
                        "markets": "h2h", "oddsFormat": "decimal",
                        "dateFormat": "iso"}, timeout=10)
            if resp.status_code != 200: continue
            for game in resp.json():
                p1 = normalize_name(game.get("home_team", ""))
                p2 = normalize_name(game.get("away_team", ""))
                if not p1 or not p2: continue
                p1_prices, p2_prices = [], []
                for bm in game.get("bookmakers", []):
                    for mkt in bm.get("markets", []):
                        if mkt.get("key") != "h2h": continue
                        for oc in mkt.get("outcomes", []):
                            on = normalize_name(oc.get("name", ""))
                            if on == p1:
                                p1_prices.append(oc["price"])
                            elif on == p2:
                                p2_prices.append(oc["price"])
                if p1_prices and p2_prices:
                    p1_dec = sorted(p1_prices)[len(p1_prices)//2]
                    p2_dec = sorted(p2_prices)[len(p2_prices)//2]
                    result[(tour, p1, p2)] = {
                        "p1_implied": round(1 / p1_dec, 4),
                        "p2_implied": round(1 / p2_dec, 4),
                        "p1_decimal": p1_dec,
                        "p2_decimal": p2_dec,
                        "commence_time": game.get("commence_time", ""),
                        "tournament": tournament,
                        "surface": surface,
                    }
        except Exception:
            continue
    return result, active

# ─── MATCH SCHEDULE FROM API-ODDS ──────────────────────────────────────────
def _parse_et(iso_str):
    if not iso_str: return ""
    try:
        dt = datetime.strptime(iso_str.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
        et = dt - timedelta(hours=4)
        return et.strftime("%-I:%M %p")
    except Exception:
        return ""

def fetch_todays_matches(odds_data):
    """Build today's match list from already-fetched odds data.
    Includes matches commencing today OR within the next 36 hours
    (tennis has matches at 5am ET in Europe that are 'today' over there)."""
    matches = []
    now = datetime.utcnow()
    cutoff = now + timedelta(hours=36)
    for (tour, p1, p2), data in odds_data.items():
        commence = data.get("commence_time", "")
        try:
            if commence:
                ct = datetime.strptime(commence.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
                if ct < now - timedelta(hours=1) or ct > cutoff:
                    continue
        except Exception:
            pass
        matches.append({
            "tour": tour, "p1": p1, "p2": p2,
            "p1_implied": data["p1_implied"],
            "p2_implied": data["p2_implied"],
            "p1_decimal": data["p1_decimal"],
            "p2_decimal": data["p2_decimal"],
            "commence_time": commence,
            "match_time_et": _parse_et(commence),
            "tournament": data.get("tournament", ""),
            "surface": data.get("surface", "Hard"),
        })
    return sorted(matches, key=lambda m: m.get("commence_time", ""))

# ─── KALSHI MATCHING (fuzzy on last name) ──────────────────────────────────
def match_kalshi(tour, p1, p2, kalshi_lines):
    """Find Kalshi line for a player pair in either order."""
    p1_last = last_name(p1)
    p2_last = last_name(p2)
    for (t, k1, k2), data in kalshi_lines.items():
        if t != tour: continue
        k1_last = last_name(k1)
        k2_last = last_name(k2)
        if (names_match(p1, k1) and names_match(p2, k2)):
            return data, False
        if (names_match(p1, k2) and names_match(p2, k1)):
            flipped = dict(data)
            flipped["p1_yes_cents"] = data["p2_yes_cents"]
            flipped["p2_yes_cents"] = data["p1_yes_cents"]
            return flipped, True
        # Last-name fallback for cases like Kalshi using "Sinner" only
        if p1_last == k1_last and p2_last == k2_last and p1_last and p2_last:
            return data, False
        if p1_last == k2_last and p2_last == k1_last and p1_last and p2_last:
            flipped = dict(data)
            flipped["p1_yes_cents"] = data["p2_yes_cents"]
            flipped["p2_yes_cents"] = data["p1_yes_cents"]
            return flipped, True
    return None, False

# ─── BETTING DECISIONS ─────────────────────────────────────────────────────
def calc_signal(model_p1_prob, kalshi_p1_yes_cents):
    if not kalshi_p1_yes_cents or not model_p1_prob:
        return 0.0, 0.0
    implied_p1 = kalshi_p1_yes_cents / 100
    edge_p1 = model_p1_prob - implied_p1
    edge_p2 = (1 - model_p1_prob) - (1 - implied_p1)
    return edge_p1, edge_p2

def betting_decision(edge_pct_abs, conviction_tier):
    in_sweet_spot = (EDGE_MIN * 100) <= edge_pct_abs <= (EDGE_MAX * 100)
    good_conv = conviction_tier in ("HIGH", "MED")
    if in_sweet_spot and good_conv:
        return "✅ BET", "success"
    if not in_sweet_spot and edge_pct_abs > EDGE_MAX * 100:
        return f"❌ SKIP — edge >{int(EDGE_MAX*100)}% (unreliable)", "warning"
    if not in_sweet_spot:
        return "❌ SKIP — no edge", "info"
    if not good_conv:
        return "❌ SKIP — LOW conviction", "warning"
    return "❌ SKIP", "info"

def calc_kelly(edge):
    bet_pct = min((edge / 1.0) * KELLY_FRACTION, MAX_BET_PCT)
    return round(bet_pct * 100, 1), round(BANKROLL * bet_pct, 2)

def fmt_edge(edge):
    if abs(edge) < EDGE_MIN: return "—"
    val = abs(edge) * 100
    sign = "+" if edge > 0 else ""
    capped = min(val, 25.0)
    suffix = "!" if val > EDGE_MAX * 100 else ""
    return f"{sign}{round(capped, 1)}%{suffix}"

# ─── SHADOW VALIDATION ─────────────────────────────────────────────────────
def shadow_log_match(match_date, tour, p1, p2, surface, model_p1_prob,
                     kalshi_p1_cents, oddsapi_p1_implied, conviction_tier,
                     conviction_score, edge_p1, edge_p2):
    if not supabase_connected: return False
    try:
        existing = (supabase.table("tennis_shadow_validation").select("id, winner_name")
                    .eq("match_date", match_date).eq("tour", tour)
                    .eq("player1", p1).eq("player2", p2).execute().data or [])
        if existing:
            row = existing[0]
            if row.get("winner_name"):
                return True
            supabase.table("tennis_shadow_validation").update({
                "model_p1_prob": round(model_p1_prob, 4),
                "kalshi_p1_cents": kalshi_p1_cents,
                "oddsapi_p1_implied": oddsapi_p1_implied,
                "conviction_tier": conviction_tier,
                "conviction_score": conviction_score,
                "edge_p1": round(edge_p1, 4) if edge_p1 else None,
                "edge_p2": round(edge_p2, 4) if edge_p2 else None,
            }).eq("id", row["id"]).execute()
            return True
        supabase.table("tennis_shadow_validation").insert({
            "match_date": match_date, "tour": tour,
            "player1": p1, "player2": p2, "surface": surface,
            "model_p1_prob": round(model_p1_prob, 4),
            "kalshi_p1_cents": kalshi_p1_cents,
            "oddsapi_p1_implied": oddsapi_p1_implied,
            "conviction_tier": conviction_tier,
            "conviction_score": conviction_score,
            "edge_p1": round(edge_p1, 4) if edge_p1 else None,
            "edge_p2": round(edge_p2, 4) if edge_p2 else None,
        }).execute()
        return True
    except Exception:
        return False

def save_bet(match_date, tour, p1, p2, surface, model_prob, kalshi_cents,
             edge, side, bet_amt, conviction_tier, conviction_score,
             placed_on_kalshi=False, real_amount=None):
    if not supabase_connected: return False
    try:
        supabase.table("tennis_settlements").insert({
            "match_date": match_date, "tour": tour,
            "player1": p1, "player2": p2, "surface": surface,
            "model_prob": round(model_prob, 4),
            "kalshi_cents": kalshi_cents,
            "edge": round(edge, 4),
            "bet_side": side, "bet_amount": bet_amt,
            "conviction_tier": conviction_tier,
            "conviction_score": conviction_score,
            "placed_on_kalshi": placed_on_kalshi,
            "real_amount": real_amount if placed_on_kalshi else None,
        }).execute()
        return True
    except Exception as e:
        st.error(f"Save error: {e}")
        return False

# ─── INIT ────────────────────────────────────────────────────────────────
overall_elos, surface_elos = load_player_elos()
kalshi_lines = fetch_kalshi_tennis_lines()
oddsapi_data, active_tournaments = fetch_oddsapi_tennis()
_kalshi_error = kalshi_lines.pop("**error**", None) if isinstance(kalshi_lines, dict) else None
todays_matches = fetch_todays_matches(oddsapi_data)

# ─── SIDEBAR ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-header">System Status</div>', unsafe_allow_html=True)
    st.markdown(f"**Supabase:** {'✅ Connected' if supabase_connected else '❌ Not connected'}")
    _odds_key = get_secret("ODDS_API_KEY")
    st.markdown(f"**Odds API:** {'✅ Loaded' if _odds_key else '❌ Missing'}")
    if _odds_key: st.caption(f"Prefix: {_odds_key[:6]}...")
    st.markdown(f"**Kalshi tennis:** {'✅' if kalshi_lines else '⚠️'} {len(kalshi_lines)} lines")
    st.markdown(f"**Player Elos:** {len(overall_elos)} players")
    st.markdown(f"**Active tournaments:** {len(active_tournaments)}")
    if active_tournaments:
        for t in active_tournaments:
            st.caption(f"• {t['title']} ({t['surface']})")
    st.markdown("---")
    st.markdown("### V1.1 Betting Rules")
    st.markdown(f"✅ BET: edge **{int(EDGE_MIN*100)}–{int(EDGE_MAX*100)}%** + 🔵/🟡 conviction")
    st.markdown(f"❌ SKIP: edge **>{int(EDGE_MAX*100)}%** (unreliable)")
    st.markdown("❌ SKIP: ⚪ LOW conviction")
    st.markdown("---")
    st.caption("Surface Elo blend: 70% surface, 30% overall")
    st.caption("Conviction: 4-signal ensemble")
    st.markdown("---")
    if st.button("🔄 Refresh data"):
        st.cache_data.clear()
        st.rerun()

# ─── TABS ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["Today's Matches", "Settlement Tracker", "Calibration", "Shadow Validation"])

with tab1:
    if not active_tournaments:
        st.warning("No active tennis tournaments found in API-Odds. "
                   "Tennis sport keys are tournament-specific and only active during events.")
    elif not todays_matches:
        st.info(f"Found {len(active_tournaments)} active tournaments but no matches "
                f"in the next 36 hours. Could be a rest day between rounds.")

    if todays_matches:
        st.markdown("<div class='section-header'>Today's Slate</div>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.success(f"Odds API: {len(todays_matches)} matches")
        with c2:
            if kalshi_lines: st.success(f"Kalshi: {len(kalshi_lines)} lines")
            else: st.warning(_kalshi_error or "Kalshi: no lines")
        with c3:
            st.info(f"Elo: {len(overall_elos)} players")
            if len(overall_elos) == 0:
                st.caption("⚠️ No Elo data — predictions will be 50/50 until backfilled")

        # Compute predictions ONCE per match, store in dict for both table + expanders
        match_state = {}
        rows = []
        shadow_logged = 0
        today = today_et()

        for m in todays_matches:
            try:
                tour = m["tour"]
                p1 = m["p1"]
                p2 = m["p2"]
                p1_disp = display_name(p1)
                p2_disp = display_name(p2)

                kalshi_data, _ = match_kalshi(tour, p1, p2, kalshi_lines)
                surface = (kalshi_data["surface"] if kalshi_data else m.get("surface", "Hard"))

                model_p1_prob, detail = predict_match(tour, p1_disp, p2_disp, surface,
                                                      overall_elos, surface_elos)
                conviction = calc_conviction(detail)

                kalshi_p1_cents = kalshi_data["p1_yes_cents"] if kalshi_data else None
                oddsapi_p1_implied = m["p1_implied"]

                if kalshi_p1_cents:
                    edge_p1, edge_p2 = calc_signal(model_p1_prob, kalshi_p1_cents)
                else:
                    edge_p1 = edge_p2 = 0

                match_state[(tour, p1, p2)] = {
                    "model_p1_prob": model_p1_prob,
                    "detail": detail,
                    "conviction": conviction,
                    "kalshi_data": kalshi_data,
                    "kalshi_p1_cents": kalshi_p1_cents,
                    "edge_p1": edge_p1,
                    "edge_p2": edge_p2,
                    "surface": surface,
                    "p1_disp": p1_disp,
                    "p2_disp": p2_disp,
                }

                if shadow_log_match(today, tour, p1_disp, p2_disp, surface,
                                    model_p1_prob, kalshi_p1_cents, oddsapi_p1_implied,
                                    conviction["tier"], conviction["score"],
                                    edge_p1, edge_p2):
                    shadow_logged += 1

                best_edge = max(edge_p1, edge_p2)
                best_side = p1_disp if edge_p1 > edge_p2 else p2_disp
                show_edge = fmt_edge(best_edge) if best_edge >= EDGE_MIN else "—"
                if best_edge < EDGE_MIN:
                    sig = "—"
                elif best_edge > EDGE_MAX:
                    sig = "⚠️ SKIP"
                else:
                    sig = "⚡ EDGE"

                rows.append({
                    "Time": m.get("match_time_et", ""),
                    "Tour": tour,
                    "Match": f"{p1_disp} vs {p2_disp}",
                    "Surf": surface[:1],
                    "Model": f"{model_p1_prob*100:.0f}%/{(1-model_p1_prob)*100:.0f}%",
                    "Kalshi": f"{kalshi_p1_cents}c" if kalshi_p1_cents else "—",
                    "Mkt": f"{int(oddsapi_p1_implied*100)}%",
                    "Best": best_side if best_edge >= EDGE_MIN else "—",
                    "Edge": show_edge,
                    "Conv": conviction["icon"],
                    "Sig": sig,
                })
            except Exception as e:
                st.warning(f"Could not process {m.get('p1','?')} vs {m.get('p2','?')}: {e}")
                continue

        if shadow_logged > 0:
            st.success(f"Shadow: {shadow_logged} rows logged")

        if rows:
            df_all = pd.DataFrame(rows)
            view = st.radio("View", ["Mobile", "Desktop"], horizontal=True, label_visibility="collapsed")
            if view == "Mobile":
                cols = ["Time", "Match", "Surf", "Model", "Kalshi", "Edge", "Conv", "Sig"]
            else:
                cols = ["Time", "Tour", "Match", "Surf", "Model", "Kalshi", "Mkt", "Best", "Edge", "Conv", "Sig"]
            st.dataframe(df_all[cols].style.set_properties(**{'text-align': 'center'}),
                         use_container_width=True, hide_index=True)
            st.markdown("---")

        # Per-match expanders — REUSE match_state (no recomputation)
        for m in todays_matches:
            try:
                key = (m["tour"], m["p1"], m["p2"])
                state = match_state.get(key)
                if not state: continue

                tour = m["tour"]
                p1_disp = state["p1_disp"]
                p2_disp = state["p2_disp"]
                surface = state["surface"]
                model_p1_prob = state["model_p1_prob"]
                detail = state["detail"]
                conviction = state["conviction"]
                kalshi_data = state["kalshi_data"]

                with st.expander(f"**{tour}** {p1_disp} vs {p2_disp} — "
                                 f"{m.get('match_time_et','')} ET ({surface}) — "
                                 f"{m.get('tournament','')}"):
                    cA, cB, cC = st.columns(3)
                    with cA:
                        st.metric(p1_disp, f"{model_p1_prob*100:.0f}%")
                        st.caption(f"Surface Elo: {detail['p1_elo_surface']:.0f}")
                        st.caption(f"Overall Elo: {detail['p1_elo_overall']:.0f}")
                    with cB:
                        st.metric(p2_disp, f"{(1-model_p1_prob)*100:.0f}%")
                        st.caption(f"Surface Elo: {detail['p2_elo_surface']:.0f}")
                        st.caption(f"Overall Elo: {detail['p2_elo_overall']:.0f}")
                    with cC:
                        st.metric("Conviction", conviction["label"], f"{conviction['score']}/8")

                    if not detail.get("elo_data_present"):
                        st.warning("⚠️ One or both players have no Elo history yet — "
                                   "prediction defaulted to 50/50. Backfill Sackmann data to fix.")

                    st.caption(f"Elo blend diff: {detail['elo_diff']:+.1f} | "
                               f"Form adj: {detail['form_adj']:+.1f} | "
                               f"H2H adj: {detail['h2h_adj']:+.1f}")

                    with st.expander("Conviction breakdown"):
                        for sig in conviction["signals"]:
                            st.caption(f"**{sig['name']}** ({sig['points']}/2): {sig['detail']}")

                    st.markdown("---")
                    st.markdown("**Market comparison**")
                    cM1, cM2, cM3 = st.columns(3)
                    with cM1:
                        st.metric("Model", f"{model_p1_prob*100:.1f}% / {(1-model_p1_prob)*100:.1f}%")
                    with cM2:
                        st.metric("API-Odds", f"{m['p1_implied']*100:.1f}% / {m['p2_implied']*100:.1f}%")
                    with cM3:
                        if kalshi_data:
                            st.metric("Kalshi", f"{kalshi_data['p1_yes_cents']}c / {kalshi_data['p2_yes_cents']}c")
                        else:
                            st.metric("Kalshi", "—")

                    if kalshi_data:
                        edge_p1 = state["edge_p1"]
                        edge_p2 = state["edge_p2"]
                        for player_name, side_label, edge_val, yes_cents in [
                            (p1_disp, "P1", edge_p1, kalshi_data["p1_yes_cents"]),
                            (p2_disp, "P2", edge_p2, kalshi_data["p2_yes_cents"]),
                        ]:
                            e_pct = round(edge_val * 100, 1)
                            decision, severity = betting_decision(abs(e_pct), conviction["tier"])
                            label = f"**{player_name}** | YES @ {yes_cents}c | Edge: {e_pct:+.1f}% | {decision}"
                            if decision.startswith("✅"):
                                _, bet_amt = calc_kelly(edge_val)
                                st.success(f"{label} | Kelly: ${bet_amt}")
                                placed = st.checkbox(f"Placed on Kalshi", key=f"placed_{tour}_{m['p1']}_{m['p2']}_{side_label}")
                                real_amt = None
                                if placed:
                                    real_amt = st.number_input(f"Real $ amount", min_value=1.0, max_value=500.0,
                                        value=float(bet_amt), step=1.0,
                                        key=f"real_{tour}_{m['p1']}_{m['p2']}_{side_label}")
                                if st.button(f"Log {player_name}", key=f"log_{tour}_{m['p1']}_{m['p2']}_{side_label}"):
                                    if save_bet(today, tour, p1_disp, p2_disp, surface,
                                                model_p1_prob if side_label == "P1" else (1 - model_p1_prob),
                                                yes_cents, edge_val, side_label, bet_amt,
                                                conviction["tier"], conviction["score"],
                                                placed, real_amt):
                                        st.success("Logged!")
                            elif severity == "warning":
                                st.warning(label)
                            elif severity == "success":
                                st.success(label)
                            else:
                                st.info(label)
                    else:
                        st.caption("No Kalshi line — shadow only")
            except Exception as ge:
                st.warning(f"Could not load match: {ge}")
                continue

with tab2:
    st.markdown("**Settlement Tracker**")
    if supabase_connected:
        try:
            data = (supabase.table("tennis_settlements")
                    .select("*").order("match_date", desc=True).execute().data or [])
            if data:
                df_s = pd.DataFrame(data)
                view = st.radio("View", ["All Logged Bets", "Real Kalshi Bets Only"],
                                horizontal=True, key="settle_view")
                if view == "Real Kalshi Bets Only" and "placed_on_kalshi" in df_s.columns:
                    df_s = df_s[df_s["placed_on_kalshi"] == True]

                settled = df_s[df_s["result"].notna()] if "result" in df_s.columns else pd.DataFrame()
                if not settled.empty:
                    wins = (settled["result"] == "WIN").sum()
                    losses = (settled["result"] == "LOSS").sum()
                    wp = round(wins / (wins + losses) * 100, 1) if (wins + losses) > 0 else 0
                    pnl = round(settled.get("profit_loss", pd.Series([0])).sum(), 2)
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Settled Bets", len(settled))
                    m2.metric("Record", f"{wins}W-{losses}L")
                    m3.metric("Win %", f"{wp}%")
                    m4.metric("P&L", f"${pnl:+.2f}")
                    st.markdown("---")

                cols = [c for c in ["match_date", "tour", "player1", "player2", "surface",
                                     "model_prob", "kalshi_cents", "bet_side", "edge",
                                     "bet_amount", "conviction_tier", "result", "profit_loss"]
                        if c in df_s.columns]
                st.dataframe(df_s[cols], use_container_width=True, hide_index=True)
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
            data = (supabase.table("tennis_shadow_validation").select("*").execute().data or [])
            if not data:
                st.info("No shadow data yet.")
            else:
                df_c = pd.DataFrame(data)
                settled = df_c[df_c["winner_name"].notna()] if "winner_name" in df_c.columns else pd.DataFrame()
                if len(settled) < 10:
                    st.info(f"Need 10+ settled matches for calibration (have {len(settled)}).")
                else:
                    st.markdown(f"**{len(settled)} settled matches**")
                    settled = settled.copy()
                    settled["p1_won"] = (settled["winner_name"] == settled["player1"]).astype(int)
                    bins = [(0.50, 0.55), (0.55, 0.60), (0.60, 0.65), (0.65, 0.70),
                            (0.70, 0.75), (0.75, 0.80), (0.80, 0.90), (0.90, 1.01)]
                    cal_rows = []
                    for lo, hi in bins:
                        sub = settled[(settled["model_p1_prob"] >= lo) & (settled["model_p1_prob"] < hi)]
                        if len(sub) >= 3:
                            cal_rows.append({
                                "Confidence": f"{int(lo*100)}-{int(hi*100)}%",
                                "N": len(sub),
                                "Predicted": f"{((lo+hi)/2)*100:.0f}%",
                                "Actual": f"{sub['p1_won'].mean()*100:.1f}%",
                            })
                    if cal_rows:
                        st.markdown("**Calibration table**")
                        st.dataframe(pd.DataFrame(cal_rows), use_container_width=True, hide_index=True)

                    if "conviction_tier" in settled.columns:
                        st.markdown("---")
                        st.markdown("**By conviction tier**")
                        tier_rows = []
                        for tier in ["HIGH", "MED", "LOW"]:
                            sub = settled[settled["conviction_tier"] == tier]
                            if len(sub) > 0:
                                sub = sub.copy()
                                sub["model_correct"] = ((sub["model_p1_prob"] >= 0.5) == (sub["p1_won"] == 1)).astype(int)
                                tier_rows.append({
                                    "Tier": tier, "N": len(sub),
                                    "Pick Accuracy": f"{sub['model_correct'].mean()*100:.1f}%",
                                })
                        if tier_rows:
                            st.dataframe(pd.DataFrame(tier_rows), use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Calibration error: {e}")
    else:
        st.warning("Supabase not connected.")

with tab4:
    st.markdown("**Shadow Validation — All Matches Auto-Logged**")
    st.caption("Every match auto-logs with conviction tier. Once matches settle, "
               "the winner gets recorded and we compare model probability to actual outcome.")
    st.markdown("---")

    if supabase_connected:
        try:
            data = (supabase.table("tennis_shadow_validation").select("*")
                    .order("match_date", desc=True).execute().data or [])
            if not data:
                st.info("No shadow rows yet. Open Today's Matches to auto-log.")
            else:
                df_sv = pd.DataFrame(data)
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Logged", len(df_sv))
                settled_sv = df_sv[df_sv["winner_name"].notna()] if "winner_name" in df_sv.columns else pd.DataFrame()
                m2.metric("Settled", len(settled_sv))
                if "conviction_tier" in df_sv.columns:
                    high_ct = len(df_sv[df_sv["conviction_tier"] == "HIGH"])
                    med_ct = len(df_sv[df_sv["conviction_tier"] == "MED"])
                    m3.metric("HIGH/MED", f"{high_ct}/{med_ct}")
                    m4.metric("LOW", len(df_sv[df_sv["conviction_tier"] == "LOW"]))

                st.markdown("---")
                st.markdown("**SQL Queries for Validation**")
                st.code("""-- Pick accuracy by conviction tier
SELECT
  conviction_tier,
  COUNT(*) AS matches,
  SUM(CASE WHEN
    (model_p1_prob >= 0.5 AND winner_name = player1) OR
    (model_p1_prob < 0.5 AND winner_name = player2)
  THEN 1 ELSE 0 END) AS correct,
  ROUND(100.0 * SUM(CASE WHEN
    (model_p1_prob >= 0.5 AND winner_name = player1) OR
    (model_p1_prob < 0.5 AND winner_name = player2)
  THEN 1 ELSE 0 END) / COUNT(*), 1) AS accuracy_pct
FROM tennis_shadow_validation
WHERE winner_name IS NOT NULL
GROUP BY conviction_tier
ORDER BY conviction_tier;""", language="sql")

                st.markdown("**Recent Shadow Rows**")
                cols = [c for c in ["match_date", "tour", "player1", "player2", "surface",
                                     "model_p1_prob", "kalshi_p1_cents", "conviction_tier",
                                     "conviction_score", "edge_p1", "edge_p2", "winner_name"]
                        if c in df_sv.columns]
                st.dataframe(df_sv[cols].head(40), use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Shadow validation error: {e}")
    else:
        st.warning("Supabase not connected.")
