from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from fotmob_mcp.server import fetch_fotmob_route, get_route_catalog, list_fotmob_routes, render_prompt_template


class FotMobMcpTests(unittest.TestCase):
    def test_route_catalog_includes_search_and_match_routes(self) -> None:
        routes = get_route_catalog()
        keys = {route["key"] for route in routes}
        self.assertIn("search_suggest", keys)
        self.assertIn("match_details", keys)
        self.assertIn("league_season_deep_stats", keys)

    def test_prompt_mentions_search_suggest(self) -> None:
        prompt = render_prompt_template()
        self.assertIn("/api/data/search/suggest", prompt)
        self.assertIn("/api/data/leagues", prompt)
        self.assertIn("/api/data/leagueseasondeepstats", prompt)

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

    def test_list_routes_filters_keyword(self) -> None:
        result = list_fotmob_routes("match")
        self.assertGreaterEqual(result["count"], 2)
        keys = {route["key"] for route in result["routes"]}
        self.assertIn("matches", keys)
        self.assertIn("match_details", keys)


if __name__ == "__main__":
    unittest.main()
