import os
from pathlib import Path
from threading import RLock, local
from typing import Any

import httpx
from dotenv import load_dotenv
from supabase import Client, create_client
from supabase_auth.errors import AuthApiError, AuthInvalidJwtError, AuthRetryableError

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

supabase_url = os.getenv("SUPABASE_URL")
service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url:
    raise RuntimeError("SUPABASE_URL is not set")

if not service_role_key:
    raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is not set")

class ThreadLocalSupabaseClient:
    """Keep sync HTTP connection pools isolated between FastAPI worker threads."""

    def __init__(self, url: str, key: str) -> None:
        self._url = url
        self._key = key
        self._local = local()

    def _client(self) -> Client:
        client = getattr(self._local, "client", None)
        if client is None:
            client = create_client(self._url, self._key)
            self._local.client = client
        return client

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client(), name)


supabase = ThreadLocalSupabaseClient(supabase_url, service_role_key)

# Keep one verifier so the project's public signing keys stay cached in-process.
# get_claims verifies asymmetric JWTs locally after the first JWKS fetch instead
# of making every authenticated API request wait on Supabase Auth.
_auth_verifier = create_client(supabase_url, service_role_key)
_auth_verifier_lock = RLock()


def _verify_with_fallback(access_token: str):
    try:
        return _auth_verifier.auth.get_claims(access_token)
    except AuthInvalidJwtError:
        # Auth is authoritative when a signing key has just rotated or a cached
        # JWKS cannot validate an otherwise-current browser session.
        return _auth_verifier.auth.get_user(access_token)


def verify_access_token(access_token: str):
    global _auth_verifier

    with _auth_verifier_lock:
        try:
            return _verify_with_fallback(access_token)
        except AuthApiError as exc:
            if exc.status < 500:
                raise
        except (AuthRetryableError, httpx.TransportError, OSError):
            pass

        # A cold JWKS request can fail transiently. Recreate the client to discard
        # a broken connection pool and retry once; the caller maps a second
        # failure to 503 without invalidating the browser session.
        _auth_verifier = create_client(supabase_url, service_role_key)
        return _verify_with_fallback(access_token)
