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
    <div class="mph-badge">V1.0</div>
    <div class="mph-sub" style="margin-top:4px">{now_et().strftime('%b %d, %Y &middot; %-I:%M %p ET')}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Constants ──
BANKROLL = 500
EDGE_MIN = 0.05      # Tennis edges run smaller than MLB totals — 5-12% sweet spot
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

# ─── ELO STATE (loaded from Supabase, cached per session) ──────────────────
@st.cache_data(ttl=300)
def load_player_elos():
    """Load all player Elo ratings from Supabase. Returns dicts keyed by player name."""
    if not supabase_connected:
        return {}, {"Hard": {}, "Clay": {}, "Grass": {}}
    try:
        rows = supabase.table("tennis_player_elos").select("*").execute().data or []
        overall = {}
        surface = {"Hard": {}, "Clay": {}, "Grass": {}}
        for r in rows:
            name = r.get("player_name")
            tour = r.get("tour", "ATP")
            key = f"{tour}|{name}"
            overall[key] = float(r.get("elo_overall", INITIAL_ELO))
            surface["Hard"][key] = float(r.get("elo_hard", INITIAL_ELO))
            surface["Clay"][key] = float(r.get("elo_clay", INITIAL_ELO))
            surface["Grass"][key] = float(r.get("elo_grass", INITIAL_ELO))
        return overall, surface
    except Exception:
        return {}, {"Hard": {}, "Clay": {}, "Grass": {}}

@st.cache_data(ttl=300)
def load_recent_form(player_key, n=RECENT_FORM_WINDOW):
    """Load player's last N match results. Returns list of 1/0."""
    if not supabase_connected: return []
    try:
        tour, name = player_key.split("|", 1)
        rows = (supabase.table("tennis_match_results")
                .select("winner_name, loser_name, match_date")
                .or_(f"winner_name.eq.{name},loser_name.eq.{name}")
                .eq("tour", tour)
                .order("match_date", desc=True)
                .limit(n).execute().data or [])
        results = []
        for r in rows:
            results.append(1 if r.get("winner_name") == name else 0)
        return results
    except Exception:
        return []

@st.cache_data(ttl=300)
def load_h2h(p1_key, p2_key):
    """Get head-to-head record between two players."""
    if not supabase_connected: return (0, 0)
    try:
        tour1, n1 = p1_key.split("|", 1)
        _, n2 = p2_key.split("|", 1)
        rows1 = (supabase.table("tennis_match_results")
                 .select("winner_name")
                 .eq("tour", tour1)
                 .or_(f"and(winner_name.eq.{n1},loser_name.eq.{n2}),and(winner_name.eq.{n2},loser_name.eq.{n1})")
                 .execute().data or [])
        p1_wins = sum(1 for r in rows1 if r.get("winner_name") == n1)
        p2_wins = sum(1 for r in rows1 if r.get("winner_name") == n2)
        return (p1_wins, p2_wins)
    except Exception:
        return (0, 0)

# ─── PREDICTION ENGINE ────────────────────────────────────────────────────
def get_blended_elo(player_key, surface, overall_elos, surface_elos):
    overall = overall_elos.get(player_key, INITIAL_ELO)
    surf = surface_elos.get(surface, {}).get(player_key, INITIAL_ELO)
    return SURFACE_WEIGHT * surf + (1 - SURFACE_WEIGHT) * overall

def predict_match(p1_key, p2_key, surface, overall_elos, surface_elos):
    """Return P(p1 beats p2) and detail dict."""
    e1 = get_blended_elo(p1_key, surface, overall_elos, surface_elos)
    e2 = get_blended_elo(p2_key, surface, overall_elos, surface_elos)

    form1 = load_recent_form(p1_key)
    form2 = load_recent_form(p2_key)
    f1_pct = sum(form1) / len(form1) if form1 else 0.5
    f2_pct = sum(form2) / len(form2) if form2 else 0.5
    form_adj = (f1_pct - f2_pct) * 30

    h2h_p1, h2h_p2 = load_h2h(p1_key, p2_key)
    h2h_total = h2h_p1 + h2h_p2
    if h2h_total >= 3:
        h2h_adj = (h2h_p1 - h2h_p2) * 8
    else:
        h2h_adj = 0

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
    }

# ─── CONVICTION ────────────────────────────────────────────────────────────
def score_elo_gap(detail):
    """Bigger Elo gaps are more confident predictions."""
    diff = abs(detail.get("elo_diff", 0))
    if diff >= 150: return 2, f"Elo gap: {diff:.0f} (decisive)"
    if diff >= 75: return 1, f"Elo gap: {diff:.0f} (moderate)"
    return 0, f"Elo gap: {diff:.0f} (small)"

def score_surface_specialization(detail):
    """Reward when surface-specific Elo confirms the favorite."""
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
    """Reward when recent form aligns with Elo favorite."""
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
    """Reward when H2H sample is meaningful and aligns."""
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
            p1 = (row.get("player1") or "").lower()
            p2 = (row.get("player2") or "").lower()
            if not p1 or not p2: continue
            result[(tour, p1, p2)] = {
                "p1_yes_cents": int(row.get("p1_yes_cents", 50)),
                "p2_yes_cents": int(row.get("p2_yes_cents", 50)),
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

# ─── ODDS API (tennis) ─────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_oddsapi_tennis():
    """Pull tennis odds from API-Odds. Returns dict keyed by (tour, p1_lower, p2_lower)."""
    api_key = get_secret("ODDS_API_KEY")
    if not api_key: return {}
    result = {}
    for sport_key, tour in [("tennis_atp", "ATP"), ("tennis_wta", "WTA")]:
        try:
            resp = requests.get(
                f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/",
                params={"apiKey": api_key, "regions": "us",
                        "markets": "h2h", "oddsFormat": "decimal",
                        "dateFormat": "iso"}, timeout=10)
            if resp.status_code != 200: continue
            for game in resp.json():
                p1 = game.get("home_team", "").lower()
                p2 = game.get("away_team", "").lower()
                # Take median price across books
                p1_prices, p2_prices = [], []
                for bm in game.get("bookmakers", []):
                    for mkt in bm.get("markets", []):
                        if mkt.get("key") != "h2h": continue
                        for oc in mkt.get("outcomes", []):
                            if oc["name"].lower() == p1:
                                p1_prices.append(oc["price"])
                            elif oc["name"].lower() == p2:
                                p2_prices.append(oc["price"])
                if p1_prices and p2_prices:
                    p1_dec = sorted(p1_prices)[len(p1_prices)//2]
                    p2_dec = sorted(p2_prices)[len(p2_prices)//2]
                    p1_implied = 1 / p1_dec
                    p2_implied = 1 / p2_dec
                    result[(tour, p1, p2)] = {
                        "p1_implied": round(p1_implied, 4),
                        "p2_implied": round(p2_implied, 4),
                        "p1_decimal": p1_dec,
                        "p2_decimal": p2_dec,
                        "commence_time": game.get("commence_time", ""),
                    }
        except Exception:
            continue
    return result

def match_oddsapi(tour, p1, p2, odds_dict):
    """Find odds for a player pair in either order."""
    p1l, p2l = p1.lower(), p2.lower()
    for (t, k1, k2), data in odds_dict.items():
        if t != tour: continue
        if (k1 in p1l or p1l in k1) and (k2 in p2l or p2l in k2):
            return data, False  # not flipped
        if (k1 in p2l or p2l in k1) and (k2 in p1l or p1l in k2):
            # Players in opposite order — flip
            return {
                "p1_implied": data["p2_implied"],
                "p2_implied": data["p1_implied"],
                "p1_decimal": data["p2_decimal"],
                "p2_decimal": data["p1_decimal"],
                "commence_time": data.get("commence_time", ""),
            }, True
    return None, False

# ─── MATCH SCHEDULE FROM API-ODDS ──────────────────────────────────────────
def fetch_todays_matches():
    """Build today's match list from API-Odds (since it covers every tournament)."""
    odds = fetch_oddsapi_tennis()
    matches = []
    today_str = today_et()
    for (tour, p1, p2), data in odds.items():
        commence = data.get("commence_time", "")
        if commence and commence[:10] != today_str:
            continue
        matches.append({
            "tour": tour, "p1": p1, "p2": p2,
            "p1_implied": data["p1_implied"],
            "p2_implied": data["p2_implied"],
            "p1_decimal": data["p1_decimal"],
            "p2_decimal": data["p2_decimal"],
            "commence_time": commence,
            "match_time_et": _parse_et(commence),
        })
    return sorted(matches, key=lambda m: m.get("commence_time", ""))

def _parse_et(iso_str):
    if not iso_str: return ""
    try:
        dt = datetime.strptime(iso_str.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
        et = dt - timedelta(hours=4)
        return et.strftime("%-I:%M %p")
    except Exception:
        return ""

def kalshi_to_implied(yes_cents):
    """Convert Kalshi YES price to implied probability."""
    return yes_cents / 100

def implied_to_decimal(implied):
    return 1 / implied if implied > 0 else 0

# ─── KALSHI MATCHING ───────────────────────────────────────────────────────
def match_kalshi(tour, p1, p2, kalshi_lines):
    """Find Kalshi line for a player pair in either order."""
    p1l, p2l = p1.lower(), p2.lower()
    for (t, k1, k2), data in kalshi_lines.items():
        if t != tour: continue
        if (k1 in p1l or p1l in k1) and (k2 in p2l or p2l in k2):
            return data, False
        if (k1 in p2l or p2l in k1) and (k2 in p1l or p1l in k2):
            flipped = dict(data)
            flipped["p1_yes_cents"] = data["p2_yes_cents"]
            flipped["p2_yes_cents"] = data["p1_yes_cents"]
            return flipped, True
    return None, False

# ─── BETTING DECISIONS ─────────────────────────────────────────────────────
def calc_signal(model_p1_prob, kalshi_p1_yes_cents):
    """Compare model probability to Kalshi YES price for player 1."""
    if not kalshi_p1_yes_cents or not model_p1_prob:
        return "EVEN", 0.0, "EVEN", 0.0
    implied_p1 = kalshi_p1_yes_cents / 100
    edge_p1 = model_p1_prob - implied_p1
    edge_p2 = (1 - model_p1_prob) - (1 - implied_p1)
    p1_lean = "BUY P1" if edge_p1 > 0 else "EVEN"
    p2_lean = "BUY P2" if edge_p2 > 0 else "EVEN"
    return p1_lean, edge_p1, p2_lean, edge_p2

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

# ─── ELO UPDATE (after match settles) ──────────────────────────────────────
def update_elo_after_match(tour, winner, loser, surface):
    """Update player Elos in Supabase after match settles."""
    if not supabase_connected: return False
    try:
        winner_key = f"{tour}|{winner}"
        loser_key = f"{tour}|{loser}"
        # Fetch current ratings
        w_rows = (supabase.table("tennis_player_elos").select("*")
                  .eq("tour", tour).eq("player_name", winner).execute().data or [])
        l_rows = (supabase.table("tennis_player_elos").select("*")
                  .eq("tour", tour).eq("player_name", loser).execute().data or [])
        w_overall = float(w_rows[0]["elo_overall"]) if w_rows else INITIAL_ELO
        l_overall = float(l_rows[0]["elo_overall"]) if l_rows else INITIAL_ELO
        w_surf_col = f"elo_{surface.lower()}"
        w_surf = float(w_rows[0][w_surf_col]) if w_rows else INITIAL_ELO
        l_surf = float(l_rows[0][w_surf_col]) if l_rows else INITIAL_ELO
        # Overall
        exp_w = 1 / (1 + 10 ** ((l_overall - w_overall) / 400))
        new_w_overall = w_overall + K_FACTOR * (1 - exp_w)
        new_l_overall = l_overall + K_FACTOR * (0 - (1 - exp_w))
        # Surface
        exp_w_s = 1 / (1 + 10 ** ((l_surf - w_surf) / 400))
        new_w_surf = w_surf + K_FACTOR * (1 - exp_w_s)
        new_l_surf = l_surf + K_FACTOR * (0 - (1 - exp_w_s))
        # Build update payload (preserve other surface ratings)
        def upsert_row(name, rows, new_overall, surface_col, new_surf):
            base = {
                "tour": tour, "player_name": name,
                "elo_overall": round(new_overall, 1),
                "elo_hard": float(rows[0]["elo_hard"]) if rows else INITIAL_ELO,
                "elo_clay": float(rows[0]["elo_clay"]) if rows else INITIAL_ELO,
                "elo_grass": float(rows[0]["elo_grass"]) if rows else INITIAL_ELO,
                "updated_at": datetime.utcnow().isoformat(),
            }
            base[surface_col] = round(new_surf, 1)
            supabase.table("tennis_player_elos").upsert(base, on_conflict="tour,player_name").execute()
        upsert_row(winner, w_rows, new_w_overall, w_surf_col, new_w_surf)
        upsert_row(loser, l_rows, new_l_overall, w_surf_col, new_l_surf)
        return True
    except Exception as e:
        st.error(f"Elo update error: {e}")
        return False

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
                return True  # already settled
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
oddsapi_data = fetch_oddsapi_tennis()
_kalshi_error = kalshi_lines.pop("**error**", None) if isinstance(kalshi_lines, dict) else None
todays_matches = fetch_todays_matches()

# ─── SIDEBAR ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-header">System Status</div>', unsafe_allow_html=True)
    st.markdown(f"**Supabase:** {'✅ Connected' if supabase_connected else '❌ Not connected'}")
    _odds_key = get_secret("ODDS_API_KEY")
    st.markdown(f"**Odds API:** {'✅ Loaded' if _odds_key else '❌ Missing'}")
    if _odds_key: st.caption(f"Prefix: {_odds_key[:6]}...")
    st.markdown(f"**Kalshi tennis:** {'✅' if kalshi_lines else '⚠️'} {len(kalshi_lines)} lines")
    st.markdown(f"**Player Elo ratings:** {len(overall_elos)} players")
    st.markdown("---")
    st.markdown("### V1.0 Betting Rules")
    st.markdown(f"✅ BET: edge **{int(EDGE_MIN*100)}–{int(EDGE_MAX*100)}%** + 🔵/🟡 conviction")
    st.markdown(f"❌ SKIP: edge **>{int(EDGE_MAX*100)}%** (unreliable)")
    st.markdown("❌ SKIP: ⚪ LOW conviction")
    st.markdown("---")
    st.caption("Surface Elo blend: 70% surface, 30% overall")
    st.caption("Conviction: 4-signal ensemble (Elo gap, surface, form, H2H)")
    st.markdown("---")
    st.markdown("**Shadow Validation**")
    st.caption("Every match auto-logs. Build calibration over weeks.")
    st.markdown("---")
    if st.button("🔄 Refresh data"):
        st.cache_data.clear()
        st.rerun()

# ─── TABS ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["Today's Matches", "Settlement Tracker", "Calibration", "Shadow Validation"])

with tab1:
    if not todays_matches:
        st.warning("No matches loaded. Check Odds API connection.")
    else:
        st.markdown("<div class='section-header'>Today's Slate</div>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            if oddsapi_data: st.success(f"Odds API: {len(oddsapi_data)} matches")
            else: st.warning("Odds API unavailable")
        with c2:
            if kalshi_lines: st.success(f"Kalshi: {len(kalshi_lines)} lines")
            else: st.warning(_kalshi_error or "Kalshi: no lines")
        with c3:
            st.info(f"Elo ratings: {len(overall_elos)} players")

        rows = []
        shadow_logged = 0
        today = today_et()

        for m in todays_matches:
            try:
                tour = m["tour"]
                p1 = m["p1"]
                p2 = m["p2"]

                kalshi_data, _ = match_kalshi(tour, p1, p2, kalshi_lines)
                surface = (kalshi_data["surface"] if kalshi_data
                           else "Hard")  # default to Hard if Kalshi unknown

                p1_key = f"{tour}|{p1.title()}"
                p2_key = f"{tour}|{p2.title()}"

                model_p1_prob, detail = predict_match(p1_key, p2_key, surface,
                                                      overall_elos, surface_elos)
                conviction = calc_conviction(detail)

                kalshi_p1_cents = kalshi_data["p1_yes_cents"] if kalshi_data else None
                oddsapi_p1_implied = m["p1_implied"]

                # Edges
                if kalshi_p1_cents:
                    p1_lean, edge_p1, p2_lean, edge_p2 = calc_signal(model_p1_prob, kalshi_p1_cents)
                else:
                    edge_p1 = edge_p2 = 0
                    p1_lean = p2_lean = "EVEN"

                # Shadow log
                if shadow_log_match(today, tour, p1.title(), p2.title(), surface,
                                    model_p1_prob, kalshi_p1_cents, oddsapi_p1_implied,
                                    conviction["tier"], conviction["score"],
                                    edge_p1, edge_p2):
                    shadow_logged += 1

                # Pick best edge to surface in table
                best_edge = max(edge_p1, edge_p2)
                best_side = p1.title() if edge_p1 > edge_p2 else p2.title()
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
                    "Match": f"{p1.title()} vs {p2.title()}",
                    "Surf": surface[:1],  # H/C/G
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

        # Per-match expanders
        for m in todays_matches:
            try:
                tour = m["tour"]
                p1 = m["p1"]
                p2 = m["p2"]
                kalshi_data, _ = match_kalshi(tour, p1, p2, kalshi_lines)
                surface = kalshi_data["surface"] if kalshi_data else "Hard"
                p1_key = f"{tour}|{p1.title()}"
                p2_key = f"{tour}|{p2.title()}"

                model_p1_prob, detail = predict_match(p1_key, p2_key, surface,
                                                       overall_elos, surface_elos)
                conviction = calc_conviction(detail)

                with st.expander(f"**{tour}** {p1.title()} vs {p2.title()} — {m.get('match_time_et','')} ET ({surface})"):
                    cA, cB, cC = st.columns(3)
                    with cA:
                        st.metric(f"{p1.title()}", f"{model_p1_prob*100:.0f}%")
                        st.caption(f"Surface Elo: {detail['p1_elo_surface']:.0f}")
                        st.caption(f"Overall Elo: {detail['p1_elo_overall']:.0f}")
                    with cB:
                        st.metric(f"{p2.title()}", f"{(1-model_p1_prob)*100:.0f}%")
                        st.caption(f"Surface Elo: {detail['p2_elo_surface']:.0f}")
                        st.caption(f"Overall Elo: {detail['p2_elo_overall']:.0f}")
                    with cC:
                        st.metric("Conviction", conviction["label"], f"{conviction['score']}/8")

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
                        kalshi_p1_cents = kalshi_data["p1_yes_cents"]
                        p1_lean, edge_p1, p2_lean, edge_p2 = calc_signal(model_p1_prob, kalshi_p1_cents)

                        for player_name, side_label, edge_val, yes_cents in [
                            (p1.title(), "P1", edge_p1, kalshi_p1_cents),
                            (p2.title(), "P2", edge_p2, kalshi_data["p2_yes_cents"]),
                        ]:
                            e_pct = round(edge_val * 100, 1)
                            decision, severity = betting_decision(abs(e_pct), conviction["tier"])
                            label = f"**{player_name}** | YES @ {yes_cents}c | Edge: {e_pct:+.1f}% | {decision}"
                            if decision.startswith("✅"):
                                _, bet_amt = calc_kelly(edge_val)
                                st.success(f"{label} | Kelly: ${bet_amt}")
                                placed = st.checkbox(f"Placed on Kalshi", key=f"placed_{tour}_{p1}_{p2}_{side_label}")
                                real_amt = None
                                if placed:
                                    real_amt = st.number_input(f"Real $ amount", min_value=1.0, max_value=500.0,
                                        value=float(bet_amt), step=1.0,
                                        key=f"real_{tour}_{p1}_{p2}_{side_label}")
                                if st.button(f"Log {player_name}", key=f"log_{tour}_{p1}_{p2}_{side_label}"):
                                    if save_bet(today, tour, p1.title(), p2.title(), surface,
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

                    # Calibration: bucket model_p1_prob, compare to actual win rates
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
                        st.markdown("**Calibration table** (when model says X%, does P1 actually win X%?)")
                        st.dataframe(pd.DataFrame(cal_rows), use_container_width=True, hide_index=True)

                    # By conviction tier
                    if "conviction_tier" in settled.columns:
                        st.markdown("---")
                        st.markdown("**By conviction tier**")
                        tier_rows = []
                        for tier in ["HIGH", "MED", "LOW"]:
                            sub = settled[settled["conviction_tier"] == tier]
                            if len(sub) > 0:
                                # Did model pick the eventual winner?
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
               "the winner gets recorded and we can compare model probability to actual outcome.")
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

                st.code("""-- Edge bucket performance (when we had Kalshi line)
SELECT
  CASE
    WHEN ABS(GREATEST(COALESCE(edge_p1,0), COALESCE(edge_p2,0))) < 0.05 THEN '1. Under 5%'
    WHEN ABS(GREATEST(COALESCE(edge_p1,0), COALESCE(edge_p2,0))) < 0.12 THEN '2. 5-12%'
    ELSE '3. 12%+'
  END AS edge_bucket,
  conviction_tier,
  COUNT(*) AS matches
FROM tennis_shadow_validation
WHERE winner_name IS NOT NULL AND kalshi_p1_cents IS NOT NULL
GROUP BY edge_bucket, conviction_tier
ORDER BY edge_bucket, conviction_tier;""", language="sql")

                st.markdown("---")
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
