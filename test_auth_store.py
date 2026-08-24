import tempfile
import unittest
from pathlib import Path

from auth_store import AuthStore


class AuthStoreTest(unittest.TestCase):
    def test_first_admin_can_login_and_password_is_hashed(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = AuthStore(Path(tmp) / "accounts.json")
            account = store.create_first_admin("admin", "secret123")

            self.assertEqual(account["role"], "admin")
            self.assertTrue(store.verify_login("admin", "secret123"))
            raw = (Path(tmp) / "accounts.json").read_text(encoding="utf-8")
            self.assertNotIn("secret123", raw)

    def test_admin_can_create_and_disable_user(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = AuthStore(Path(tmp) / "accounts.json")
            store.create_first_admin("admin", "secret123")

            user = store.upsert_account("staff", "pw123456", role="user", active=True)
            self.assertEqual(user["username"], "staff")
            self.assertTrue(store.verify_login("staff", "pw123456"))

            store.set_active("staff", False)
            self.assertFalse(store.verify_login("staff", "pw123456"))


if __name__ == "__main__":
    unittest.main()
