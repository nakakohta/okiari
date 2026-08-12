import os
from pathlib import Path
from threading import RLock, local
from typing import Any

from dotenv import load_dotenv
from supabase import Client, create_client

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

# Keep authentication verification serialized on the shared sync client.  Using
# Auth's user endpoint avoids rejecting otherwise-valid tokens when signing keys
# are rotated or a local JWKS cache is temporarily stale.
_auth_verifier = create_client(supabase_url, service_role_key)
_auth_verifier_lock = RLock()


def verify_access_token(access_token: str):
    with _auth_verifier_lock:
        return _auth_verifier.auth.get_user(access_token)
