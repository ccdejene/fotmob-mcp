from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fotmob_mcp.client import FotMobClient


class FotMobClientTests(unittest.TestCase):
    def test_headers_omit_x_mas_when_unset(self) -> None:
        client = FotMobClient(cache_dir=".cache/test", cache_ttl_seconds=60)
        self.assertNotIn("x-mas", client.headers)

    def test_headers_include_x_mas_when_set(self) -> None:
        client = FotMobClient(cache_dir=".cache/test", cache_ttl_seconds=60, x_mas="abc123")
        self.assertEqual(client.headers["x-mas"], "abc123")

    def test_get_json_accepts_list_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            client = FotMobClient(cache_dir=tmpdir, cache_ttl_seconds=60, x_mas="test")
            response = MagicMock()
            response.raise_for_status.return_value = None
            response.json.return_value = [{"title": "All"}]

            with patch("fotmob_mcp.client.requests.get", return_value=response) as mock_get:
                payload = client.get_json("/api/data/search/suggest", {"term": "neth"})

            self.assertEqual(payload, [{"title": "All"}])
            mock_get.assert_called_once()
            cache_files = list(Path(tmpdir).glob("*.json"))
            self.assertEqual(len(cache_files), 1)


if __name__ == "__main__":
    unittest.main()
