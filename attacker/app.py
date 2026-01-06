from __future__ import annotations

import os

from flask import Flask, render_template, request

app = Flask(__name__)

VICTIM_ORIGIN = os.environ.get("VICTIM_ORIGIN", "http://127.0.0.1:5000").rstrip("/")


@app.get("/")
def attack():
    debug = request.args.get("debug") == "1"
    new_email = request.args.get("new_email", "attacker@evil.test")
    return render_template(
        "attack.html",
        victim_origin=VICTIM_ORIGIN,
        debug=debug,
        new_email=new_email,
    )


@app.get("/legit")
def legit():
    # “Legalny” przypadek: osadzamy publiczną treść ofiary (np. widget/banner).
    return render_template("legit.html", victim_origin=VICTIM_ORIGIN)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False)


