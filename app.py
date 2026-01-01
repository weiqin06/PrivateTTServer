
import math
from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "pingpong_secret"

def get_db():
    conn = sqlite3.connect("pingpong.db")
    conn.row_factory = sqlite3.Row
    return conn

def login_required():
    return "user_id" in session

# --- ELO 算法核心逻辑 ---
def calculate_elo(rating_a, rating_b, actual_score_a, k=32):
    # expected_a 是 A 对 B 的胜率期望
    expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    new_rating_a = rating_a + k * (actual_score_a - expected_a)
    return int(new_rating_a - rating_a)

@app.context_processor
def inject_user():
    is_logged_in = "user_id" in session
    is_admin = False
    if is_logged_in:
        db = get_db()
        user = db.execute("SELECT role FROM users WHERE id=?", (session["user_id"],)).fetchone()
        if user and user["role"] == "admin":
            is_admin = True
    return dict(logged_in=is_logged_in, is_admin=is_admin)

@app.route("/")
def index():
    if not login_required():
        return redirect("/login")

    db = get_db()
    cur = db.execute("SELECT rating FROM users WHERE id=?", (session["user_id"],))
    row = cur.fetchone()
    if not row: return redirect("/logout")
    rating = row["rating"]

    matches = db.execute("SELECT opponent, result, delta, created_at, score FROM matches WHERE user_id=? ORDER BY created_at DESC",
                (session["user_id"],)).fetchall()

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
    
    db = get_db()

    if request.method == "POST":
        opponent_id = request.form["opponent_id"]
        my_score = int(request.form["my_score"])
        op_score = int(request.form["op_score"])
        
        # 判断胜负
        if my_score > op_score:
            result = "win"
            actual_score = 1
        else:
            result = "lose"
            actual_score = 0
        
        score_str = f"{my_score}:{op_score}"

        # 获取双方数据
        me = db.execute("SELECT username, rating FROM users WHERE id=?", (session["user_id"],)).fetchone()
        opponent = db.execute("SELECT username, rating FROM users WHERE id=?", (opponent_id,)).fetchone()
        
        # 计算 ELO
        delta = calculate_elo(me["rating"], opponent["rating"], actual_score)
        
        # 更新积分 (我方)
        db.execute("UPDATE users SET rating = rating + ? WHERE id=?", (delta, session["user_id"]))
        # 更新积分 (对手)
        db.execute("UPDATE users SET rating = rating - ? WHERE id=?", (delta, opponent_id))

        # 记录比赛 (我方视角)
        db.execute(
            "INSERT INTO matches(user_id, opponent, result, delta, score) VALUES (?,?,?,?,?)",
            (session["user_id"], opponent["username"], result, delta, score_str)
        )
        
        # 记录比赛 (对手视角 - 镜像记录)
        op_result = "win" if result == "lose" else "lose"
        op_score_str = f"{op_score}:{my_score}"
        db.execute(
            "INSERT INTO matches(user_id, opponent, result, delta, score) VALUES (?,?,?,?,?)",
            (opponent_id, me["username"], op_result, -delta, op_score_str)
        )

        db.commit()
        return redirect("/")

    # GET: 获取除了自己以外的用户
    users = db.execute("SELECT id, username, rating FROM users WHERE id != ? ORDER BY username", (session["user_id"],)).fetchall()
    return render_template("match.html", opponents=users)

@app.route("/admin")
def admin():
    if not login_required(): return redirect("/login")
    
    db = get_db()
    user = db.execute("SELECT role FROM users WHERE id=?", (session["user_id"],)).fetchone()
    if user["role"] != "admin":
        return "<h1>403 Forbidden</h1><p>You are not an administrator.</p>", 403

    all_users = db.execute("SELECT * FROM users ORDER BY id").fetchall()
    return render_template("admin.html", users=all_users)
# --- 管理员功能路由 ---

@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
def admin_delete_user(user_id):
    if not login_required(): return redirect("/login")
    db = get_db()
    # 鉴权
    admin = db.execute("SELECT role FROM users WHERE id=?", (session["user_id"],)).fetchone()
    if not admin or admin["role"] != "admin": return "Unauthorized", 403
    
    # 防止删除自己
    if user_id == session["user_id"]:
        return "Cannot delete yourself", 400

    db.execute("DELETE FROM users WHERE id=?", (user_id,))
    db.execute("DELETE FROM matches WHERE user_id=?", (user_id,))
    db.commit()
    return redirect("/admin")

@app.route("/admin/update_user/<int:user_id>", methods=["POST"])
def admin_update_user(user_id):
    if not login_required(): return redirect("/login")
    db = get_db()
    admin = db.execute("SELECT role FROM users WHERE id=?", (session["user_id"],)).fetchone()
    if not admin or admin["role"] != "admin": return "Unauthorized", 403

    new_rating = request.form.get("rating")
    new_password = request.form.get("password")

    if new_rating:
        db.execute("UPDATE users SET rating=? WHERE id=?", (new_rating, user_id))
    
    if new_password and len(new_password) > 0:
        hash_pw = generate_password_hash(new_password)
        db.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_pw, user_id))
    
    db.commit()
    return redirect("/admin")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        db = get_db()
        try:
            db.execute(
                "INSERT INTO users(username,password_hash,role) VALUES (?,?,?)",
                (request.form["username"],
                 generate_password_hash(request.form["password"]),
                 "user")
            )
            db.commit()
        except sqlite3.IntegrityError:
            return "Username already exists"
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        db = get_db()
        u = db.execute("SELECT id,password_hash FROM users WHERE username=?",
                    (request.form["username"],)).fetchone()
        if u and check_password_hash(u["password_hash"], request.form["password"]):
            session["user_id"] = u["id"]
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

if __name__ == "__main__":
    app.run(debug=True)
