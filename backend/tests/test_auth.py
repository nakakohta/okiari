import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from supabase_auth.errors import AuthInvalidJwtError, AuthRetryableError

from app.core.auth import get_current_user, invalidate_user_profile_cache


class AuthVerificationTests(unittest.TestCase):
    def setUp(self) -> None:
        invalidate_user_profile_cache()
        self.credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="test-token")
        self.profile = {
            "id": "00000000-0000-0000-0000-000000000001",
            "is_active": True,
            "role": {"code": "admin"},
        }

    @patch("app.core.auth.get_user_profile")
    @patch("app.core.auth.verify_access_token")
    def test_verified_claims_and_profile_are_cached(self, get_claims, get_profile) -> None:
        get_claims.return_value = SimpleNamespace(claims={"sub": self.profile["id"]})
        get_profile.return_value = self.profile

        first = get_current_user(self.credentials)
        second = get_current_user(self.credentials)

        self.assertEqual(first.auth_user_id, self.profile["id"])
        self.assertEqual(second.role_code, "admin")
        self.assertEqual(get_claims.call_count, 2)
        self.assertEqual(get_profile.call_count, 1)

    @patch("app.core.auth.verify_access_token")
    def test_invalid_jwt_returns_401(self, get_claims) -> None:
        get_claims.side_effect = AuthInvalidJwtError("invalid")
        with self.assertRaises(HTTPException) as context:
            get_current_user(self.credentials)
        self.assertEqual(context.exception.status_code, 401)

    @patch("app.core.auth.verify_access_token")
    def test_retryable_auth_failure_returns_503(self, get_claims) -> None:
        get_claims.side_effect = AuthRetryableError("temporary", 503)
        with self.assertRaises(HTTPException) as context:
            get_current_user(self.credentials)
        self.assertEqual(context.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
