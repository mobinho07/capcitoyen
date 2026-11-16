from __future__ import annotations

import json
import os
import random
import threading
import secrets
import click
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
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
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
    user = read_json(USERS_FILE, {}).get(username)
    if not user or not user.get("active", True) or session.get("version", 0) != user.get("version", 0):
        return None
    return user


def start_session(username, user):
    session.clear()
    session.update(username=username, version=user.get("version", 0), csrf=secrets.token_urlsafe(32))


def superadmin_required(fn):
    @wraps(fn)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user().get("role", "user") != "superadmin":
            return jsonify({"error": "Accès réservé au superadmin."}), 403
        if request.method != "GET" and not secrets.compare_digest(request.headers.get("X-CSRF-Token", ""), session.get("csrf", "missing")):
            return jsonify({"error": "Session invalide. Rechargez la page."}), 403
        return fn(*args, **kwargs)
    return wrapped


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
        users[username] = {"name": name, "password": generate_password_hash(password), "version": secrets.token_hex(16), "results": {}, "exams": [], "created_at": datetime.now(timezone.utc).isoformat()}
        write_json(USERS_FILE, users)
    start_session(username, users[username])
    return jsonify({"ok": True})


@app.post("/api/login")
def login():
    payload = request.get_json(force=True)
    username = str(payload.get("username", "")).strip().lower()
    user = read_json(USERS_FILE, {}).get(username)
    if not user or not user.get("active", True) or not check_password_hash(user["password"], str(payload.get("password", ""))):
        return jsonify({"error": "Identifiant ou mot de passe incorrect."}), 401
    start_session(username, user)
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
        "user": {"name": user["name"], "username": session["username"], "role": user.get("role", "user")},
        "csrf": session.setdefault("csrf", secrets.token_urlsafe(32)),
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


@app.get("/api/admin/users")
@superadmin_required
def admin_users():
    output = []
    for username, user in read_json(USERS_FILE, {}).items():
        attempts = [a for items in user.get("results", {}).values() for a in items]
        exams = user.get("exams", [])
        all_attempts = attempts + exams
        output.append({
            "username": username, "name": user["name"], "role": user.get("role", "user"),
            "active": user.get("active", True), "created_at": user.get("created_at"),
            "completed": sum(m["passed"] for m in module_statuses(user)),
            "attempts": len(attempts), "exams": len(exams),
            "average": round(sum(a["percent"] for a in all_attempts) / len(all_attempts), 1) if all_attempts else None,
        })
    return jsonify(users=output, stats={"total": len(output), "active": sum(u["active"] for u in output),
        "attempts": sum(u["attempts"] for u in output), "exams": sum(u["exams"] for u in output)})


@app.post("/api/admin/users")
@superadmin_required
def admin_create():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify(error="Données invalides."), 400
    username = str(payload.get("username", "")).strip().lower()
    name = str(payload.get("name", "")).strip()
    password = str(payload.get("password", ""))
    if len(username) < 3 or len(name) < 2 or len(password) < 6:
        return jsonify(error="Nom (2+), identifiant (3+) et mot de passe (6+) requis."), 400
    with LOCK:
        users = read_json(USERS_FILE, {})
        if username in users:
            return jsonify(error="Cet identifiant existe déjà."), 409
        users[username] = dict(name=name, password=generate_password_hash(password), role="user", active=True, version=secrets.token_hex(16),
                               results={}, exams=[], created_at=datetime.now(timezone.utc).isoformat())
        write_json(USERS_FILE, users)
    return jsonify(ok=True), 201


@app.patch("/api/admin/users/<username>")
@superadmin_required
def admin_update(username):
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify(error="Données invalides."), 400
    with LOCK:
        users = read_json(USERS_FILE, {})
        user = users.get(username)
        if not user:
            return jsonify(error="Utilisateur introuvable."), 404
        name = payload.get("name", user["name"])
        role = payload.get("role", user.get("role", "user"))
        active = payload.get("active", user.get("active", True))
        password = payload.get("password")
        if not isinstance(name, str) or len(name.strip()) < 2 or role not in ("user", "superadmin") or not isinstance(active, bool):
            return jsonify(error="Nom, rôle ou statut invalide."), 400
        if password is not None and (not isinstance(password, str) or len(password) < 6):
            return jsonify(error="Le mot de passe doit contenir au moins 6 caractères."), 400
        if username == session["username"] and (not active or role != "superadmin"):
            return jsonify(error="Vous ne pouvez pas désactiver votre compte ou retirer votre propre rôle."), 400
        user.update(name=name.strip(), role=role, active=active)
        if password is not None:
            user["password"] = generate_password_hash(password)
        if password is not None or not active or role != "superadmin":
            user["version"] = secrets.token_hex(16)
        write_json(USERS_FILE, users)
    return jsonify(ok=True)


@app.delete("/api/admin/users/<username>")
@superadmin_required
def admin_delete(username):
    with LOCK:
        users = read_json(USERS_FILE, {})
        if username == session["username"]:
            return jsonify(error="Vous ne pouvez pas supprimer votre propre compte."), 400
        if username not in users:
            return jsonify(error="Utilisateur introuvable."), 404
        del users[username]
        write_json(USERS_FILE, users)
    return jsonify(ok=True)


@app.cli.command("create-superadmin")
@click.argument("username")
@click.option("--name", prompt="Nom complet")
@click.password_option(confirmation_prompt=True)
def create_superadmin(username, name, password):
    """Créer le premier superadmin depuis le serveur."""
    username = username.strip().lower()
    if len(username) < 3 or len(name.strip()) < 2 or len(password) < 6:
        raise click.ClickException("Nom (2+), identifiant (3+) et mot de passe (6+) requis.")
    with LOCK:
        users = read_json(USERS_FILE, {})
        if username in users:
            raise click.ClickException("Cet identifiant existe déjà. Choisissez un nouvel identifiant.")
        users[username] = dict(name=name.strip(), password=generate_password_hash(password), role="superadmin",
                               active=True, version=secrets.token_hex(16), results={}, exams=[], created_at=datetime.now(timezone.utc).isoformat())
        write_json(USERS_FILE, users)
    click.echo("Superadmin créé.")


if __name__ == "__main__":
    DATA_DIR.mkdir(exist_ok=True)
    if not QUESTIONS_FILE.exists():
        import subprocess
        import sys
        subprocess.run([sys.executable, str(BASE_DIR / "generate_questions.py")], check=True)
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
