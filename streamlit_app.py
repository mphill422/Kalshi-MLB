import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const ODDS_API_KEY = Deno.env.get("ODDS_API_KEY")!;

const KALSHI_TEAM_MAP: Record<string, string> = {
  NYY: "Yankees", BOS: "Red Sox", TOR: "Blue Jays", BAL: "Orioles", TBR: "Rays", TAM: "Rays", TB: "Rays",
  CLE: "Guardians", MIN: "Twins", DET: "Tigers", KCR: "Royals", KAN: "Royals", KC: "Royals",
  CWS: "White Sox", CHW: "White Sox", HOU: "Astros", SEA: "Mariners", TEX: "Rangers",
  LAA: "Angels", OAK: "Athletics", ATH: "Athletics", NYM: "Mets", PHI: "Phillies",
  ATL: "Braves", WSH: "Nationals", WAS: "Nationals", MIA: "Marlins", CHC: "Cubs",
  MIL: "Brewers", STL: "Cardinals", PIT: "Pirates", CIN: "Reds", LAD: "Dodgers",
  SDP: "Padres", SAN: "Padres", SD: "Padres", ARI: "Diamondbacks", AZ: "Diamondbacks",
  SFG: "Giants", SF: "Giants", COL: "Rockies",
};

function parseTeamCodes(teamStr: string): [string, string] | null {
  for (let i = 2; i <= teamStr.length - 2; i++) {
    const away = teamStr.slice(0, i);
    const home = teamStr.slice(i);
    if (KALSHI_TEAM_MAP[away] && KALSHI_TEAM_MAP[home]) {
      return [away, home];
    }
  }
  return null;
}

async function fetchMarkets(seriesTicker: string): Promise<any[]> {
  const resp = await fetch(
    `https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=${seriesTicker}&status=open&limit=200`
  );
  const data = await resp.json();
  return data.markets || [];
}

async function fetchVegasLines(): Promise<Map<string, number>> {
  // Returns map of "awayFragment|homeFragment" -> vegas total
  const vegasMap = new Map<string, number>();
  try {
    const resp = await fetch(
      `https://api.the-odds-api.com/v4/sports/baseball_mlb/odds/?apiKey=${ODDS_API_KEY}&regions=us&markets=totals&oddsFormat=american`
    );
    const games = await resp.json();
    for (const game of games) {
      const away = (game.away_team || "").toLowerCase();
      const home = (game.home_team || "").toLowerCase();
      for (const bm of game.bookmakers || []) {
        for (const mkt of bm.markets || []) {
          if (mkt.key !== "totals") continue;
          for (const oc of mkt.outcomes || []) {
            if (oc.name === "Over") {
              vegasMap.set(`${away}|${home}`, parseFloat(oc.point));
            }
          }
        }
        break; // first bookmaker is enough
      }
    }
  } catch (e) {
    console.error("Vegas fetch failed:", e);
  }
  return vegasMap;
}

function findVegasTotal(awayTeam: string, homeTeam: string, vegasMap: Map<string, number>): number | null {
  const awayLow = awayTeam.toLowerCase();
  const homeLow = homeTeam.toLowerCase();
  for (const [key, total] of vegasMap.entries()) {
    const [ka, kh] = key.split("|");
    if ((ka.includes(awayLow) || awayLow.includes(ka)) &&
        (kh.includes(homeLow) || homeLow.includes(kh))) {
      return total;
    }
  }
  return null;
}

function processMarkets(
  markets: any[],
  marketType: string,
  today: string,
  vegasMap: Map<string, number>
) {
  // Group all brackets by game
  const gameMap: Record<string, any[]> = {};

  for (const mkt of markets) {
    const ticker = mkt.ticker || "";
    const parts = ticker.split("-");
    if (parts.length < 3) continue;

    const line = parseFloat(parts[parts.length - 1]);
    if (isNaN(line) || line < 1 || line > 25) continue;

    const segment = parts[parts.length - 2];
    const teamStr = segment.match(/[A-Z]+$/)?.[0] || "";
    if (!teamStr) continue;

    const split = parseTeamCodes(teamStr);
    if (!split) continue;

    const [awayCd, homeCd] = split;
    const awayTeam = KALSHI_TEAM_MAP[awayCd];
    const homeTeam = KALSHI_TEAM_MAP[homeCd];

    const yesBid = parseFloat(mkt.yes_bid_dollars || "0.5");
    const volume = parseFloat(mkt.open_interest_fp || mkt.volume_fp || "0");

    if (!gameMap[teamStr]) gameMap[teamStr] = [];
    gameMap[teamStr].push({
      away_team: awayTeam,
      home_team: homeTeam,
      line,
      over_price_cents: Math.round(yesBid * 100),
      ticker,
      game_date: today,
      market_type: marketType,
      updated_at: new Date().toISOString(),
      volume,
      teamStr,
    });
  }

  const rows = [];
  for (const [teamStr, brackets] of Object.entries(gameMap)) {
    if (!brackets.length) continue;
    const { away_team, home_team } = brackets[0];

    // Find Vegas reference line
    const vegasTotal = findVegasTotal(away_team, home_team, vegasMap);
    let targetLine: number;

    if (vegasTotal) {
      targetLine = marketType === "f5" ? vegasTotal / 2 : vegasTotal;
    } else {
      // No Vegas line — fall back to highest volume bracket
      brackets.sort((a, b) => b.volume - a.volume);
      const { volume, teamStr: _, ...row } = brackets[0];
      rows.push(row);
      continue;
    }

    // Pick bracket closest to target line
    brackets.sort((a, b) => Math.abs(a.line - targetLine) - Math.abs(b.line - targetLine));
    const best = brackets[0];
    const { volume, teamStr: _, ...row } = best;
    rows.push(row);
  }

  return rows;
}

Deno.serve(async () => {
  try {
    const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);
    const today = new Date().toISOString().split("T")[0];

    // Fetch Vegas lines and Kalshi markets in parallel
    const [vegasMap, fullMarkets, f5Markets] = await Promise.all([
      fetchVegasLines(),
      fetchMarkets("KXMLBTOTAL"),
      fetchMarkets("KXMLBF5TOTAL"),
    ]);

    await supabase.from("kalshi_lines").delete().eq("game_date", today);

    const fullRows = processMarkets(fullMarkets, "full", today, vegasMap);
    const f5Rows = processMarkets(f5Markets, "f5", today, vegasMap);
    const allRows = [...fullRows, ...f5Rows];

    if (allRows.length > 0) {
      await supabase.from("kalshi_lines").insert(allRows);
    }

    return new Response(JSON.stringify({
      success: true,
      full_game: fullRows.length,
      f5: f5Rows.length,
      total: allRows.length,
      vegas_lines_found: vegasMap.size,
    }), { headers: { "Content-Type": "application/json" } });

  } catch (e) {
    return new Response(JSON.stringify({ error: String(e) }), {
      status: 500, headers: { "Content-Type": "application/json" },
    });
  }
});
