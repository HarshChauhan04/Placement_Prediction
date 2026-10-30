"""
app/admin.py
============
Purpose: Administrative dashboard controller displaying system analytics, user accounts, and model metrics.
Author: Student Project (Explainable Machine Learning with MongoDB)

ACCESS POLICY:
Strictly restricted to users with role == 'admin' via the @admin_required decorator.
Regular students attempting to visit /admin receive HTTP 403 Forbidden.
"""

import os
import json
from flask import (
    Blueprint,
    render_template,
    send_from_directory,
    abort
)
from app.config import (
    METRICS_JSON_PATH,
    CHARTS_DIR
)
from app.db import (
    get_users_collection,
    get_predictions_collection
)
from app.auth import admin_required

admin_bp = Blueprint("admin", __name__)


def load_model_metrics():
    """
    Read model evaluation metrics directly from outputs/metrics.json.
    NEVER invent or hardcode metric values.

    Returns:
        dict: Parsed metrics dictionary, or empty dict if file not found.
    """
    if os.path.exists(METRICS_JSON_PATH):
        try:
            with open(METRICS_JSON_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[admin.py] Error reading metrics.json: {e}")
    return {}


@admin_bp.route("/admin")
@admin_required
def admin_dashboard():
    """
    Render administrator control panel with platform analytics and model metrics.
    """
    users_col = get_users_collection()
    preds_col = get_predictions_collection()

    # 1. Platform Statistics
    total_users = users_col.count_documents({}) if users_col is not None else 0
    total_predictions = preds_col.count_documents({}) if preds_col is not None else 0
    placed_count = preds_col.count_documents({"placed": 1}) if preds_col is not None else 0

    if total_predictions > 0:
        placed_pct = round((placed_count / total_predictions) * 100.0, 1)
    else:
        placed_pct = 0.0

    not_placed_count = total_predictions - placed_count

    # 2. Aggregation: Predictions grouped by student branch
    branch_labels = ["Computer Science", "Information Technology", "Electronics", "Mechanical", "Civil"]
    branch_counts = {b: 0 for b in branch_labels}

    if preds_col is not None:
        pipeline = [
            {"$group": {"_id": "$inputs.branch", "count": {"$sum": 1}}}
        ]
        for item in preds_col.aggregate(pipeline):
            branch_name = item.get("_id")
            if branch_name in branch_counts:
                branch_counts[branch_name] = item.get("count", 0)

    # 3. Read official ML metrics from disk
    model_metrics = load_model_metrics()

    # 4. Fetch list of registered users (NEVER retrieve or expose password_hash)
    users_list = []
    if users_col is not None:
        cursor = users_col.find({}, {"password_hash": 0}).sort("created_at", -1)
        users_list = list(cursor)

    return render_template(
        "admin.html",
        total_users=total_users,
        total_predictions=total_predictions,
        placed_count=placed_count,
        not_placed_count=not_placed_count,
        placed_pct=placed_pct,
        branch_labels=list(branch_counts.keys()),
        branch_data=list(branch_counts.values()),
        model_metrics=model_metrics,
        users=users_list
    )


@admin_bp.route("/admin/charts/<filename>")
@admin_required
def serve_chart_image(filename):
    """
    Safely serve generated confusion matrix and regression charts from outputs/charts/.

    Parameters:
        filename (str): Name of the chart PNG file.
    """
    # Prevent directory traversal attacks by whitelisting valid chart files
    allowed_files = {
        "confusion_matrix_logistic_regression.png",
        "confusion_matrix_random_forest.png",
        "actual_vs_predicted_regression.png"
    }

    if filename not in allowed_files:
        abort(404)

    return send_from_directory(CHARTS_DIR, filename)
