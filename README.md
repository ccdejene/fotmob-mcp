# FotMob MCP

FotMob MCP is a standalone Model Context Protocol server for working with live FotMob football data.

It is meant for:

- fixture lookup
- team and player research
- match details and lineups
- league discovery
- search-based entity lookup

The server wraps verified FotMob JSON routes and exposes them through a small, predictable MCP surface.

It provides:

- a route catalog
- a reusable prompt template
- a small set of tools for listing routes, fetching routes, search suggestions, live fixtures, and top-stats lookups

## Install

From a source checkout:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

This installs both the runtime dependencies and the local `fotmob-mcp` package. Installing the package matters because MCP clients can start the server from any working directory.

## Run

```bash
fotmob-mcp
```

## Register in Codex

```bash
codex mcp add fotmob -- /absolute/path/to/fotmob-mcp/.venv/bin/fotmob-mcp
```

If you do not install the package, you must register it with `PYTHONPATH` pointed at the checkout:

```bash
codex mcp add fotmob --env PYTHONPATH=/absolute/path/to/fotmob-mcp -- /absolute/path/to/fotmob-mcp/.venv/bin/python -m fotmob_mcp.server
```

## Configuration

Optional environment variables:

- `FOTMOB_X_MAS`: set this only if you want to send the FotMob request header used by some browser sessions
- `FOTMOB_BASE_URL`: override the default FotMob base URL
- `FOTMOB_CACHE_DIR`: change the local cache directory
- `FOTMOB_CACHE_TTL_SECONDS`: change the cache lifetime

## Optional x-mas header

Most verified routes work without this header. If you want to send it anyway, set `FOTMOB_X_MAS` before starting the server.

To obtain a fresh value, open FotMob in your browser, trigger a request to one of the JSON endpoints, and inspect the request headers in DevTools Network. Copy the `x-mas` header value from that request into `FOTMOB_X_MAS`.

## Resources

- `fotmob://reference`
- `fotmob://routes`
- `fotmob://prompt`

## Tools

- `list_fotmob_routes`
- `fetch_fotmob_route`
- `search_fotmob`
- `get_live_fixtures`
- `get_league_top_stats`

## What this MCP does

Use this server when you need live FotMob data for football research, fixture lookup, team pages, player pages, or match details.

The server exposes:

- a route inventory for the verified FotMob endpoints
- a reusable prompt describing the supported routes
- MCP tools for listing routes, fetching a route, and searching FotMob suggestions

The client caches responses locally and only sends the header when you configure it.

## Supported Endpoints

The server currently exposes these verified FotMob routes:

- `/api/data/search/suggest`
- `/api/data/allLeagues`
- `/api/data/matches`
- `/api/data/leagues`
- `/api/data/leagueseasondeepstats`
- `/api/data/teams`
- `/api/data/playerData`
- `/api/data/playerMatches`
- `/api/data/matchDetails`
- `/api/data/heatmap/match/{matchId}/heatmaps`
- `/api/data/transfers`
- `/api/data/tvlistings`
- `/api/data/audio-matches`
- `/api/data/dataproviders`

Use `list_fotmob_routes` to inspect the exact parameters and notes for each route.
