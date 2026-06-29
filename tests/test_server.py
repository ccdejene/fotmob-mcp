from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from fotmob_mcp.client import FotMobUnavailable
from fotmob_mcp.server import (
    extract_match_id,
    fetch_fotmob_route,
    get_league_top_stats,
    get_live_fixtures,
    get_match_liveticker,
    get_match_details,
    get_route_catalog,
    list_fotmob_routes,
    render_prompt_template,
)


class FotMobMcpTests(unittest.TestCase):
    def test_route_catalog_includes_search_and_match_routes(self) -> None:
        routes = get_route_catalog()
        keys = {route["key"] for route in routes}
        self.assertIn("search_suggest", keys)
        self.assertIn("match_details", keys)
        self.assertIn("league_season_deep_stats", keys)
        self.assertIn("match_liveticker", keys)
        self.assertIn("match_heatmaps", keys)
        self.assertIn("transfers", keys)

    def test_prompt_mentions_search_suggest(self) -> None:
        prompt = render_prompt_template()
        self.assertIn("/api/data/search/suggest", prompt)
        self.assertIn("/api/data/leagues", prompt)
        self.assertIn("/api/data/leagueseasondeepstats", prompt)
        self.assertIn("/api/data/ltc", prompt)
        self.assertIn("/api/data/heatmap/match/{matchId}/heatmaps", prompt)
        self.assertIn("/api/data/transfers", prompt)

    def test_fetch_route_uses_client(self) -> None:
        client = MagicMock()
        client.get_json.return_value = {"ok": True}
        with patch("fotmob_mcp.server.FotMobClient", return_value=client):
            payload = fetch_fotmob_route("search_suggest", {"term": "neth"})
        self.assertEqual(payload["path"], "/api/data/search/suggest")
        self.assertEqual(payload["params"]["term"], "neth")
        client.get_json.assert_called_once()

    def test_fetch_route_adds_search_defaults(self) -> None:
        client = MagicMock()
        client.get_json.return_value = [{"suggestions": []}]
        with patch("fotmob_mcp.server.FotMobClient", return_value=client):
            fetch_fotmob_route("search_suggest", {"term": "neth"})
        client.get_json.assert_called_once()
        _, params = client.get_json.call_args.args
        self.assertEqual(params["hits"], "10")
        self.assertEqual(params["lang"], "en")

    def test_fetch_route_adds_shotmap_default(self) -> None:
        client = MagicMock()
        client.get_json.return_value = {"ok": True}
        with patch("fotmob_mcp.server.FotMobClient", return_value=client):
            fetch_fotmob_route("leagues_shotmap", {"id": "77", "season": "2026", "ccode3": "INT"})
        client.get_json.assert_called_once()
        _, params = client.get_json.call_args.args
        self.assertEqual(params["shotmap"], "true")

    def test_fetch_route_supports_league_season_deep_stats(self) -> None:
        client = MagicMock()
        client.get_json.return_value = {"statsData": []}
        with patch("fotmob_mcp.server.FotMobClient", return_value=client):
            payload = fetch_fotmob_route(
                "league_season_deep_stats",
                {"id": "77", "season": "24254", "type": "players", "stat": "goals"},
            )
        self.assertEqual(payload["path"], "/api/data/leagueseasondeepstats")
        client.get_json.assert_called_once_with(
            "/api/data/leagueseasondeepstats",
            {"id": "77", "season": "24254", "type": "players", "stat": "goals"},
            use_cache=False,
        )

    def test_fetch_route_supports_match_heatmaps(self) -> None:
        client = MagicMock()
        client.get_json.return_value = {"players": {}}
        with patch("fotmob_mcp.server.FotMobClient", return_value=client):
            payload = fetch_fotmob_route(
                "match_heatmaps",
                {"matchId": "4667787", "heatmapUrl": "https://pub.fotmob.com/prod/db/api/heatmap/match/4667787"},
            )
        self.assertEqual(payload["path"], "/api/data/heatmap/match/4667787/heatmaps")
        client.get_json.assert_called_once_with(
            "/api/data/heatmap/match/4667787/heatmaps",
            {"heatmapUrl": "https://pub.fotmob.com/prod/db/api/heatmap/match/4667787"},
            use_cache=False,
        )

    def test_fetch_route_bypasses_cache_for_match_details(self) -> None:
        client = MagicMock()
        client.get_json.return_value = {"general": {"matchId": "4653711"}}
        with patch("fotmob_mcp.server.FotMobClient", return_value=client):
            fetch_fotmob_route("match_details", {"matchId": "4653711"})
        client.get_json.assert_called_once_with(
            "/api/data/matchDetails",
            {"matchId": "4653711"},
            use_cache=False,
        )

    def test_fetch_route_supports_match_liveticker(self) -> None:
        client = MagicMock()
        client.get_json.return_value = {"events": []}
        fetch_fotmob_route(
            "match_liveticker",
            {
                "ltcUrl": "https://data.fotmob.com/webcl/ltc/gsm/4653711_en.json.gz",
                "teams": "[\"Brazil\",\"Japan\"]",
            },
            client,
        )
        client.get_json.assert_called_once_with(
            "/api/data/ltc",
            {
                "ltcUrl": "https://data.fotmob.com/webcl/ltc/gsm/4653711_en.json.gz",
                "teams": "[\"Brazil\",\"Japan\"]",
            },
            use_cache=False,
        )

    def test_fetch_route_can_opt_into_cache(self) -> None:
        client = MagicMock()
        client.get_json.return_value = {"ok": True}
        fetch_fotmob_route("teams", {"id": "8256"}, client, use_cache=True)
        client.get_json.assert_called_once_with(
            "/api/data/teams",
            {"id": "8256"},
            use_cache=True,
        )

    def test_extract_match_id_supports_fotmob_urls(self) -> None:
        self.assertEqual(
            extract_match_id("https://www.fotmob.com/en-GB/matches/japan-vs-brazil/1uqadm#4653711"),
            "4653711",
        )
        self.assertEqual(extract_match_id("4653711"), "4653711")

    def test_get_match_details_accepts_match_url(self) -> None:
        client = MagicMock()
        client.get_json.return_value = {
            "general": {"started": True, "finished": False},
            "header": {"status": {"scoreStr": "1 - 0"}},
        }
        result = get_match_details(
            "https://www.fotmob.com/en-GB/matches/japan-vs-brazil/1uqadm#4653711",
            client=client,
        )
        self.assertEqual(result["matchId"], "4653711")
        self.assertEqual(result["started"], True)
        self.assertEqual(result["finished"], False)
        client.get_json.assert_called_once_with(
            "/api/data/matchDetails",
            {"matchId": "4653711"},
            use_cache=False,
        )

    def test_get_match_liveticker_derives_url_and_teams(self) -> None:
        client = MagicMock()
        client.get_json.side_effect = [
            {
                "content": {"liveticker": {"teams": ["Brazil", "Japan"]}},
                "general": {"started": True, "finished": True},
                "header": {"status": {"scoreStr": "2 - 1"}},
            },
            {"events": [{"type": "comment", "text": "FULL-TIME: BRAZIL 2-1 JAPAN"}]},
        ]
        result = get_match_liveticker(
            "https://www.fotmob.com/en-GB/matches/japan-vs-brazil/1uqadm#4653711",
            client=client,
        )
        self.assertEqual(result["matchId"], "4653711")
        self.assertEqual(result["teams"], ["Brazil", "Japan"])
        self.assertEqual(result["params"]["ltcUrl"], "https://data.fotmob.com/webcl/ltc/gsm/4653711_en.json.gz")
        self.assertEqual(result["params"]["teams"], "[\"Brazil\",\"Japan\"]")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["payload"]["events"][0]["type"], "comment")
        client.get_json.assert_any_call(
            "/api/data/matchDetails",
            {"matchId": "4653711"},
            use_cache=False,
        )
        client.get_json.assert_any_call(
            "/api/data/ltc",
            {
                "ltcUrl": "https://data.fotmob.com/webcl/ltc/gsm/4653711_en.json.gz",
                "teams": "[\"Brazil\",\"Japan\"]",
            },
            use_cache=False,
        )

    def test_get_match_liveticker_falls_back_when_liveticker_is_false(self) -> None:
        client = MagicMock()
        client.get_json.side_effect = [
            {
                "content": {"liveticker": False},
                "general": {
                    "homeTeam": {"name": "Germany"},
                    "awayTeam": {"name": "Paraguay"},
                },
                "header": {"status": {}},
            },
            {"events": [], "hasUrl": False},
        ]
        result = get_match_liveticker("4653703", client=client)
        self.assertEqual(result["teams"], ["Germany", "Paraguay"])
        self.assertEqual(result["params"]["ltcUrl"], "https://data.fotmob.com/webcl/ltc/gsm/4653703_en.json.gz")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["payload"]["hasUrl"], False)

    def test_get_match_liveticker_returns_unavailable_when_ltc_missing(self) -> None:
        client = MagicMock()
        client.get_json.side_effect = [
            {
                "content": {"liveticker": False},
                "general": {
                    "homeTeam": {"name": "Afturelding"},
                    "awayTeam": {"name": "Aegir"},
                },
                "header": {"status": {"scoreStr": "1 - 0"}},
            },
            FotMobUnavailable("no ticker"),
        ]
        result = get_match_liveticker("5225781", client=client)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["payload"], {"events": [], "hasUrl": False})
        self.assertEqual(result["teams"], ["Afturelding", "Aegir"])

    def test_get_league_top_stats_resolves_internal_season_id(self) -> None:
        client = MagicMock()
        client.get_json.side_effect = [
            {"statsData": [], "seasons": [{"id": 24254, "name": "2026"}]},
            {"statsData": [{"name": "Lionel Messi", "statValue": {"value": 6}}]},
        ]
        result = get_league_top_stats("77", "2026", "goals", "players", 1, client=client)
        self.assertEqual(result["resolvedSeason"], "24254")
        self.assertEqual(result["statsData"], [{"name": "Lionel Messi", "statValue": {"value": 6}}])
        self.assertEqual(client.get_json.call_count, 2)

    def test_get_live_fixtures_returns_pending_before_poll(self) -> None:
        client = MagicMock()
        client.get_json.return_value = {
            "playoff": {
                "liveFixtureApiLink": {
                    "url": "https://pub.fotmob.com/prod/db/api/fixture/live?leagueId=77",
                    "pollFromUtc": "2099-06-28T18:55:00Z",
                }
            }
        }
        result = get_live_fixtures("77", "2026", client=client)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["payload"], [])
        self.assertEqual(client.get_json.call_count, 1)
        client.get_json.assert_called_once_with(
            "/api/data/leagues",
            {"id": "77", "season": "2026", "ccode3": "INT"},
            use_cache=False,
        )

    def test_get_live_fixtures_fetches_poll_payload_after_start(self) -> None:
        client = MagicMock()
        client.get_json.side_effect = [
            {
                "playoff": {
                    "liveFixtureApiLink": {
                        "url": "https://pub.fotmob.com/prod/db/api/fixture/live?leagueId=77",
                        "pollFromUtc": "2000-06-28T18:55:00Z",
                    }
                }
            },
            {"fixtures": [{"id": 1}]},
        ]
        result = get_live_fixtures("77", "2026", client=client)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["payload"], {"fixtures": [{"id": 1}]})
        self.assertEqual(client.get_json.call_count, 2)
        client.get_json.assert_any_call(
            "https://pub.fotmob.com/prod/db/api/fixture/live?leagueId=77",
            {},
            use_cache=False,
        )

    def test_get_live_fixtures_handles_poll_unavailable(self) -> None:
        client = MagicMock()
        client.get_json.side_effect = [
            {
                "playoff": {
                    "liveFixtureApiLink": {
                        "url": "https://pub.fotmob.com/prod/db/api/fixture/live?leagueId=77",
                        "pollFromUtc": "2000-06-28T18:55:00Z",
                    }
                }
            },
            FotMobUnavailable("no live payload"),
        ]
        result = get_live_fixtures("77", "2026", client=client)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["payload"], [])

    def test_list_routes_filters_keyword(self) -> None:
        result = list_fotmob_routes("match")
        self.assertGreaterEqual(result["count"], 2)
        keys = {route["key"] for route in result["routes"]}
        self.assertIn("matches", keys)
        self.assertIn("match_details", keys)


if __name__ == "__main__":
    unittest.main()
