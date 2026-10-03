"""
AI-Based Smart Parking Management System
Flask Backend Application
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import os
from model import ParkingMLSystem
import json

app = Flask(__name__)
app.secret_key = "smart_parking_secret_key_2024"

# ─── Database Setup ────────────────────────────────────────────────────────────
DB_PATH = "database.db"

def get_db():
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables and seed data."""
    conn = get_db()
    cur = conn.cursor()

    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Parking slots table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS parking_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_number TEXT UNIQUE NOT NULL,
            area TEXT NOT NULL,
            status TEXT DEFAULT 'available',
            booked_by TEXT,
            booked_at TIMESTAMP
        )
    """)

    # Predictions log table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predictions_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            time_hour INTEGER,
            day INTEGER,
            num_cars INTEGER,
            traffic_level INTEGER,
            lr_result TEXT,
            rf_result TEXT,
            cluster_area TEXT,
            forecast TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed default admin
    cur.execute("SELECT * FROM users WHERE username='admin'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", "admin123", "admin")
        )

    # Seed parking slots (30 slots across 3 areas)
    cur.execute("SELECT COUNT(*) FROM parking_slots")
    if cur.fetchone()[0] == 0:
        areas = ["A", "B", "C"]
        statuses = ["available", "available", "occupied", "available", "moderate",
                    "occupied", "available", "available", "moderate", "occupied"]
        for area in areas:
            for i in range(1, 11):
                slot_num = f"{area}{i:02d}"
                status = statuses[(i - 1) % len(statuses)]
                cur.execute(
                    "INSERT INTO parking_slots (slot_number, area, status) VALUES (?, ?, ?)",
                    (slot_num, area, status)
                )

    conn.commit()
    conn.close()

# ─── Initialize ML System ──────────────────────────────────────────────────────
ml_system = ParkingMLSystem()
ml_system.train_all_models()

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Redirect to login page."""
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login."""
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("user_dashboard"))
        else:
            error = "Invalid username or password."

    return render_template("login.html", error=error)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Handle new user registration."""
    error = None
    success = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        confirm  = request.form.get("confirm_password", "").strip()

        if not username or not password:
            error = "Username and password are required."
        elif password != confirm:
            error = "Passwords do not match."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        else:
            try:
                conn = get_db()
                conn.execute(
                    "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    (username, password, "user")
                )
                conn.commit()
                conn.close()
                success = "Registration successful! Please login."
            except sqlite3.IntegrityError:
                error = "Username already exists."

    return render_template("register.html", error=error, success=success)


@app.route("/user")
def user_dashboard():
    """User dashboard – requires login."""
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    slots = conn.execute("SELECT * FROM parking_slots ORDER BY area, slot_number").fetchall()
    conn.close()

    stats = {
        "total": len(slots),
        "available": sum(1 for s in slots if s["status"] == "available"),
        "occupied":  sum(1 for s in slots if s["status"] == "occupied"),
        "moderate":  sum(1 for s in slots if s["status"] == "moderate"),
    }
    return render_template("user_dashboard.html",
                           username=session["username"],
                           slots=slots,
                           stats=stats)


@app.route("/admin")
def admin_dashboard():
    """Admin dashboard – requires admin role."""
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db()
    slots  = conn.execute("SELECT * FROM parking_slots").fetchall()
    users  = conn.execute("SELECT * FROM users WHERE role='user'").fetchall()
    logs   = conn.execute(
        "SELECT * FROM predictions_log ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    conn.close()

    stats = {
        "total":     len(slots),
        "available": sum(1 for s in slots if s["status"] == "available"),
        "occupied":  sum(1 for s in slots if s["status"] == "occupied"),
        "moderate":  sum(1 for s in slots if s["status"] == "moderate"),
        "users":     len(users),
    }

    # Area-wise data for charts
    area_data = {}
    for slot in slots:
        a = slot["area"]
        if a not in area_data:
            area_data[a] = {"available": 0, "occupied": 0, "moderate": 0}
        area_data[a][slot["status"]] += 1

    return render_template("admin_dashboard.html",
                           stats=stats,
                           area_data=json.dumps(area_data),
                           logs=logs,
                           users=users)


@app.route("/predict", methods=["POST"])
def predict():
    """Run all ML models and return combined prediction result."""
    if "user_id" not in session:
        return redirect(url_for("login"))

    time_hour     = int(request.form.get("time_hour", 12))
    day           = int(request.form.get("day", 0))
    num_cars      = int(request.form.get("num_cars", 30))
    traffic_level = int(request.form.get("traffic_level", 1))

    # Run ML predictions
    result = ml_system.predict_all(time_hour, day, num_cars, traffic_level)

    # Log prediction to DB
    conn = get_db()
    conn.execute("""
        INSERT INTO predictions_log
            (user_id, time_hour, day, num_cars, traffic_level,
             lr_result, rf_result, cluster_area, forecast)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session["user_id"], time_hour, day, num_cars, traffic_level,
        result["lr_status"], result["rf_status"],
        result["recommended_area"],
        json.dumps(result["forecast"])
    ))
    conn.commit()
    conn.close()

    return render_template("result.html",
                           result=result,
                           inputs={
                               "time_hour": time_hour,
                               "day": day,
                               "num_cars": num_cars,
                               "traffic_level": traffic_level
                           })


@app.route("/api/slots")
def api_slots():
    """API endpoint: return live slot data as JSON."""
    conn = get_db()
    slots = conn.execute("SELECT * FROM parking_slots ORDER BY area, slot_number").fetchall()
    conn.close()
    return jsonify([dict(s) for s in slots])


@app.route("/api/book", methods=["POST"])
def api_book():
    """API endpoint: book a specific parking slot."""
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data       = request.get_json()
    slot_num   = data.get("slot_number")
    username   = session["username"]

    conn = get_db()
    slot = conn.execute(
        "SELECT * FROM parking_slots WHERE slot_number=?", (slot_num,)
    ).fetchone()

    if not slot:
        conn.close()
        return jsonify({"error": "Slot not found"}), 404
    if slot["status"] == "occupied":
        conn.close()
        return jsonify({"error": "Slot already occupied"}), 400

    conn.execute(
        "UPDATE parking_slots SET status='occupied', booked_by=?, booked_at=CURRENT_TIMESTAMP WHERE slot_number=?",
        (username, slot_num)
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Slot {slot_num} booked successfully!"})


@app.route("/api/release", methods=["POST"])
def api_release():
    """API endpoint: release / free a parking slot."""
    if session.get("role") != "admin":
        return jsonify({"error": "Admin only"}), 403
    data     = request.get_json()
    slot_num = data.get("slot_number")
    conn     = get_db()
    conn.execute(
        "UPDATE parking_slots SET status='available', booked_by=NULL, booked_at=NULL WHERE slot_number=?",
        (slot_num,)
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/logout")
def logout():
    """Clear session and redirect to login."""
    session.clear()
    return redirect(url_for("login"))


# ─── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("\n✅ Smart Parking System is running!")
    print("   Open: http://127.0.0.1:5000")
    print("   Admin login → username: admin | password: admin123\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
