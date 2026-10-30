"""
app/predict.py
==============
Purpose: Load trained ML models, execute inference on student inputs, generate improvement tips, and log predictions.
Author: Student Project (Explainable Machine Learning with MongoDB)

This module handles:
1. Loading the persisted scikit-learn models and scalers from models/.
2. Encoding categorical branch and scaling features identically to training.
3. Predicting placement (0 or 1) and calculating confidence probability (%).
4. Estimating salary package (LPA) ONLY for students predicted as placed.
5. Generating transparent, rule-based improvement tips (derived from deterministic if/else checks, not the ML model).
6. Persisting every prediction in MongoDB for the student's history and admin reporting.
"""

import os
from datetime import datetime, timezone
from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    session,
    redirect,
    url_for
)
import joblib
import numpy as np

from app.config import MODELS_DIR
from app.db import get_predictions_collection
from app.auth import login_required
from app.validators import validate_prediction_inputs

# Blueprint for prediction routes
predict_bp = Blueprint("predict", __name__)

# Cache for loaded models and preprocessing artifacts
_loaded_artifacts = None


def load_ml_artifacts():
    """
    Load persisted models and transformers from disk.

    Returns:
        dict: Dictionary containing best_classifier, best_regressor, scaler, regression_scaler, branch_encoder.
    """
    global _loaded_artifacts
    if _loaded_artifacts is None:
        clf_path = os.path.join(MODELS_DIR, "best_classifier.joblib")
        reg_path = os.path.join(MODELS_DIR, "best_regressor.joblib")
        scaler_path = os.path.join(MODELS_DIR, "scaler.joblib")
        reg_scaler_path = os.path.join(MODELS_DIR, "regression_scaler.joblib")
        encoder_path = os.path.join(MODELS_DIR, "branch_encoder.joblib")

        # Verify that models exist
        if not (os.path.exists(clf_path) and os.path.exists(reg_path) and os.path.exists(scaler_path)):
            raise FileNotFoundError(
                f"Model files not found in '{MODELS_DIR}'. "
                "Please run 'python src/train_models.py' or 'python src/main.py' first."
            )

        _loaded_artifacts = {
            "classifier": joblib.load(clf_path),
            "regressor": joblib.load(reg_path),
            "scaler": joblib.load(scaler_path),
            "reg_scaler": joblib.load(reg_scaler_path),
            "encoder": joblib.load(encoder_path)
        }
        print("[predict.py] ML models and preprocessing transformers loaded successfully.")

    return _loaded_artifacts


def generate_rule_based_tips(inputs):
    """
    Generate actionable advice based on simple, explainable if/else business rules.

    Parameters:
        inputs (dict): Raw input features submitted by the student.

    Returns:
        list of str: 2-3 prioritized recommendations.
    """
    tips = []

    # Rule 1: Backlogs are the #1 barrier to corporate placement eligibility
    if inputs.get("backlogs", 0) > 0:
        tips.append("Clear all active backlogs as top priority; most tier-1 companies enforce a strict zero-backlog eligibility criterion.")

    # Rule 2: Coding proficiency
    if inputs.get("coding_score", 0) < 70.0:
        tips.append("Raise your coding score above 70 by practicing Data Structures & Algorithms regularly on LeetCode or HackerRank.")

    # Rule 3: Practical industry internship experience
    if inputs.get("internships", 0) == 0:
        tips.append("Complete at least one industry internship to gain hands-on production experience before campus recruitment.")

    # Rule 4: Project portfolio
    if inputs.get("projects", 0) < 2:
        tips.append("Build at least 2 full-stack or domain-specific projects to showcase in your technical portfolio and GitHub.")

    # Rule 5: Communication and interview etiquette
    if inputs.get("communication_score", 0) < 65.0:
        tips.append("Enhance verbal communication and technical storytelling by participating in mock interviews and group discussions.")

    # Rule 6: If already high across all indicators
    if len(tips) == 0:
        tips.append("Strong academic and technical profile! Focus on advanced system design topics and behavioral interview preparation.")
        tips.append("Maintain your CGPA and keep your problem-solving momentum sharp.")

    # Limit to top 3 most urgent tips
    return tips[:3]


def predict_placement_and_salary(inputs):
    """
    Execute prediction for placement status and expected salary package.

    Parameters:
        inputs (dict): Cleaned dictionary of student attributes.

    Returns:
        tuple: (placed: int, probability: float, salary_lpa: float or None, tips: list)
    """
    artifacts = load_ml_artifacts()
    clf = artifacts["classifier"]
    reg = artifacts["regressor"]
    scaler = artifacts["scaler"]
    reg_scaler = artifacts["reg_scaler"]
    encoder = artifacts["encoder"]

    # 1. Encode categorical branch identically to preprocessing.py
    # If an unseen branch is encountered, handle gracefully
    try:
        branch_encoded = int(encoder.transform([inputs["branch"]])[0])
    except Exception:
        branch_encoded = 0

    # 2. Arrange features in EXACT order matching training:
    # ["cgpa", "10th_percent", "12th_percent", "internships", "projects",
    #  "certifications", "coding_score", "communication_score", "backlogs", "branch_encoded"]
    feature_vector = np.array([[
        inputs["cgpa"],
        inputs["10th_percent"],
        inputs["12th_percent"],
        inputs["internships"],
        inputs["projects"],
        inputs["certifications"],
        inputs["coding_score"],
        inputs["communication_score"],
        inputs["backlogs"],
        branch_encoded
    ]], dtype=float)

    # 3. Scale features using the fitted classification scaler
    features_scaled = scaler.transform(feature_vector)

    # 4. Predict Placement Status (0 or 1)
    placed_prediction = int(clf.predict(features_scaled)[0])

    # 5. Compute Confidence Probability (%)
    if hasattr(clf, "predict_proba"):
        probability = round(float(clf.predict_proba(features_scaled)[0][1]) * 100.0, 1)
    else:
        # Fallback for models without predict_proba
        probability = 90.0 if placed_prediction == 1 else 10.0

    # 6. Predict Salary in LPA ONLY if candidate is predicted as placed
    # WHY: Unplaced students receive no corporate offer; predicting a package
    # for an unplaced candidate is illogical in a campus placement context.
    salary_lpa = None
    if placed_prediction == 1:
        reg_features_scaled = reg_scaler.transform(feature_vector)
        raw_salary = float(reg.predict(reg_features_scaled)[0])
        # Clip to realistic college placement bounds (3.2 LPA to 24.0 LPA)
        salary_lpa = round(float(np.clip(raw_salary, 3.2, 24.0)), 2)

    # 7. Generate rule-based recommendations
    tips = generate_rule_based_tips(inputs)

    return placed_prediction, probability, salary_lpa, tips


@predict_bp.route("/predict", methods=["GET", "POST"])
@login_required
def predict_page():
    """
    Render student prediction input form and handle prediction submission.
    """
    if request.method == "POST":
        # 1. Validate and sanitize inputs on server
        is_valid, error_msg, cleaned_inputs = validate_prediction_inputs(request.form)
        if not is_valid:
            flash(error_msg, "danger")
            return render_template("predict.html", form_data=request.form)

        # 2. Execute Machine Learning inference
        try:
            placed, prob, salary, tips = predict_placement_and_salary(cleaned_inputs)
        except Exception as e:
            flash(f"Inference error: {str(e)}", "danger")
            return render_template("predict.html", form_data=request.form)

        # 3. Store prediction document into MongoDB collection 'predictions'
        preds_col = get_predictions_collection()
        if preds_col is not None:
            prediction_record = {
                "user_id": session.get("user_id"),
                "user_email": session.get("user_email"),
                "inputs": cleaned_inputs,
                "placed": placed,
                "probability": prob,
                "salary_lpa": salary,
                "created_at": datetime.now(timezone.utc)
            }
            preds_col.insert_one(prediction_record)
            print(f"[PREDICT] Saved prediction for {session.get('user_email')}: Placed={placed}, Prob={prob}%, Salary={salary} LPA")

        # 4. Render result presentation card
        return render_template(
            "result.html",
            placed=placed,
            probability=prob,
            salary_lpa=salary,
            tips=tips,
            inputs=cleaned_inputs
        )

    return render_template("predict.html", form_data={})
