
from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "pingpong_secret"

def get_db():
    return sqlite3.connect("pingpong.db")

def login_required():
    return "user_id" in session

@app.context_processor
def inject_user():
    return dict(logged_in=("user_id" in session))

@app.route("/")
def index():
    if not login_required():
        return redirect("/login")

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT rating FROM users WHERE id=?", (session["user_id"],))
    rating = cur.fetchone()[0]

    cur.execute("SELECT opponent,result,delta,created_at FROM matches WHERE user_id=? ORDER BY created_at DESC",
                (session["user_id"],))
    matches = cur.fetchall()

    if rating == 0:
        return render_template("choose_level.html")
    return render_template("dashboard.html", rating=rating, matches=matches)

@app.route("/choose_level", methods=["POST"])
def choose_level():
    rating = {"beginner":500,"intermediate":1000,"advanced":1500}[request.form["level"]]
    db = get_db()
    db.execute("UPDATE users SET rating=? WHERE id=?", (rating, session["user_id"]))
    db.commit()
    return redirect("/")

@app.route("/match", methods=["GET","POST"])
def match():
    if not login_required():
        return redirect("/login")

    if request.method == "POST":
        opponent = request.form["opponent"]
        result = request.form["result"]
        delta = 20 if result == "win" else -15

        db = get_db()
        db.execute(
            "INSERT INTO matches(user_id,opponent,result,delta) VALUES (?,?,?,?)",
            (session["user_id"], opponent, result, delta)
        )
        db.execute(
            "UPDATE users SET rating = rating + ? WHERE id=?",
            (delta, session["user_id"])
        )
        db.commit()
        return redirect("/")

    return render_template("match.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        db = get_db()
        db.execute(
            "INSERT INTO users(username,password_hash,role) VALUES (?,?,?)",
            (request.form["username"],
             generate_password_hash(request.form["password"]),
             "user")
        )
        db.commit()
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT id,password_hash FROM users WHERE username=?",
                    (request.form["username"],))
        u = cur.fetchone()
        if u and check_password_hash(u[1], request.form["password"]):
            session["user_id"] = u[0]
            return redirect("/")
    return render_template("login.html")

@app.route("/rank")
def rank():
    db = get_db()
    users = db.execute("SELECT username,rating FROM users ORDER BY rating DESC").fetchall()
    return render_template("rank.html", users=users)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

app.run(debug=True)
