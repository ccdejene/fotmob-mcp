from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from fotmob_mcp.server import fetch_fotmob_route, get_league_top_stats, get_live_fixtures, get_route_catalog, list_fotmob_routes, render_prompt_template


class FotMobMcpTests(unittest.TestCase):
    def test_route_catalog_includes_search_and_match_routes(self) -> None:
        routes = get_route_catalog()
        keys = {route["key"] for route in routes}
        self.assertIn("search_suggest", keys)
        self.assertIn("match_details", keys)
        self.assertIn("league_season_deep_stats", keys)
        self.assertIn("match_heatmaps", keys)
        self.assertIn("transfers", keys)

    def test_prompt_mentions_search_suggest(self) -> None:
        prompt = render_prompt_template()
        self.assertIn("/api/data/search/suggest", prompt)
        self.assertIn("/api/data/leagues", prompt)
        self.assertIn("/api/data/leagueseasondeepstats", prompt)
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
        )

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

    def test_list_routes_filters_keyword(self) -> None:
        result = list_fotmob_routes("match")
        self.assertGreaterEqual(result["count"], 2)
        keys = {route["key"] for route in result["routes"]}
        self.assertIn("matches", keys)
        self.assertIn("match_details", keys)


if __name__ == "__main__":
    unittest.main()
