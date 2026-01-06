from __future__ import annotations

import os
from datetime import datetime, timezone

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

# Uproszczony stan aplikacji (bez logowania/cookies — żeby clickjacking był powtarzalny
# niezależnie od polityk third‑party cookies w przeglądarce).
DEFAULT_EMAIL = "user@example.com"
STATE = {
    "email": DEFAULT_EMAIL,
    "last_change_utc": None,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def current_mode() -> str:
    """
    Tryby (ustawiane przez zmienną środowiskową VICTIM_PROTECTION):
      - none
      - xfo_deny
      - xfo_sameorigin
      - csp_none
      - csp_self
      - csp_allow_attacker      (celowo zła allowlista — do demonstracji)
      - selective_xfo_deny      (nagłówki tylko dla /sensitive/*)
      - selective_csp_self      (nagłówki tylko dla /sensitive/*)
    """
    return os.environ.get("VICTIM_PROTECTION", "none").strip().lower()


def is_selective(mode: str) -> bool:
    return mode.startswith("selective_")


def should_protect_path(mode: str, path: str) -> bool:
    if not is_selective(mode):
        return True
    return path.startswith("/sensitive/")


@app.context_processor
def inject_globals():
    return {
        "mode": current_mode(),
    }


@app.after_request
def add_clickjacking_protection(resp):
    mode = current_mode()
    if mode == "none":
        return resp

    protect = should_protect_path(mode, request.path)
    if not protect:
        return resp

    if mode in {"xfo_deny", "selective_xfo_deny"}:
        resp.headers["X-Frame-Options"] = "DENY"
        return resp

    if mode == "xfo_sameorigin":
        resp.headers["X-Frame-Options"] = "SAMEORIGIN"
        return resp

    if mode == "csp_none":
        resp.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
        return resp

    if mode in {"csp_self", "selective_csp_self"}:
        resp.headers["Content-Security-Policy"] = "frame-ancestors 'self'"
        return resp

    if mode == "csp_allow_attacker":
        # Celowo dopuszczamy origin atakującego, żeby pokazać jak allowlista “odblokowuje” osadzanie.
        resp.headers["Content-Security-Policy"] = (
            "frame-ancestors 'self' http://127.0.0.1:5001 http://localhost:5001"
        )
        return resp

    # Nieznany tryb => zachowujemy się jak "none", ale zostawiamy wartość w UI (pomaga w debugowaniu).
    return resp


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/account")
def account():
    return render_template(
        "account.html",
        email=STATE["email"],
        last_change_utc=STATE["last_change_utc"],
    )


@app.get("/reset")
def reset():
    STATE["email"] = DEFAULT_EMAIL
    STATE["last_change_utc"] = None
    return redirect(url_for("account"))


@app.get("/public/banner")
def public_banner():
    return render_template("public_banner.html")


@app.get("/embed-demo")
def embed_demo():
    # Strona ofiary, która *legalnie* osadza wrażliwą ścieżkę w iframe (ten sam origin).
    return render_template("embed_demo.html")


@app.get("/sensitive/change-email")
def sensitive_change_email():
    new_email = request.args.get("new_email", "attacker@evil.test")
    return render_template("sensitive_change_email.html", new_email=new_email)


@app.post("/sensitive/confirm-change-email")
def sensitive_confirm_change_email():
    new_email = (request.form.get("new_email") or "").strip() or "attacker@evil.test"
    STATE["email"] = new_email
    STATE["last_change_utc"] = utc_now_iso()
    return redirect(url_for("account"))


if __name__ == "__main__":
    # Stabilnie (bez auto-reloadera), żeby w czasie labów nie było “podwójnych” procesów.
    app.run(host="127.0.0.1", port=5000, debug=False)


