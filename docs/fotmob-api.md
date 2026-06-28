# FotMob API Reference

FotMob MCP wraps verified FotMob JSON routes in a standalone Model Context Protocol server.

It is designed for tools and agents that need live football data without scraping the entire FotMob site manually. The server focuses on the routes that are useful for:

- discovering leagues and teams
- looking up fixtures and match details
- reading lineups, scorers, and performance data
- retrieving player profiles and match history
- searching FotMob entities by name

All requests should go through the shared FotMob client.

## Endpoint Overview

| Route | Purpose | Main params |
| --- | --- | --- |
| `/api/data/search/suggest` | Search autocomplete and entity lookup | `term`, `hits`, `lang` |
| `/api/data/allLeagues` | Global league directory | `locale`, `country` |
| `/api/data/matches` | Daily match listings | `date`, `timezone`, `ccode3` |
| `/api/data/leagues` | League overview, table, fixtures, stats, playoff data | `id`, `season`, `ccode3` |
| `/api/data/leagueseasondeepstats` | League season player and team stat tables | `id`, `season`, `type`, `stat`, `teamId` |
| `/api/data/teams` | Team overview, fixtures, stats, transfers, history | `id`, `ccode3` |
| `/api/data/playerData` | Player profile, stats, market value data | `id`, `includeMarketValues` |
| `/api/data/playerMatches` | Paginated player match history | `playerId`, `before`, `parentLeagueId` |
| `/api/data/matchDetails` | Match details page | `matchId` |
| `/api/data/tvlistings` | TV listings | `countryCode`, `ids` |
| `/api/data/audio-matches` | Audio/commentary listings | no query parameters observed |
| `/api/data/dataproviders` | Betting/provider metadata | no query parameters observed |

## Route Groups

### Discovery

- `/api/data/search/suggest`
- `/api/data/allLeagues`

### Fixtures and competitions

- `/api/data/matches`
- `/api/data/leagues`
- `/api/data/leagueseasondeepstats`
- `/api/data/tvlistings`

### Teams and players

- `/api/data/teams`
- `/api/data/playerData`
- `/api/data/playerMatches`

### Match detail

- `/api/data/matchDetails`
- `/api/data/audio-matches`
- `/api/data/dataproviders`

## Example Requests

```text
GET https://www.fotmob.com/api/data/search/suggest?hits=50&lang=en%2Cfr%2Cnl&term=neth
GET https://www.fotmob.com/api/data/leagues?id=57&ccode3=NED&season=2026/2027
GET https://www.fotmob.com/api/data/leagueseasondeepstats?id=77&season=24254&type=players&stat=goals
GET https://www.fotmob.com/api/data/teams?id=8593&ccode3=NED
GET https://www.fotmob.com/api/data/playerData?id=12345&includeMarketValues=true
GET https://www.fotmob.com/api/data/playerMatches?playerId=12345&before=1719532800&parentLeagueId=57
GET https://www.fotmob.com/api/data/matchDetails?matchId=4653849
```

## Search Payload Shape

`/api/data/search/suggest` returns mixed suggestions, typically:

- `team`
- `league`
- `player`
- `match`

The search endpoint is useful for quick lookup, but it is not a full indexed search API.

## How to use the MCP

The server exposes three tools:

- `list_fotmob_routes` returns the verified route catalog
- `fetch_fotmob_route` fetches one route by key and parameter object
- `search_fotmob` queries FotMob suggestions for a search term

It also exposes three resources:

- `fotmob://reference`
- `fotmob://routes`
- `fotmob://prompt`

Typical flow:

1. search a team, league, or player by name
2. fetch the relevant team, league, or match route
3. inspect match details for lineups, scorers, and event data
4. cache and reuse the response when the same request is made again

For league stat tables, fetch `/api/data/leagues` first and use the internal season id from its `seasons` list. For example, World Cup 2026 uses `season=24254` for `/api/data/leagueseasondeepstats`, while the overview route can use `season=2026`.

## Configuration

Optional environment variables:

- `FOTMOB_X_MAS`: send the FotMob request header used by some browser sessions
- `FOTMOB_BASE_URL`: override the default FotMob base URL
- `FOTMOB_CACHE_DIR`: change the local cache directory
- `FOTMOB_CACHE_TTL_SECONDS`: change the cache lifetime

If you need to collect a fresh `x-mas` value, open FotMob in a browser, trigger a request to a JSON endpoint, inspect the request in DevTools Network, and copy the `x-mas` request header into `FOTMOB_X_MAS`.

## MCP Server

Run locally:

```bash
fotmob-mcp
```

Register in Codex:

```bash
codex mcp add fotmob -- ./.venv/bin/python -m fotmob_mcp.server
```

Resources:

- `fotmob://reference`
- `fotmob://routes`
- `fotmob://prompt`

Tools:

- `list_fotmob_routes`
- `fetch_fotmob_route`
- `search_fotmob`
