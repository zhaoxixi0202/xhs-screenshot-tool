#!/usr/bin/env python3
from __future__ import annotations

import cgi
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from auth_store import AuthStore


HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8799"))
DATA_DIR = Path(os.environ.get("AUTH_DATA_DIR", "auth_data"))
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "change-me")
STORE = AuthStore(DATA_DIR / "accounts.json")


def html_page(message: str = "") -> bytes:
    rows = "\n".join(
        f"<tr><td>{a['username']}</td><td>{a['role']}</td><td>{'启用' if a['active'] else '禁用'}</td><td>{a['updatedAt']}</td></tr>"
        for a in STORE.list_accounts()
    )
    return f"""<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><title>账号管理中心</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:920px;margin:30px auto;padding:0 16px}}input,select{{padding:8px;margin:4px 0;width:100%}}button{{padding:9px 14px;background:#e5485d;color:white;border:0;border-radius:6px}}table{{width:100%;border-collapse:collapse;margin-top:18px}}td,th{{border:1px solid #ddd;padding:8px;text-align:left}}.msg{{color:#b42318}}</style>
<h1>账号管理中心</h1>
<p class="msg">{message}</p>
<form method="post" action="/admin/accounts">
  <input name="token" placeholder="管理员令牌" required>
  <input name="username" placeholder="账号" required>
  <input name="password" placeholder="密码（至少 6 位）" type="password" required>
  <select name="role"><option value="user">普通用户</option><option value="admin">管理员</option></select>
  <select name="active"><option value="1">启用</option><option value="0">禁用</option></select>
  <button type="submit">新增/重置账号</button>
</form>
<form method="post" action="/admin/toggle" style="margin-top:16px">
  <input name="token" placeholder="管理员令牌" required>
  <input name="username" placeholder="要启用/禁用的账号" required>
  <select name="active"><option value="1">启用</option><option value="0">禁用</option></select>
  <button type="submit">更新状态</button>
</form>
<table><tr><th>账号</th><th>角色</th><th>状态</th><th>更新时间</th></tr>{rows}</table>
</html>""".encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def send_bytes(self, body: bytes, content_type: str = "text/html; charset=utf-8", status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, payload: dict, status: int = 200) -> None:
        self.send_bytes(json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", status)

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/admin":
            return self.send_bytes(html_page())
        if urlparse(self.path).path == "/health":
            return self.send_json({"ok": True})
        self.send_error(404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/login":
            return self.login()
        if path == "/admin/accounts":
            return self.upsert()
        if path == "/admin/toggle":
            return self.toggle()
        self.send_error(404)

    def read_form(self) -> dict[str, str]:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        return {k: v[0] for k, v in parse_qs(body).items()}

    def login(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        data = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        account = STORE.verify_login(data.get("username", ""), data.get("password", ""))
        if not account:
            return self.send_json({"ok": False, "error": "账号或密码错误"}, 401)
        return self.send_json({"ok": True, "account": account})

    def require_token(self, form: dict[str, str]) -> bool:
        return form.get("token") == ADMIN_TOKEN

    def upsert(self) -> None:
        form = self.read_form()
        if not self.require_token(form):
            return self.send_bytes(html_page("管理员令牌错误"), status=403)
        try:
            STORE.upsert_account(
                form.get("username", ""),
                form.get("password", ""),
                role=form.get("role", "user"),
                active=form.get("active", "1") == "1",
            )
            return self.send_bytes(html_page("已保存账号"))
        except Exception as exc:
            return self.send_bytes(html_page(str(exc)), status=400)

    def toggle(self) -> None:
        form = self.read_form()
        if not self.require_token(form):
            return self.send_bytes(html_page("管理员令牌错误"), status=403)
        try:
            STORE.set_active(form.get("username", ""), form.get("active", "1") == "1")
            return self.send_bytes(html_page("已更新状态"))
        except Exception as exc:
            return self.send_bytes(html_page(str(exc)), status=400)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"账号管理中心：http://{HOST}:{PORT}/admin")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
