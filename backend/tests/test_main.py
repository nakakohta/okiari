import os
import re
import unittest
from unittest.mock import patch

from app.main import DEFAULT_CORS_ORIGIN_REGEX, _cors_origins


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


if __name__ == "__main__":
    unittest.main()
