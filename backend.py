from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import csv
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ==============================
# PATHS
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
USERS_FILE = os.path.join(BASE_DIR, "users.json")
REQUESTS_FILE = os.path.join(BASE_DIR, "citizen_requests.csv")


# ==============================
# USER FUNCTIONS
# ==============================

def load_users():
    if not os.path.exists(USERS_FILE):
        return []

    with open(USERS_FILE, "r") as file:
        return json.load(file)


def save_users(users):
    with open(USERS_FILE, "w") as file:
        json.dump(users, file, indent=4)

def get_next_report_id(rows):
    ids = []

    for row in rows:
        try:
            ids.append(int(row["id"]))
        except:
            pass

    return max(ids, default=0) + 1


# ==============================
# FRONTEND
# ==============================

@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "login.html")


@app.route("/<path:filename>")
def frontend_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


# ==============================
# BACKEND STATUS
# ==============================

@app.route("/api/status")
def status():
    return jsonify({
        "status": "success",
        "message": "CivicAI Backend is running!"
    })


# ==============================
# SIGNUP API
# ==============================

@app.route("/api/signup", methods=["POST"])
def signup():

    data = request.get_json()

    if not data:
        return jsonify({
            "status": "error",
            "message": "Invalid request."
        }), 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    mobile = data.get("mobile", "").strip()
    password = data.get("password", "")

    # Check empty fields
    if not name or not email or not mobile or not password:
        return jsonify({
            "status": "error",
            "message": "All fields are required."
        }), 400

    users = load_users()

    # Check existing email
    for user in users:

        if user["email"] == email:

            return jsonify({
                "status": "error",
                "message": "An account with this email already exists."
            }), 409

    # Create new user
    new_user = {
        "name": name,
        "email": email,
        "mobile": mobile,
        "password": generate_password_hash(password)
    }

    users.append(new_user)

    save_users(users)

    return jsonify({
        "status": "success",
        "message": "Account created successfully!"
    }), 201


# ==============================
# LOGIN API
# ==============================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json()

    if not data:
        return jsonify({
            "status": "error",
            "message": "Invalid request."
        }), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # Check empty fields
    if not email or not password:
        return jsonify({
            "status": "error",
            "message": "Email and password are required."
        }), 400

    users = load_users()

    # Find user
    for user in users:

        if user["email"] == email:

            # Check password
            if check_password_hash(user["password"], password):

                return jsonify({
                    "status": "success",
                    "message": "Login successful!",
                    "name": user["name"],
                    "email": user["email"],
                    "mobile": user["mobile"]
                }), 200

            else:

                return jsonify({
                    "status": "error",
                    "message": "Incorrect password."
                }), 401

    # User not found
    return jsonify({
        "status": "error",
        "message": "Account not found. Please sign up first."
    }), 404

# ==============================
# AI ISSUE CLASSIFICATION
# ==============================

def classify_issue(problem):

    text = problem.lower()

    if any(word in text for word in [
     "pothole",
    "road",
    "street",
    "traffic",
    "footpath",
    "bridge",
    "signal",
    "road damage",
    "broken road",
    "bus stop",
    "transport",
    "parking"
    ]):
        return "Road & Transport"

    if any(word in text for word in [
        "water",
        "leakage",
        "pipeline",
        "drainage",
        "sewage",
        "flood"
    ]):
        return "Water & Sanitation"

    if any(word in text for word in [
    "garbage",
    "waste",
    "dustbin",
    "trash",
    "cleaning",
    "dump",
    "dirty area",
    "litter"
]):
        return "Waste Management"

    if any(word in text for word in [
    "light",
    "electricity",
    "electric",
    "streetlight",
    "street light",
    "power",
    "power cut",
    "transformer",
    "blackout"
]):
        return "Electricity"

    if any(word in text for word in [
    "hospital",
    "health",
    "medical",
    "clinic",
    "ambulance",
    "doctor",
    "medicine",
    "healthcare"
]):
        return "Healthcare"

    if any(word in text for word in [
    "school",
    "college",
    "education",
    "teacher",
    "classroom",
    "student"
]):
        return "Education"

    if any(word in text for word in [
    "park",
    "garden",
    "tree",
    "environment",
    "pollution",
    "air pollution",
    "noise pollution"
]):
        return "Environment"

    return "Other"


# ==============================
# AI SEVERITY ANALYSIS
# ==============================

def analyze_severity(problem):

    text = problem.lower()

    high_keywords = [
        "death",
        "accident",
        "fire",
        "flood",
        "collapse",
        "danger",
        "dangerous",
        "emergency",
        "life threatening",
        "electric shock",
        "major leakage",
        "severe damage"
    ]

    medium_keywords = [
        "broken",
        "damaged",
        "leakage",
        "overflow",
        "blocked",
        "traffic",
        "not working",
        "poor condition",
        "garbage",
        "pothole"
    ]

    if any(word in text for word in high_keywords):
        return "High"

    if any(word in text for word in medium_keywords):
        return "Medium"

    return "Low"

# ==============================
# AI PRIORITY SCORE
# ==============================

def calculate_priority(category, severity):

    # Base score from severity
    severity_scores = {
        "Low": 30,
        "Medium": 60,
        "High": 90
    }

    score = severity_scores.get(severity, 30)

    # Category-based importance
    category_bonus = {
        "Healthcare": 10,
        "Water & Sanitation": 10,
        "Electricity": 8,
        "Road & Transport": 5,
        "Waste Management": 4,
        "Environment": 4,
        "Education": 3,
        "Other": 0
    }

    score += category_bonus.get(category, 0)

    # Maximum score = 100
    return min(score, 100)

# ==============================
# CIVIC ISSUE SUBMISSION API
# ==============================

@app.route("/api/report", methods=["POST"])
def submit_report():

    data = request.get_json()

    if not data:
        return jsonify({
            "status": "error",
            "message": "Invalid request."
        }), 400

    problem = data.get("problem", "").strip()
    language = data.get("language", "").strip()
    location = data.get("location", "").strip()
    citizen_email = data.get("citizen_email", "").strip()

# Validate required fields
    if not problem or not location or not citizen_email:
        return jsonify({
        "status": "error",
        "message": "Problem, location, and citizen login are required."
    }), 400

# AI analysis
    category = classify_issue(problem)
    severity = analyze_severity(problem)
    priority_score = calculate_priority(
        category,
        severity
)

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    

    # Generate next ID
    rows = []

    if os.path.exists(REQUESTS_FILE):

        with open(
            REQUESTS_FILE,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            rows = list(csv.DictReader(file))

    next_id = get_next_report_id(rows)

    # Create CSV file with header if it doesn't exist
    file_exists = os.path.exists(REQUESTS_FILE)

    with open(
        REQUESTS_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
        "id",
        "problem",
        "language",
        "location",
        "category",
        "severity",
        "priority_score",
        "status",
        "created_at",
        "citizen_email"
    ])

        writer.writerow([
    next_id,
    problem,
    language,
    location,
    category,
    severity,
    priority_score,
    "Pending",
    created_at,
    citizen_email
])

    return jsonify({
    "status": "success",
    "message": "Civic issue submitted successfully!",
    "id": next_id,
    "category": category,
    "severity": severity,
    "location": location,
    "priority_score": priority_score
}), 201

# ==============================
# GET CIVIC REPORTS API
# ==============================

@app.route("/api/reports", methods=["GET"])
def get_reports():

    reports = []

    if os.path.exists(REQUESTS_FILE):

        with open(
            REQUESTS_FILE,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                reports.append({
                    "id": row.get("id", ""),
                    "problem": row.get("problem", ""),
                    "language": row.get("language", ""),
                    "location": row.get("location", ""),
                    "category": row.get("category", ""),
                    "severity": row.get("severity", "Low"),
                    "priority_score": row.get("priority_score", "0"),
                    "status": row.get("status") or "Pending",
                    "created_at": row.get("created_at", "")
                })

    total_reports = len(reports)

    pending = sum(
    1
    for report in reports
    if (report["status"] or "").lower() == "pending"
)

    resolved = sum(
    1
    for report in reports
    if (report["status"] or "").lower() == "resolved"
)

    in_progress = sum(
    1
    for report in reports
    if (report["status"] or "").lower() == "in progress"
)

    high_priority = sum(
    1
    for report in reports
    if int(report["priority_score"] or 0) >= 80
    )

    return jsonify({
    "status": "success",
    "total_reports": total_reports,
    "pending": pending,
    "in_progress": in_progress,
    "resolved": resolved,
    "high_priority": high_priority,
    "reports": reports[-5:][::-1]
}), 200

# ==============================
# GET MY REPORTS
# ==============================

@app.route("/api/my-reports", methods=["GET"])
def get_my_reports():

    citizen_email = request.args.get(
        "citizen_email",
        ""
    ).strip().lower()

    if not citizen_email:
        return jsonify({
            "status": "error",
            "message": "Citizen email is required."
        }), 400

    reports = []

    if os.path.exists(REQUESTS_FILE):

        with open(
            REQUESTS_FILE,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                row_email = (
                    row.get("citizen_email") or ""
                ).strip().lower()

                if row_email == citizen_email:

                    reports.append({
                        "id": row.get("id", ""),
                        "problem": row.get("problem", ""),
                        "language": row.get("language", ""),
                        "location": row.get("location", ""),
                        "category": row.get("category", ""),
                        "severity": row.get("severity") or "Low",
                        "priority_score": row.get(
                            "priority_score"
                        ) or "0",
                        "status": row.get(
                            "status"
                        ) or "Pending",
                        "created_at": row.get(
                            "created_at"
                        ) or ""
                    })

    return jsonify({
        "status": "success",
        "citizen_email": citizen_email,
        "total_reports": len(reports),
        "reports": reports[::-1]
    }), 200




# ==============================
# GET REPORTS BY CITY
# ==============================

@app.route("/api/reports/city", methods=["GET"])
def get_reports_by_city():

    city = request.args.get("city", "").strip()

    if not city:
        return jsonify({
            "status": "error",
            "message": "City name is required."
        }), 400

    reports = []

    if os.path.exists(REQUESTS_FILE):

        with open(
            REQUESTS_FILE,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                location = row.get("location", "").strip()

                # Case-insensitive city matching
                if location.lower() == city.lower():

                    reports.append({
                        "id": row.get("id", ""),
                        "problem": row.get("problem", ""),
                        "language": row.get("language", ""),
                        "location": location,
                        "category": row.get("category", ""),
                        "severity": row.get("severity", "Low"),
                        "priority_score": row.get("priority_score", "0"),
                        "status": row.get("status") or "Pending"
                    })


    # ==============================
    # CITY INTELLIGENCE
    # ==============================

    total_reports = len(reports)

    high_priority = sum(
    1
    for report in reports
    if int(report["priority_score"] or 0) >= 80
)
    pending = sum(
    1
    for report in reports
    if (report["status"] or "").lower() == "pending"
)

    resolved = sum(
    1
    for report in reports
    if (report["status"] or "").lower() == "resolved"
)

    in_progress = sum(
    1
    for report in reports
    if (report["status"] or "").lower() == "in progress"
)


    # Find most common civic category

    category_counts = {}

    for report in reports:

        category = report["category"]

        if category:
            category_counts[category] = \
                category_counts.get(category, 0) + 1


    if category_counts:

        top_category = max(
            category_counts,
            key=category_counts.get
        )

    else:

        top_category = "No data"


    return jsonify({

        "status": "success",

        "city": city,

        "total_reports": total_reports,

        "high_priority": high_priority,

        "pending": pending,

        "in_progress": in_progress,

        "resolved": resolved,

        "top_category": top_category,

        "reports": reports[::-1]

    }), 200

# ==============================
# TRACK CIVIC REQUEST
# ==============================

@app.route("/api/report/<report_id>", methods=["GET"])
def track_report(report_id):

    if not os.path.exists(REQUESTS_FILE):
        return jsonify({
            "status": "error",
            "message": "No civic reports found."
        }), 404

    with open(
        REQUESTS_FILE,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            if row.get("id", "") == str(report_id):

                return jsonify({
                    "status": "success",
                    "report": {
                        "id": row.get("id", ""),
                        "problem": row.get("problem", ""),
                        "language": row.get("language", ""),
                        "location": row.get("location", ""),
                        "category": row.get("category", ""),
                        "severity": row.get("severity", "Low"),
                        "priority_score": row.get(
                            "priority_score",
                            "0"
                        ),
                        "status": row.get(
                            "status",
                            "Pending"
                        ),
                        "created_at": row.get(
                            "created_at",
                            ""
                            )
                                                
                        }
                }), 200

    return jsonify({
        "status": "error",
        "message": "Report ID not found."
    }), 404

# ==============================
# RUN SERVER
# ==============================

if __name__ == "__main__":

    print("=" * 50)
    print("CivicAI Server Started")
    print("=" * 50)
    print("Frontend : http://127.0.0.1:5000")
    print("Signup   : http://127.0.0.1:5000/signup.html")
    print("Login    : http://127.0.0.1:5000/login.html")
    print("Dashboard: http://127.0.0.1:5000/dashboard.html")
    print("=" * 50)

    app.run(
        host="127.0.0.1",
        port=5000,
        debug= False
    )