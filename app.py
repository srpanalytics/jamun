"""
Jamun — main Flask application.

Stack: Flask (Python) + SQLite (SQL) + server-rendered HTML/CSS/vanilla JS.
Run locally with:  python app.py
"""
import os
import sqlite3
from datetime import datetime

from flask import (
    Flask, g, request, session, redirect, url_for,
    render_template, jsonify, flash
)
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "jamun.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")

CATEGORIES = [
    "Marketing", "Coding & Development", "Writing & Content",
    "Business & Strategy", "Education", "Productivity",
    "Data Analysis", "Image Generation",
]
TARGET_MODELS = ["GPT-4", "GPT-5", "Claude", "Gemini", "Midjourney", "DALL·E", "Any Model"]

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")


# ----------------------------------------------------------------------
# Database helpers
# ----------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        db.executescript(f.read())
    db.commit()


@app.cli.command("init-db")
def init_db_command():
    """Flask CLI: `flask --app app init-db` — wipes and recreates all tables."""
    init_db()
    print("Database initialized.")


def ensure_database_ready():
    """Create + seed the DB automatically on first run so the site works out of the box."""
    if not os.path.exists(DB_PATH):
        with app.app_context():
            init_db()
            from seed import seed_data
            seed_data(get_db())
            print("Database created and seeded with demo data.")


# ----------------------------------------------------------------------
# Auth helpers
# ----------------------------------------------------------------------
def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()


def login_required_redirect():
    flash("Please log in to continue.", "error")
    return redirect(url_for("login", next=request.path))


@app.context_processor
def inject_globals():
    return {
        "current_user": current_user(),
        "categories": CATEGORIES,
        "target_models": TARGET_MODELS,
    }


# ----------------------------------------------------------------------
# Public pages
# ----------------------------------------------------------------------
@app.route("/")
def index():
    db = get_db()
    featured = db.execute(
        """
        SELECT p.*, u.name AS creator_name,
               (SELECT ROUND(AVG(rating), 1) FROM reviews WHERE prompt_id = p.id) AS avg_rating,
               (SELECT COUNT(*) FROM reviews WHERE prompt_id = p.id) AS review_count
        FROM prompts p JOIN users u ON u.id = p.creator_id
        ORDER BY p.sales_count DESC, p.created_at DESC
        LIMIT 6
        """
    ).fetchall()
    stats = db.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM prompts) AS total_prompts,
            (SELECT COUNT(*) FROM users WHERE role = 'creator') AS total_creators,
            (SELECT COUNT(*) FROM purchases) AS total_sales
        """
    ).fetchone()
    return render_template("index.html", featured=featured, stats=stats)


@app.route("/marketplace")
def marketplace():
    return render_template("marketplace.html", initial_category=request.args.get("category", ""))


@app.route("/prompt/<int:prompt_id>")
def prompt_detail(prompt_id):
    db = get_db()
    prompt = db.execute(
        """
        SELECT p.*, u.name AS creator_name, u.bio AS creator_bio, u.id AS creator_user_id,
               (SELECT ROUND(AVG(rating), 1) FROM reviews WHERE prompt_id = p.id) AS avg_rating,
               (SELECT COUNT(*) FROM reviews WHERE prompt_id = p.id) AS review_count
        FROM prompts p JOIN users u ON u.id = p.creator_id
        WHERE p.id = ?
        """,
        (prompt_id,),
    ).fetchone()

    if prompt is None:
        return render_template("404.html"), 404

    reviews = db.execute(
        """
        SELECT r.*, u.name AS buyer_name
        FROM reviews r JOIN users u ON u.id = r.buyer_id
        WHERE r.prompt_id = ?
        ORDER BY r.created_at DESC
        """,
        (prompt_id,),
    ).fetchall()

    user = current_user()
    owns = False
    is_owner = False
    user_review = None
    if user:
        is_owner = user["id"] == prompt["creator_id"]
        if not is_owner:
            owns = db.execute(
                "SELECT 1 FROM purchases WHERE buyer_id = ? AND prompt_id = ?",
                (user["id"], prompt_id),
            ).fetchone() is not None
            user_review = db.execute(
                "SELECT * FROM reviews WHERE buyer_id = ? AND prompt_id = ?",
                (user["id"], prompt_id),
            ).fetchone()

    # other prompts by the same creator
    more_from_creator = db.execute(
        "SELECT id, title, price FROM prompts WHERE creator_id = ? AND id != ? LIMIT 4",
        (prompt["creator_id"], prompt_id),
    ).fetchall()

    return render_template(
        "prompt_detail.html",
        prompt=prompt, reviews=reviews, owns=owns, is_owner=is_owner,
        user_review=user_review, more_from_creator=more_from_creator,
    )


# ----------------------------------------------------------------------
# Auth pages
# ----------------------------------------------------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user():
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "buyer")
        bio = request.form.get("bio", "").strip()

        error = None
        if not name or not email or not password:
            error = "Name, email, and password are all required."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif role not in ("buyer", "creator"):
            error = "Invalid role."

        db = get_db()
        if error is None:
            existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if existing:
                error = "That email is already registered — try logging in instead."

        if error:
            flash(error, "error")
            return render_template("signup.html", form=request.form)

        password_hash = generate_password_hash(password)
        cur = db.execute(
            "INSERT INTO users (name, email, password_hash, role, bio) VALUES (?, ?, ?, ?, ?)",
            (name, email, password_hash, role, bio),
        )
        db.commit()
        session.clear()
        session["user_id"] = cur.lastrowid
        flash(f"Welcome to jamun, {name}!", "success")
        return redirect(url_for("dashboard") if role == "creator" else url_for("marketplace"))

    return render_template("signup.html", form={})


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Incorrect email or password.", "error")
            return render_template("login.html", email=email)

        session.clear()
        session["user_id"] = user["id"]
        flash(f"Welcome back, {user['name']}!", "success")
        next_url = request.args.get("next")
        return redirect(next_url or url_for("index"))

    return render_template("login.html", email="")


@app.route("/logout")
def logout():
    session.clear()
    flash("You've been logged out.", "success")
    return redirect(url_for("index"))


# ----------------------------------------------------------------------
# Creator dashboard
# ----------------------------------------------------------------------
@app.route("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return login_required_redirect()

    db = get_db()
    my_prompts = db.execute(
        """
        SELECT p.*,
               (SELECT COUNT(*) FROM purchases WHERE prompt_id = p.id) AS total_sales,
               (SELECT COALESCE(SUM(price_paid), 0) FROM purchases WHERE prompt_id = p.id) AS total_revenue,
               (SELECT ROUND(AVG(rating), 1) FROM reviews WHERE prompt_id = p.id) AS avg_rating
        FROM prompts p
        WHERE p.creator_id = ?
        ORDER BY p.created_at DESC
        """,
        (user["id"],),
    ).fetchall()

    total_earnings = sum(p["total_revenue"] for p in my_prompts)
    total_sales = sum(p["total_sales"] for p in my_prompts)

    my_purchases = db.execute(
        """
        SELECT p.id, p.title, p.price, pu.purchased_at, u.name AS creator_name
        FROM purchases pu
        JOIN prompts p ON p.id = pu.prompt_id
        JOIN users u ON u.id = p.creator_id
        WHERE pu.buyer_id = ?
        ORDER BY pu.purchased_at DESC
        """,
        (user["id"],),
    ).fetchall()

    return render_template(
        "dashboard.html",
        prompts=my_prompts, total_earnings=total_earnings,
        total_sales=total_sales, my_purchases=my_purchases,
    )


@app.route("/dashboard/new", methods=["GET", "POST"])
def create_prompt():
    user = current_user()
    if not user:
        return login_required_redirect()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "")
        target_model = request.form.get("target_model", "")
        price_raw = request.form.get("price", "0")
        content = request.form.get("content", "").strip()

        error = None
        try:
            price = round(float(price_raw), 2)
        except ValueError:
            price = -1

        if not title or not description or not content:
            error = "Title, description, and prompt content are all required."
        elif category not in CATEGORIES:
            error = "Please choose a valid category."
        elif target_model not in TARGET_MODELS:
            error = "Please choose a valid target model."
        elif price < 0:
            error = "Price must be zero or a positive number."

        if error:
            flash(error, "error")
            return render_template("create_prompt.html", form=request.form)

        preview = (content[:160] + "…") if len(content) > 160 else content
        db = get_db()
        cur = db.execute(
            """
            INSERT INTO prompts (creator_id, title, description, category, target_model, price, content, preview)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user["id"], title, description, category, target_model, price, content, preview),
        )
        db.commit()
        flash("Your prompt is live in the marketplace!", "success")
        return redirect(url_for("prompt_detail", prompt_id=cur.lastrowid))

    return render_template("create_prompt.html", form={})


@app.route("/dashboard/edit/<int:prompt_id>", methods=["GET", "POST"])
def edit_prompt(prompt_id):
    user = current_user()
    if not user:
        return login_required_redirect()

    db = get_db()
    prompt = db.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,)).fetchone()
    if prompt is None:
        return render_template("404.html"), 404
    if prompt["creator_id"] != user["id"]:
        flash("You can only edit your own prompts.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "")
        target_model = request.form.get("target_model", "")
        price_raw = request.form.get("price", "0")
        content = request.form.get("content", "").strip()

        try:
            price = round(float(price_raw), 2)
        except ValueError:
            price = -1

        error = None
        if not title or not description or not content:
            error = "Title, description, and prompt content are all required."
        elif category not in CATEGORIES or target_model not in TARGET_MODELS or price < 0:
            error = "Please check the category, model, and price fields."

        if error:
            flash(error, "error")
            return render_template("create_prompt.html", form=request.form, editing=prompt)

        preview = (content[:160] + "…") if len(content) > 160 else content
        db.execute(
            """
            UPDATE prompts SET title=?, description=?, category=?, target_model=?, price=?, content=?, preview=?
            WHERE id=?
            """,
            (title, description, category, target_model, price, content, preview, prompt_id),
        )
        db.commit()
        flash("Prompt updated.", "success")
        return redirect(url_for("prompt_detail", prompt_id=prompt_id))

    return render_template("create_prompt.html", form=dict(prompt), editing=prompt)


@app.route("/dashboard/delete/<int:prompt_id>", methods=["POST"])
def delete_prompt(prompt_id):
    user = current_user()
    if not user:
        return login_required_redirect()

    db = get_db()
    prompt = db.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,)).fetchone()
    if prompt is None:
        return redirect(url_for("dashboard"))
    if prompt["creator_id"] != user["id"]:
        flash("You can only delete your own prompts.", "error")
        return redirect(url_for("dashboard"))

    db.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
    db.commit()
    flash("Prompt deleted.", "success")
    return redirect(url_for("dashboard"))


# ----------------------------------------------------------------------
# JSON API — used by the frontend JS for search/filter/purchase/reviews
# ----------------------------------------------------------------------
@app.route("/api/prompts")
def api_prompts():
    db = get_db()
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    target_model = request.args.get("model", "").strip()
    sort = request.args.get("sort", "popular")

    query = """
        SELECT p.id, p.title, p.description, p.category, p.target_model, p.price,
               p.sales_count, p.creator_id, p.preview, u.name AS creator_name,
               (SELECT ROUND(AVG(rating), 1) FROM reviews WHERE prompt_id = p.id) AS avg_rating,
               (SELECT COUNT(*) FROM reviews WHERE prompt_id = p.id) AS review_count
        FROM prompts p JOIN users u ON u.id = p.creator_id
        WHERE 1 = 1
    """
    params = []
    if q:
        query += " AND (p.title LIKE ? OR p.description LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    if category:
        query += " AND p.category = ?"
        params.append(category)
    if target_model:
        query += " AND p.target_model = ?"
        params.append(target_model)

    query += {
        "price_low": " ORDER BY p.price ASC",
        "price_high": " ORDER BY p.price DESC",
        "newest": " ORDER BY p.created_at DESC",
        "rating": " ORDER BY avg_rating DESC",
    }.get(sort, " ORDER BY p.sales_count DESC")

    rows = db.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/prompts/<int:prompt_id>/purchase", methods=["POST"])
def api_purchase(prompt_id):
    user = current_user()
    if not user:
        return jsonify({"error": "You must be logged in to purchase."}), 401

    db = get_db()
    prompt = db.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,)).fetchone()
    if prompt is None:
        return jsonify({"error": "Prompt not found."}), 404
    if prompt["creator_id"] == user["id"]:
        return jsonify({"error": "You can't purchase your own prompt."}), 400

    already = db.execute(
        "SELECT 1 FROM purchases WHERE buyer_id = ? AND prompt_id = ?", (user["id"], prompt_id)
    ).fetchone()
    if already:
        return jsonify({"error": "You already own this prompt."}), 400

    try:
        db.execute(
            "INSERT INTO purchases (buyer_id, prompt_id, price_paid) VALUES (?, ?, ?)",
            (user["id"], prompt_id, prompt["price"]),
        )
        db.execute("UPDATE prompts SET sales_count = sales_count + 1 WHERE id = ?", (prompt_id,))
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({"error": "You already own this prompt."}), 400

    return jsonify({"success": True, "content": prompt["content"]})


@app.route("/api/prompts/<int:prompt_id>/reviews", methods=["POST"])
def api_add_review(prompt_id):
    user = current_user()
    if not user:
        return jsonify({"error": "You must be logged in to leave a review."}), 401

    data = request.get_json(silent=True) or request.form
    try:
        rating = int(data.get("rating", 0))
    except (TypeError, ValueError):
        rating = 0
    comment = str(data.get("comment", "")).strip()

    if rating < 1 or rating > 5:
        return jsonify({"error": "Rating must be between 1 and 5."}), 400

    db = get_db()
    owns = db.execute(
        "SELECT 1 FROM purchases WHERE buyer_id = ? AND prompt_id = ?", (user["id"], prompt_id)
    ).fetchone()
    if not owns:
        return jsonify({"error": "You can only review prompts you've purchased."}), 403

    try:
        db.execute(
            "INSERT INTO reviews (prompt_id, buyer_id, rating, comment) VALUES (?, ?, ?, ?)",
            (prompt_id, user["id"], rating, comment),
        )
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({"error": "You've already reviewed this prompt."}), 400

    return jsonify({"success": True})


@app.route("/api/me")
def api_me():
    user = current_user()
    if not user:
        return jsonify({"logged_in": False})
    return jsonify({
        "logged_in": True,
        "id": user["id"], "name": user["name"],
        "role": user["role"], "email": user["email"],
    })


# ----------------------------------------------------------------------
# Error handlers
# ----------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
ensure_database_ready()

# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 5000))
#     debug = os.environ.get("FLASK_DEBUG", "1") == "1"
#     app.run(host="0.0.0.0", port=port, debug=debug)
if __name__ == "__main__":
    app.run(debug=True)