from __future__ import annotations

import json
import os
import random
import threading
from datetime import datetime, timezone
from pathlib import Path
from functools import wraps

from flask import Flask, jsonify, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
QUESTIONS_FILE = DATA_DIR / "questions.json"
USERS_FILE = DATA_DIR / "users.json"
LOCK = threading.Lock()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production-canada-2026")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")


def read_json(path: Path, default):
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    tmp.replace(path)


def questions():
    return read_json(QUESTIONS_FILE, [])


def modules_catalog():
    seen = {}
    for q in questions():
        seen.setdefault(q["module_id"], {"id": q["module_id"], "title": q["module"], "order": q["module_order"]})
    return sorted(seen.values(), key=lambda item: item["order"])


def current_user():
    username = session.get("username")
    if not username:
        return None
    return read_json(USERS_FILE, {}).get(username)


def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not current_user():
            return jsonify({"error": "Authentification requise"}), 401
        return fn(*args, **kwargs)
    return wrapped


def public_question(q):
    return {k: q[k] for k in ("id", "module_id", "module", "question", "choices")}


def module_statuses(user):
    results = user.get("results", {})
    unlocked = True
    output = []
    for module in modules_catalog():
        attempts = results.get(module["id"], [])
        best = max((a["percent"] for a in attempts), default=0)
        last = attempts[-1] if attempts else None
        passed = best >= 75
        output.append({**module, "attempts": len(attempts), "best": best, "last": last, "passed": passed, "unlocked": unlocked})
        unlocked = unlocked and passed
    return output


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/register")
def register():
    payload = request.get_json(force=True)
    name = str(payload.get("name", "")).strip()
    username = str(payload.get("username", "")).strip().lower()
    password = str(payload.get("password", ""))
    if len(name) < 2 or len(username) < 3 or len(password) < 6:
        return jsonify({"error": "Nom, identifiant (3+) et mot de passe (6+) requis."}), 400
    with LOCK:
        users = read_json(USERS_FILE, {})
        if username in users:
            return jsonify({"error": "Cet identifiant existe déjà."}), 409
        users[username] = {"name": name, "password": generate_password_hash(password), "results": {}, "exams": [], "created_at": datetime.now(timezone.utc).isoformat()}
        write_json(USERS_FILE, users)
    session["username"] = username
    return jsonify({"ok": True})


@app.post("/api/login")
def login():
    payload = request.get_json(force=True)
    username = str(payload.get("username", "")).strip().lower()
    user = read_json(USERS_FILE, {}).get(username)
    if not user or not check_password_hash(user["password"], str(payload.get("password", ""))):
        return jsonify({"error": "Identifiant ou mot de passe incorrect."}), 401
    session["username"] = username
    return jsonify({"ok": True})


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.get("/api/dashboard")
@login_required
def dashboard():
    user = current_user()
    statuses = module_statuses(user)
    return jsonify({
        "user": {"name": user["name"]},
        "modules": statuses,
        "completed": sum(1 for m in statuses if m["passed"]),
        "total": len(statuses),
        "exams": user.get("exams", [])[-5:][::-1],
    })


@app.get("/api/quiz/<module_id>")
@login_required
def quiz(module_id):
    mode = request.args.get("mode", "free")
    status = next((m for m in module_statuses(current_user()) if m["id"] == module_id), None)
    if not status:
        return jsonify({"error": "Module introuvable."}), 404
    if mode == "path" and not status["unlocked"]:
        return jsonify({"error": "Réussis d’abord le module précédent."}), 403
    pool = [q for q in questions() if q["module_id"] == module_id]
    count = min(20, len(pool))
    chosen = random.sample(pool, count)
    session["active_quiz"] = {"type": "module", "module_id": module_id, "ids": [q["id"] for q in chosen]}
    return jsonify({"title": status["title"], "questions": [public_question(q) for q in chosen], "pass_mark": 75})


@app.get("/api/exam")
@login_required
def exam():
    pool = questions()
    chosen = random.sample(pool, min(20, len(pool)))
    session["active_quiz"] = {"type": "exam", "ids": [q["id"] for q in chosen]}
    return jsonify({"title": "Examen blanc — 20 questions", "questions": [public_question(q) for q in chosen], "pass_mark": 75, "duration_minutes": 45})


@app.post("/api/answer")
@login_required
def answer():
    payload = request.get_json(force=True)
    active = session.get("active_quiz", {})
    qid = payload.get("question_id")
    if qid not in active.get("ids", []):
        return jsonify({"error": "Question hors session."}), 400
    q = next((item for item in questions() if item["id"] == qid), None)
    selected = payload.get("selected")
    correct = selected == q["answer"]
    return jsonify({"correct": correct, "answer": q["answer"], "explanation": q["explanation"], "source": q.get("source", "Découvrir le Canada")})


@app.post("/api/submit")
@login_required
def submit():
    payload = request.get_json(force=True)
    active = session.get("active_quiz")
    if not active:
        return jsonify({"error": "Aucun quiz actif."}), 400
    qmap = {q["id"]: q for q in questions()}
    answers = payload.get("answers", {})
    total = len(active["ids"])
    score = sum(1 for qid in active["ids"] if answers.get(qid) == qmap[qid]["answer"])
    percent = round(score * 100 / total) if total else 0
    attempt = {"score": score, "total": total, "percent": percent, "passed": percent >= 75, "date": datetime.now(timezone.utc).isoformat()}
    with LOCK:
        users = read_json(USERS_FILE, {})
        user = users[session["username"]]
        if active["type"] == "exam":
            user.setdefault("exams", []).append(attempt)
        else:
            user.setdefault("results", {}).setdefault(active["module_id"], []).append(attempt)
        write_json(USERS_FILE, users)
    session.pop("active_quiz", None)
    return jsonify(attempt)


if __name__ == "__main__":
    DATA_DIR.mkdir(exist_ok=True)
    if not QUESTIONS_FILE.exists():
        raise SystemExit("Exécutez d’abord: python generate_questions.py")
    app.run(host="127.0.0.1", port=5000, debug=True)
