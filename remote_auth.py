from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import urllib.error
import urllib.request


def bundled_auth_api_url() -> str:
    roots = [Path.cwd(), Path(__file__).resolve().parent]
    if getattr(sys, "frozen", False):
        roots.insert(0, Path(getattr(sys, "_MEIPASS", Path.cwd())))
    for root in roots:
        config = root / "auth_config.json"
        if config.exists():
            try:
                return str(json.loads(config.read_text(encoding="utf-8")).get("authApiUrl", "")).rstrip("/")
            except Exception:
                return ""
    return ""


DEFAULT_AUTH_API_URL = (os.environ.get("XHS_AUTH_API_URL") or bundled_auth_api_url()).rstrip("/")


class RemoteAuthClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or DEFAULT_AUTH_API_URL).rstrip("/")

    def configured(self) -> bool:
        return bool(self.base_url)

    def admin_url(self) -> str:
        return f"{self.base_url}/admin" if self.base_url else ""

    def verify_login(self, username: str, password: str) -> dict | None:
        if not self.base_url:
            raise RuntimeError("未配置账号服务器地址，请联系管理员。")
        payload = json.dumps({"username": username, "password": password}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/login",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in {400, 401, 403}:
                return None
            raise RuntimeError(f"账号服务器异常：HTTP {exc.code}") from exc
        except Exception as exc:
            raise RuntimeError(f"无法连接账号服务器：{exc}") from exc
        if not data.get("ok"):
            return None
        return data.get("account") or None
