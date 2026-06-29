# FotMob API Reference

FotMob MCP wraps verified FotMob JSON routes in a standalone Model Context Protocol server.

It is designed for tools and agents that need live football data without scraping the entire FotMob site manually. The server focuses on the routes that are useful for:

- discovering leagues and teams
- looking up fixtures and match details
- reading lineups, scorers, and performance data
- retrieving player profiles and match history
- searching FotMob entities by name

All requests should go through the shared FotMob client. MCP tools fetch fresh FotMob data by default; local caching is only used when a tool explicitly opts into it.

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
| `/api/data/ltc` | Match live ticker/commentary events | `ltcUrl`, `teams` |
| `/api/data/heatmap/match/{matchId}/heatmaps` | Match player heatmap SVG data | `matchId`, `heatmapUrl` |
| `/api/data/transfers` | Transfer center data | `teamId`, `leagueId`, `page`, `sortBy`, `showLoans` |
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
- `/api/data/transfers`

### Match detail

- `/api/data/matchDetails`
- `/api/data/ltc`
- `/api/data/heatmap/match/{matchId}/heatmaps`
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
GET https://www.fotmob.com/api/data/ltc?ltcUrl=https%3A%2F%2Fdata.fotmob.com%2Fwebcl%2Fltc%2Fgsm%2F4653711_en.json.gz&teams=%5B%22Brazil%22%2C%22Japan%22%5D
GET https://www.fotmob.com/api/data/heatmap/match/4667787/heatmaps?heatmapUrl=https%3A%2F%2Fpub.fotmob.com%2Fprod%2Fdb%2Fapi%2Fheatmap%2Fmatch%2F4667787
GET https://www.fotmob.com/api/data/transfers?teamId=8593
```

## Search Payload Shape

`/api/data/search/suggest` returns mixed suggestions, typically:

- `team`
- `league`
- `player`
- `match`

The search endpoint is useful for quick lookup, but it is not a full indexed search API.

## How to use the MCP

The server exposes these tools:

- `list_fotmob_routes` returns the verified route catalog
- `search_fotmob` queries FotMob suggestions for a search term
- `fetch_fotmob_route` fetches one route by key and parameter object. Fresh by default.
- `get_match_details` fetches match details from a FotMob match id or URL. Fresh by default.
- `get_match_liveticker` fetches match live ticker/commentary events from a FotMob match id or URL. Fresh by default.

It also exposes three resources:

- `fotmob://reference`
- `fotmob://routes`
- `fotmob://prompt`

Typical flow:

1. search a team, league, or player by name
2. fetch the relevant team, league, or match route
3. inspect match details for lineups, scorers, status, stats, and event data
4. opt into caching only when stale data is acceptable

For match pages, prefer `get_match_details` when you have either the match id or a full FotMob URL:

```text
get_match_details("https://www.fotmob.com/en-GB/matches/japan-vs-brazil/1uqadm#4653711")
```

For match commentary/live ticker events, prefer `get_match_liveticker`. It derives `ltcUrl` as `https://data.fotmob.com/webcl/ltc/gsm/{matchId}_{lang}.json.gz` and reads team names from `matchDetails.content.liveticker.teams`:

```text
get_match_liveticker("https://www.fotmob.com/en-GB/matches/japan-vs-brazil/1uqadm#4653711")
```

The match page slug can vary; the helper extracts the match id from the URL fragment. If FotMob has no live ticker file for a match, the tool returns `status: unavailable` with an empty `events` array.

For league stat tables, fetch `/api/data/leagues` first and use the internal season id from its `seasons` list. For example, World Cup 2026 uses `season=24254` for `/api/data/leagueseasondeepstats`, while the overview route can use `season=2026`.

The `get_league_top_stats` tool wraps this by retrying with the internal season id when FotMob returns an empty stat table with a `seasons` mapping.

For heatmaps, fetch `matchDetails` first and pass the returned `heatmapUrl` query value into `match_heatmaps`.

For live fixtures, use `get_live_fixtures`. It reads the league payload's `liveFixtureApiLink`, waits until `pollFromUtc` when present, and returns an empty payload with status metadata if FotMob has not opened the poll yet.

All MCP tools fetch fresh FotMob data by default, including search, league, team, player, match, fixture, heatmap, transfer, TV, audio, and provider routes. Use `use_cache=true` only when stale data is acceptable.

## Configuration

Optional environment variables:

- `FOTMOB_BASE_URL`: override the default FotMob base URL
- `FOTMOB_CACHE_DIR`: change the local cache directory for explicit cache use
- `FOTMOB_CACHE_TTL_SECONDS`: change the cache lifetime for explicit cache use

## MCP Server

After installation, verify that the server command is available on the agent process `PATH`:

```bash
command -v fotmob-mcp
fotmob-mcp --help
```

Run locally:

```bash
fotmob-mcp
```

Register in Codex:

```bash
codex mcp add fotmob -- ./.venv/bin/python -m fotmob_mcp.server
```

Register in Hermes Agent over stdio:

```json
{
  "mcpServers": {
    "fotmob": {
      "command": "fotmob-mcp",
      "args": []
    }
  }
}
```

For Hermes setups that use HTTP MCP, start the server with streamable HTTP:

```bash
fotmob-mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

Then point Hermes at:

```text
http://127.0.0.1:8000/mcp
```

Resources:

- `fotmob://reference`
- `fotmob://routes`
- `fotmob://prompt`

Tools:

- `list_fotmob_routes`
- `fetch_fotmob_route`
- `search_fotmob`
- `get_match_details`
- `get_match_liveticker`
- `get_live_fixtures`
- `get_league_top_stats`
