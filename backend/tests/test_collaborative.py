import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.core.auth import CurrentUser
from app.routers.collaborative import (
    ClearPayload,
    LockPayload,
    _require_write,
    _validate_values,
    clear_board,
    delete_resource,
    update_lock,
)


def user(role: str) -> CurrentUser:
    return CurrentUser(
        auth_user_id="00000000-0000-0000-0000-000000000000",
        profile={},
        role={"code": role},
    )


class CollaborativeValidationTests(unittest.TestCase):
    def test_rejects_unknown_fields(self) -> None:
        with self.assertRaises(HTTPException) as context:
            _validate_values("d-rows", {"unexpected": True}, create=False)
        self.assertEqual(context.exception.status_code, 400)

    def test_rejects_negative_quantities(self) -> None:
        with self.assertRaises(HTTPException) as context:
            _validate_values("m-rows", {"actual_quantity": -1}, create=False)
        self.assertEqual(context.exception.status_code, 400)

    def test_rejects_invalid_status(self) -> None:
        with self.assertRaises(HTTPException) as context:
            _validate_values("d-rows", {"status": "working"}, create=False)
        self.assertEqual(context.exception.status_code, 400)


class CollaborativePermissionTests(unittest.TestCase):
    def test_viewer_cannot_write(self) -> None:
        with self.assertRaises(HTTPException) as context:
            _require_write(user("viewer"), "m-rows", {"actual_quantity": 1})
        self.assertEqual(context.exception.status_code, 403)

    @patch("app.routers.collaborative._require_store_edit")
    def test_sub_leader_cannot_confirm_inventory(self, _: object) -> None:
        with self.assertRaises(HTTPException) as context:
            _require_write(
                user("sub_leader"),
                "m-rows",
                {"is_confirmed": True},
                {"store_id": 1, "is_confirmed": False},
            )
        self.assertEqual(context.exception.status_code, 403)

    @patch("app.routers.collaborative._require_store_edit")
    def test_leader_can_confirm_inventory(self, _: object) -> None:
        _require_write(
            user("leader"),
            "m-rows",
            {"is_confirmed": True},
            {"store_id": 1, "is_confirmed": False},
        )

    def test_sub_leader_cannot_edit_columns(self) -> None:
        with self.assertRaises(HTTPException) as context:
            _require_write(user("sub_leader"), "md-columns", {"title": "商品"})
        self.assertEqual(context.exception.status_code, 403)

    def test_leader_cannot_delete_or_clear(self) -> None:
        with self.assertRaises(HTTPException) as delete_context:
            delete_resource("drink-refill", "d-rows", 1, user("leader"))
        self.assertEqual(delete_context.exception.status_code, 403)
        with self.assertRaises(HTTPException) as clear_context:
            clear_board("drink-refill", ClearPayload(store_id=1, scope="drink"), user("leader"))
        self.assertEqual(clear_context.exception.status_code, 403)

    def test_sub_leader_cannot_change_locks(self) -> None:
        with self.assertRaises(HTTPException) as context:
            update_lock(
                "drink-refill",
                LockPayload(store_id=1, scope="drink", column_key="note", is_locked=True),
                user("sub_leader"),
            )
        self.assertEqual(context.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
