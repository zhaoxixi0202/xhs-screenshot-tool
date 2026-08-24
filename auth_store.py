from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from pathlib import Path


class AuthStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def has_accounts(self) -> bool:
        return bool(self.list_accounts())

    def list_accounts(self) -> list[dict]:
        data = self._read()
        return [
            {
                "username": item["username"],
                "role": item.get("role", "user"),
                "active": bool(item.get("active", True)),
                "createdAt": item.get("createdAt", ""),
                "updatedAt": item.get("updatedAt", ""),
            }
            for item in data.get("accounts", [])
        ]

    def create_first_admin(self, username: str, password: str) -> dict:
        if self.has_accounts():
            raise ValueError("管理员账号已存在")
        return self.upsert_account(username, password, role="admin", active=True)

    def upsert_account(self, username: str, password: str, role: str = "user", active: bool = True) -> dict:
        username = self._clean_username(username)
        self._validate_password(password)
        if role not in {"admin", "user"}:
            raise ValueError("角色只能是 admin 或 user")

        data = self._read()
        accounts = data.setdefault("accounts", [])
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        password_data = self._hash_password(password)
        for item in accounts:
            if item["username"].lower() == username.lower():
                item.update(password_data)
                item["role"] = role
                item["active"] = bool(active)
                item["updatedAt"] = now
                self._write(data)
                return self._public_account(item)

        item = {
            "username": username,
            "role": role,
            "active": bool(active),
            "createdAt": now,
            "updatedAt": now,
            **password_data,
        }
        accounts.append(item)
        self._write(data)
        return self._public_account(item)

    def set_active(self, username: str, active: bool) -> None:
        data = self._read()
        item = self._find(data, username)
        if not item:
            raise ValueError("账号不存在")
        item["active"] = bool(active)
        item["updatedAt"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self._write(data)

    def verify_login(self, username: str, password: str) -> dict | None:
        data = self._read()
        item = self._find(data, username)
        if not item or not item.get("active", True):
            return None
        expected = self._derive(password, item["salt"], int(item.get("iterations", 260000)))
        if hmac.compare_digest(expected, item["passwordHash"]):
            return self._public_account(item)
        return None

    def _read(self) -> dict:
        if not self.path.exists():
            return {"accounts": []}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {"accounts": []}

    def _write(self, data: dict) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _find(self, data: dict, username: str) -> dict | None:
        clean = self._clean_username(username).lower()
        for item in data.get("accounts", []):
            if item.get("username", "").lower() == clean:
                return item
        return None

    def _clean_username(self, username: str) -> str:
        username = str(username or "").strip()
        if len(username) < 3:
            raise ValueError("账号名至少 3 个字符")
        return username

    def _validate_password(self, password: str) -> None:
        if len(str(password or "")) < 6:
            raise ValueError("密码至少 6 个字符")

    def _hash_password(self, password: str) -> dict:
        salt = base64.b64encode(os.urandom(16)).decode("ascii")
        iterations = 260000
        return {
            "salt": salt,
            "iterations": iterations,
            "passwordHash": self._derive(password, salt, iterations),
        }

    def _derive(self, password: str, salt: str, iterations: int) -> str:
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            str(password).encode("utf-8"),
            base64.b64decode(salt.encode("ascii")),
            iterations,
        )
        return base64.b64encode(digest).decode("ascii")

    def _public_account(self, item: dict) -> dict:
        return {
            "username": item["username"],
            "role": item.get("role", "user"),
            "active": bool(item.get("active", True)),
            "createdAt": item.get("createdAt", ""),
            "updatedAt": item.get("updatedAt", ""),
        }
