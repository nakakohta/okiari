import os
import re
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import DEFAULT_CORS_ORIGIN_REGEX, _cors_origins, app


class CorsConfigurationTests(unittest.TestCase):
    def test_default_origins_keep_local_development(self) -> None:
        with patch.dict(os.environ, {"CORS_ORIGINS": ""}):
            self.assertEqual(
                _cors_origins(),
                ["http://localhost:5173", "http://127.0.0.1:5173"],
            )

    def test_configured_origins_are_trimmed(self) -> None:
        with patch.dict(
            os.environ,
            {"CORS_ORIGINS": " http://192.168.1.10:5173/, https://example.test "},
        ):
            self.assertEqual(
                _cors_origins(),
                ["http://192.168.1.10:5173", "https://example.test"],
            )

    def test_default_regex_allows_private_lan_not_public_hosts(self) -> None:
        self.assertIsNotNone(re.fullmatch(DEFAULT_CORS_ORIGIN_REGEX, "http://192.168.1.10:5173"))
        self.assertIsNotNone(re.fullmatch(DEFAULT_CORS_ORIGIN_REGEX, "http://172.31.0.5:5173"))
        self.assertIsNone(re.fullmatch(DEFAULT_CORS_ORIGIN_REGEX, "http://example.com:5173"))


class ProductionSurfaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_public_responses_prevent_indexing(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["x-robots-tag"],
            "noindex, nofollow, noarchive, nosnippet, noimageindex",
        )
        self.assertEqual(response.headers["referrer-policy"], "no-referrer")

    def test_debug_and_schema_routes_are_not_exposed(self) -> None:
        for path in ("/test-reports", "/docs", "/redoc", "/openapi.json"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)


if __name__ == "__main__":
    unittest.main()
