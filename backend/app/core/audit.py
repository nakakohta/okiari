from datetime import UTC, datetime
from typing import Any

from app.supabase_client import supabase


def write_audit_log(
    *,
    actor_user_id: str,
    target_table: str,
    target_id: str,
    action: str,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> None:
    payload = {
        "user_id": actor_user_id,
        "target_table": target_table,
        "target_id": target_id,
        "action": action,
        "before_data": before,
        "after_data": after,
        "created_at": datetime.now(UTC).isoformat(),
    }
    supabase.table("audit_logs").insert(payload).execute()
