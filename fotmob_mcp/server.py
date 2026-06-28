from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from fotmob_mcp.client import FotMobClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = PROJECT_ROOT / "docs" / "fotmob-api.md"


@dataclass(frozen=True)
class FotMobRoute:
    key: str
    path: str
    description: str
    params: tuple[str, ...]
    notes: str = ""


ROUTES: list[FotMobRoute] = [
    FotMobRoute("search_suggest", "/api/data/search/suggest", "Search autocomplete and entity lookup", ("term", "hits", "lang")),
    FotMobRoute("all_leagues", "/api/data/allLeagues", "Global league directory", ("locale", "country")),
    FotMobRoute("matches", "/api/data/matches", "Daily match listings", ("date", "timezone", "ccode3")),
    FotMobRoute("leagues", "/api/data/leagues", "League overview, table, fixtures, stats, playoff data", ("id", "season", "ccode3")),
    FotMobRoute("leagues_shotmap", "/api/data/leagues", "League overview with shotmap data", ("id", "season", "ccode3", "shotmap"), notes="Set shotmap=true"),
    FotMobRoute(
        "league_season_deep_stats",
        "/api/data/leagueseasondeepstats",
        "League season player and team stat tables",
        ("id", "season", "type", "stat", "teamId"),
        notes="Use the internal season id from the leagues route, e.g. World Cup 2026 season=24254",
    ),
    FotMobRoute("teams", "/api/data/teams", "Team overview, fixtures, stats, transfers, history", ("id", "ccode3")),
    FotMobRoute("player_data", "/api/data/playerData", "Player profile, stats, market value data", ("id", "includeMarketValues")),
    FotMobRoute("player_matches", "/api/data/playerMatches", "Paginated player match history", ("playerId", "before", "parentLeagueId")),
    FotMobRoute("match_details", "/api/data/matchDetails", "Match details page", ("matchId",)),
    FotMobRoute(
        "match_heatmaps",
        "/api/data/heatmap/match/{matchId}/heatmaps",
        "Match player heatmap SVG data",
        ("matchId", "heatmapUrl"),
        notes="Use heatmapUrl from matchDetails.content.matchFacts.heatmapUrl",
    ),
    FotMobRoute("transfers", "/api/data/transfers", "Transfer center data", ("teamId", "leagueId", "page", "sortBy", "showLoans")),
    FotMobRoute("tvlistings", "/api/data/tvlistings", "TV listings", ("countryCode", "ids")),
    FotMobRoute("audio_matches", "/api/data/audio-matches", "Audio/commentary listings", ()),
    FotMobRoute("dataproviders", "/api/data/dataproviders", "Betting/provider metadata", ()),
]

ROUTE_BY_KEY = {route.key: route for route in ROUTES}

mcp = FastMCP(
    "fotmob-api-reference",
    instructions="Expose FotMob route docs and a small fetch layer for the verified JSON endpoints.",
)


def get_route_catalog() -> list[dict[str, Any]]:
    return [
        {
            "key": route.key,
            "path": route.path,
            "description": route.description,
            "params": list(route.params),
            "notes": route.notes,
        }
        for route in ROUTES
    ]


def render_route_catalog_markdown() -> str:
    lines = [
        "# FotMob API Routes",
        "",
        "This MCP server exposes the verified FotMob route inventory.",
        "",
        "| Key | Route | Purpose | Params | Notes |",
        "| --- | --- | --- | --- | --- |",
    ]
    for route in ROUTES:
        lines.append(
            f"| `{route.key}` | `{route.path}` | {route.description} | "
            f"{', '.join(f'`{p}`' for p in route.params) if route.params else '-'} | "
            f"{route.notes or '-'} |"
        )
    return "\n".join(lines)


def render_prompt_template() -> str:
    return """You are working with FotMob public JSON routes.

Use the shared FotMob client. The x-mas header is optional and only added when configured.

Available routes:
- /api/data/search/suggest?term={q}&hits={n}&lang={langs}
- /api/data/allLeagues?locale={locale}&country={ccode3}
- /api/data/matches?date={yyyy-mm-dd}&timezone={tz}&ccode3={ccode3}
- /api/data/leagues?id={leagueId}&season={season}&ccode3={ccode3}
- /api/data/leagues?id={leagueId}&season={season}&ccode3={ccode3}&shotmap=true
- /api/data/leagueseasondeepstats?id={leagueId}&season={seasonId}&type={players|teams}&stat={statName}
- /api/data/teams?id={teamId}&ccode3={ccode3}
- /api/data/playerData?id={playerId}&includeMarketValues=true
- /api/data/playerMatches?playerId={playerId}&before={unix}&parentLeagueId={leagueId}
- /api/data/matchDetails?matchId={matchId}
- /api/data/heatmap/match/{matchId}/heatmaps?heatmapUrl={heatmapUrl}
- /api/data/transfers?teamId={teamId}&leagueId={leagueId}
- /api/data/tvlistings?countryCode={ccode3}&ids={ids}
- /api/data/audio-matches
- /api/data/dataproviders

Use search/suggest for autocomplete and lookup.
Use allLeagues for league discovery.
Use matches for date-based match lists.
Use leagues for league pages and playoff data.
Use league_season_deep_stats for league player/team stat tables; pass the internal season id exposed by leagues.seasons.
Use teams for team pages.
Use playerData and playerMatches for player pages.
Use matchDetails for match pages.
Use match_heatmaps with the heatmapUrl value from matchDetails.
Use transfers for transfer center data.

If you need more routes, inspect FotMob's own frontend bundles and confirm the exact path and params before coding.
"""


def _coerce_params(params: dict[str, Any]) -> dict[str, str]:
    return {key: str(value) for key, value in params.items() if value is not None}


def _resolve_route(route_key: str) -> FotMobRoute:
    key = route_key.strip()
    if key not in ROUTE_BY_KEY:
        raise KeyError(f"Unknown FotMob route key: {route_key}")
    return ROUTE_BY_KEY[key]


def fetch_fotmob_route(route_key: str, params: dict[str, Any] | None = None, client: FotMobClient | None = None) -> dict[str, Any]:
    route = _resolve_route(route_key)
    query = _coerce_params(params or {})
    client = client or FotMobClient()
    path = route.path
    if route.key == "match_heatmaps":
        match_id = query.pop("matchId", "")
        if not match_id:
            raise ValueError("match_heatmaps requires matchId")
        path = route.path.format(matchId=match_id)
    if route.key == "leagues_shotmap":
        query.setdefault("shotmap", "true")
    if route.key == "search_suggest":
        query.setdefault("hits", "10")
        query.setdefault("lang", "en")
    payload = client.get_json(path, query)
    return {"route": route.key, "path": path, "params": query, "payload": payload}


def get_league_top_stats(
    league_id: str | int,
    season: str | int,
    stat: str = "goals",
    stat_type: str = "players",
    limit: int = 10,
    team_id: str | int | None = None,
    client: FotMobClient | None = None,
) -> dict[str, Any]:
    client = client or FotMobClient()
    params: dict[str, Any] = {"id": league_id, "season": season, "type": stat_type, "stat": stat}
    if team_id is not None:
        params["teamId"] = team_id

    first = fetch_fotmob_route("league_season_deep_stats", params, client)
    payload = first["payload"]
    rows = payload.get("statsData", []) if isinstance(payload, dict) else []

    resolved_season = str(season)
    if not rows and isinstance(payload, dict):
        for season_info in payload.get("seasons", []):
            if str(season_info.get("name")) == str(season):
                resolved_season = str(season_info["id"])
                params["season"] = resolved_season
                first = fetch_fotmob_route("league_season_deep_stats", params, client)
                payload = first["payload"]
                rows = payload.get("statsData", []) if isinstance(payload, dict) else []
                break

    return {
        "route": "league_top_stats",
        "source_route": first["route"],
        "path": first["path"],
        "params": first["params"],
        "resolvedSeason": resolved_season,
        "statsData": rows[: max(limit, 0)],
    }


def search_suggestions(term: str, hits: int = 10, lang: str = "en") -> dict[str, Any]:
    return fetch_fotmob_route("search_suggest", {"term": term, "hits": hits, "lang": lang})


@mcp.resource("fotmob://reference", name="FotMob API Reference", mime_type="text/markdown")
def fotmob_reference() -> str:
    return REFERENCE_PATH.read_text(encoding="utf-8")


@mcp.resource("fotmob://routes", name="FotMob Route Catalog", mime_type="text/markdown")
def fotmob_routes() -> str:
    return render_route_catalog_markdown()


@mcp.resource("fotmob://prompt", name="FotMob Reusable Prompt", mime_type="text/plain")
def fotmob_prompt() -> str:
    return render_prompt_template()


@mcp.tool(name="list_fotmob_routes", description="List the verified FotMob route inventory, optionally filtered by a keyword.")
def list_fotmob_routes(query: str | None = None) -> dict[str, Any]:
    routes = get_route_catalog()
    if query:
        needle = query.lower().strip()
        routes = [
            route
            for route in routes
            if needle in route["key"].lower()
            or needle in route["path"].lower()
            or needle in route["description"].lower()
            or needle in route["notes"].lower()
        ]
    return {"count": len(routes), "routes": routes}


@mcp.tool(name="fetch_fotmob_route", description="Fetch one of the verified FotMob JSON routes through the shared FotMob client.")
def fetch_route_tool(route_key: str, params_json: str = "{}") -> dict[str, Any]:
    try:
        params = json.loads(params_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"params_json must be valid JSON: {exc}") from exc
    if not isinstance(params, dict):
        raise ValueError("params_json must decode to a JSON object")
    return fetch_fotmob_route(route_key, params)


@mcp.tool(name="search_fotmob", description="Fetch FotMob search suggestions for a term.")
def search_fotmob(term: str, hits: int = 10, lang: str = "en") -> dict[str, Any]:
    return search_suggestions(term=term, hits=hits, lang=lang)


@mcp.tool(name="get_league_top_stats", description="Fetch top league player/team stats and resolve FotMob internal season ids automatically.")
def league_top_stats_tool(
    league_id: str,
    season: str,
    stat: str = "goals",
    stat_type: str = "players",
    limit: int = 10,
    team_id: str | None = None,
) -> dict[str, Any]:
    return get_league_top_stats(league_id, season, stat, stat_type, limit, team_id)


def main() -> None:
    mcp.run("stdio")


if __name__ == "__main__":
    main()
