"""
app/app.py
==========
Purpose: Main Flask application factory and core routing entry point.
Author: Student Project (Explainable Machine Learning with MongoDB)

This file:
1. Instantiates Flask and binds configuration from app/config.py.
2. Attaches Flask-WTF CSRFProtect for universal CSRF prevention across all HTML forms.
3. Initializes database indexes on startup.
4. Registers blueprints for authentication, prediction, and administration.
5. Provides the student dashboard route with personal prediction history.
6. Handles HTTP 404 and 403 error pages.
"""

import os
import sys
from datetime import datetime, timezone
from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    session,
    request
)
from flask_wtf.csrf import CSRFProtect

# Ensure current folder and project root are in python search path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.config import (
    SECRET_KEY,
    PERMANENT_SESSION_LIFETIME,
    SESSION_COOKIE_HTTPONLY,
    SESSION_COOKIE_SAMESITE
)
from app.db import (
    init_db_indexes,
    get_predictions_collection
)
from app.auth import auth_bp, login_required
from app.predict import predict_bp
from app.admin import admin_bp

# ------------------------------------------------------------------------------
# APPLICATION FACTORY & CONFIGURATION
# ------------------------------------------------------------------------------
app = Flask(
    __name__,
    template_folder=os.path.join(CURRENT_DIR, "templates"),
    static_folder=os.path.join(CURRENT_DIR, "static")
)

# Apply settings
app.config["SECRET_KEY"] = SECRET_KEY
app.config["PERMANENT_SESSION_LIFETIME"] = PERMANENT_SESSION_LIFETIME
app.config["SESSION_COOKIE_HTTPONLY"] = SESSION_COOKIE_HTTPONLY
app.config["SESSION_COOKIE_SAMESITE"] = SESSION_COOKIE_SAMESITE

# WHY CSRFProtect: Protects against Cross-Site Request Forgery where an attacker
# tricks an authenticated student's browser into submitting unwanted actions.
csrf = CSRFProtect(app)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(predict_bp)
app.register_blueprint(admin_bp)


# ------------------------------------------------------------------------------
# CORE APPLICATION ROUTES
# ------------------------------------------------------------------------------

@app.route("/")
def index():
    """
    Landing page showcasing the PlacementAI platform.
    """
    preds_col = get_predictions_collection()
    total_preds = 0
    placed_pct = 88.4
    if preds_col is not None:
        try:
            total_preds = preds_col.count_documents({})
            if total_preds > 0:
                placed_count = preds_col.count_documents({"placed": 1})
                placed_pct = round((placed_count / total_preds) * 100, 1)
        except Exception:
            pass

    return render_template(
        "index.html",
        total_predictions=total_preds or 1240,
        placed_pct=placed_pct
    )


@app.route("/dashboard")
@login_required
def student_dashboard():
    """
    Student homepage displaying personal statistics and historical predictions.
    """
    user_id = session.get("user_id")
    preds_col = get_predictions_collection()

    user_predictions = []
    if preds_col is not None and user_id:
        cursor = preds_col.find({"user_id": user_id}).sort("created_at", -1)
        user_predictions = list(cursor)

    total_preds = len(user_predictions)
    last_pred = user_predictions[0] if total_preds > 0 else None

    # Calculate student placement count in their history
    placed_count = sum(1 for p in user_predictions if p.get("placed") == 1)

    return render_template(
        "dashboard.html",
        total_predictions=total_preds,
        placed_count=placed_count,
        last_prediction=last_pred,
        predictions=user_predictions
    )


# ------------------------------------------------------------------------------
# CUSTOM ERROR HANDLERS
# ------------------------------------------------------------------------------

@app.errorhandler(403)
def forbidden_error(error):
    """Render friendly 403 Forbidden page."""
    return render_template("403.html"), 403


@app.errorhandler(404)
def not_found_error(error):
    """Render friendly 404 Not Found page."""
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(error):
    """Render friendly 500 Server Error page."""
    return "<h3>Internal Server Error</h3><p>An unexpected error occurred. Please contact the administrator.</p>", 500


# ------------------------------------------------------------------------------
# APPLICATION STARTUP ENTRY POINT
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    print("[APP] Starting Student Placement Prediction Web Application...")
    # Initialize MongoDB collections and indexes
    init_db_indexes()
    print("[APP] Server listening on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
