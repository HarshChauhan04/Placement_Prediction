"""
train_models.py
===============
Purpose: Train, evaluate, and visualize classification and regression models.
Author: Student Project (Explainable Machine Learning with MongoDB)

This script performs:
1. Classification:
   - Logistic Regression (interpretable linear baseline using sigmoid activation).
   - Random Forest Classifier (ensemble of decision trees capturing non-linear interactions).
   - Evaluation metrics: Accuracy, Precision, Recall, and F1-Score.
   - Plots and saves Confusion Matrix heatmaps.
2. Regression (for placed students only):
   - Linear Regression (interpretable baseline for salary continuous prediction).
   - Random Forest Regressor (ensemble regression capturing salary tier plateaus).
   - Evaluation metrics: R² (variance explained) and MAE (Mean Absolute Error in LPA).
   - Plots and saves Actual vs. Predicted scatter plots.
3. Persisting all numerical metrics into outputs/metrics.json.
"""

import json
import os
import joblib
import matplotlib.pyplot as plt
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    precision_score,
    r2_score,
    recall_score,
)

# ==============================================================================
# NAMED CONSTANTS (No magic numbers)
# ==============================================================================
RANDOM_STATE = 42          # Ensures repeatable model training results
MAX_ITER = 1000            # Ample iterations for Logistic Regression convergence
N_ESTIMATORS = 100         # Standard 100 decision trees in Random Forest ensemble

# Output paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
CHARTS_DIR = os.path.join(OUTPUTS_DIR, "charts")
METRICS_JSON_PATH = os.path.join(OUTPUTS_DIR, "metrics.json")
MODELS_DIR = os.path.join(BASE_DIR, "models")


def plot_confusion_matrix(cm, model_name, save_path):
    """
    Generate and save a clear confusion matrix chart using matplotlib.

    Parameters:
        cm (np.ndarray): 2x2 confusion matrix array [[TN, FP], [FN, TP]].
        model_name (str): Name of the model for the title.
        save_path (str): Filepath where the chart image will be saved.
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.figure(figsize=(6, 5))
    plt.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    plt.title(f"Confusion Matrix: {model_name}", fontsize=13, fontweight="bold", pad=12)
    plt.colorbar()

    class_labels = ["Not Placed (0)", "Placed (1)"]
    tick_marks = np.arange(len(class_labels))
    plt.xticks(tick_marks, class_labels, fontsize=10)
    plt.yticks(tick_marks, class_labels, fontsize=10)

    # Annotate counts inside the matrix squares
    threshold = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            cell_text = f"{cm[i, j]}"
            text_color = "white" if cm[i, j] > threshold else "black"
            plt.text(j, i, cell_text, horizontalalignment="center",
                     verticalalignment="center", color=text_color,
                     fontsize=14, fontweight="bold")

    plt.ylabel("True Actual Label", fontsize=11)
    plt.xlabel("Model Predicted Label", fontsize=11)
    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close()
    print(f"[train_models.py] Saved confusion matrix chart to: {save_path}")


def plot_actual_vs_predicted(y_actual, y_pred_linear, y_pred_rf, save_path):
    """
    Plot actual vs predicted LPA salary scatter plot for both regression models.

    Parameters:
        y_actual (np.ndarray): Actual test salary packages in LPA.
        y_pred_linear (np.ndarray): Linear Regression predicted salary packages.
        y_pred_rf (np.ndarray): Random Forest predicted salary packages.
        save_path (str): Filepath to save the plot.
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.figure(figsize=(8, 6))

    # Scatter points for Linear Regression
    plt.scatter(y_actual, y_pred_linear, color="#1f77b4", alpha=0.6, edgecolors="none",
                label="Linear Regression", s=45)

    # Scatter points for Random Forest Regressor
    plt.scatter(y_actual, y_pred_rf, color="#2ca02c", alpha=0.6, edgecolors="none",
                marker="^", label="Random Forest Regressor", s=45)

    # Ideal 45-degree reference line (where Actual == Predicted)
    min_val = min(y_actual.min(), y_pred_linear.min(), y_pred_rf.min())
    max_val = max(y_actual.max(), y_pred_linear.max(), y_pred_rf.max())
    plt.plot([min_val, max_val], [min_val, max_val], color="red", linestyle="--",
             linewidth=2, label="Ideal Prediction (y = x)")

    plt.title("Actual vs. Predicted Salary Packages (LPA)", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Actual Salary (LPA)", fontsize=11)
    plt.ylabel("Predicted Salary (LPA)", fontsize=11)
    plt.legend(loc="upper left", fontsize=10)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close()
    print(f"[train_models.py] Saved actual vs predicted regression chart to: {save_path}")


def train_classification_models(X_train, X_test, y_train, y_test):
    """
    Train and evaluate Logistic Regression and Random Forest classifiers.

    Parameters:
        X_train, X_test: Scaled feature sets for training and testing.
        y_train, y_test: Ground truth binary placement labels.

    Returns:
        dict: Evaluation metrics and trained model objects.
    """
    # --------------------------------------------------------------------------
    # MODEL 1: LOGISTIC REGRESSION
    # WHY: Logistic Regression is the standard, highly interpretable baseline
    # for binary classification. It passes a weighted linear sum through a
    # sigmoid function to estimate class probabilities.
    # --------------------------------------------------------------------------
    log_reg = LogisticRegression(max_iter=MAX_ITER, random_state=RANDOM_STATE)
    log_reg.fit(X_train, y_train)
    y_pred_log = log_reg.predict(X_test)

    # Compute classification metrics
    # Accuracy: Overall proportion of correct predictions
    acc_log = round(float(accuracy_score(y_test, y_pred_log)), 4)
    # Precision: When model predicts placed, how often is it right?
    prec_log = round(float(precision_score(y_test, y_pred_log)), 4)
    # Recall: Out of all actually placed students, how many were correctly detected?
    rec_log = round(float(recall_score(y_test, y_pred_log)), 4)
    # F1-Score: Harmonic mean balancing Precision and Recall
    f1_log = round(float(f1_score(y_test, y_pred_log)), 4)
    cm_log = confusion_matrix(y_test, y_pred_log)

    # --------------------------------------------------------------------------
    # MODEL 2: RANDOM FOREST CLASSIFIER
    # WHY: Random Forest builds an ensemble of multiple decision trees using
    # bagging (bootstrap aggregation). It captures non-linear relationships,
    # prevents overfitting, and generally offers higher accuracy on tabular data.
    # --------------------------------------------------------------------------
    rf_clf = RandomForestClassifier(n_estimators=N_ESTIMATORS, random_state=RANDOM_STATE)
    rf_clf.fit(X_train, y_train)
    y_pred_rf = rf_clf.predict(X_test)

    acc_rf = round(float(accuracy_score(y_test, y_pred_rf)), 4)
    prec_rf = round(float(precision_score(y_test, y_pred_rf)), 4)
    rec_rf = round(float(recall_score(y_test, y_pred_rf)), 4)
    f1_rf = round(float(f1_score(y_test, y_pred_rf)), 4)
    cm_rf = confusion_matrix(y_test, y_pred_rf)

    # Save confusion matrix charts
    cm_log_path = os.path.join(CHARTS_DIR, "confusion_matrix_logistic_regression.png")
    cm_rf_path = os.path.join(CHARTS_DIR, "confusion_matrix_random_forest.png")
    plot_confusion_matrix(cm_log, "Logistic Regression", cm_log_path)
    plot_confusion_matrix(cm_rf, "Random Forest Classifier", cm_rf_path)

    metrics = {
        "Logistic_Regression": {
            "Accuracy": acc_log,
            "Precision": prec_log,
            "Recall": rec_log,
            "F1_Score": f1_log,
            "Confusion_Matrix": cm_log.tolist(),
            "Chart_File": "confusion_matrix_logistic_regression.png"
        },
        "Random_Forest_Classifier": {
            "Accuracy": acc_rf,
            "Precision": prec_rf,
            "Recall": rec_rf,
            "F1_Score": f1_rf,
            "Confusion_Matrix": cm_rf.tolist(),
            "Chart_File": "confusion_matrix_random_forest.png"
        }
    }

    return metrics, log_reg, rf_clf


def train_regression_models(X_train, X_test, y_train, y_test):
    """
    Train and evaluate Linear Regression and Random Forest Regressor on placed students.

    Parameters:
        X_train, X_test: Scaled feature sets for placed students.
        y_train, y_test: Ground truth salary packages in LPA.

    Returns:
        dict: Evaluation metrics and trained model objects.
    """
    # --------------------------------------------------------------------------
    # MODEL 1: LINEAR REGRESSION
    # WHY: Linear Regression is the transparent parametric baseline. It finds
    # the best-fitting hyperplane that minimizes the sum of squared residuals.
    # --------------------------------------------------------------------------
    lin_reg = LinearRegression()
    lin_reg.fit(X_train, y_train)
    y_pred_lin = lin_reg.predict(X_test)

    # WHY R² AND MAE:
    # R² (Coefficient of Determination) measures the proportion of variance in salary
    # explained by candidate skills (1.0 = perfect prediction).
    # MAE (Mean Absolute Error) is in natural units (LPA), directly telling us the
    # average prediction error (e.g., predicted package is off by ~0.8 LPA on average).
    r2_lin = round(float(r2_score(y_test, y_pred_lin)), 4)
    mae_lin = round(float(mean_absolute_error(y_test, y_pred_lin)), 4)

    # --------------------------------------------------------------------------
    # MODEL 2: RANDOM FOREST REGRESSOR
    # WHY: Random Forest Regressor averages predictions from multiple decision
    # trees. It easily captures non-linear patterns, such as bonus tiers for
    # exceptional coders, which a straight linear line cannot fully capture.
    # --------------------------------------------------------------------------
    rf_reg = RandomForestRegressor(n_estimators=N_ESTIMATORS, random_state=RANDOM_STATE)
    rf_reg.fit(X_train, y_train)
    y_pred_rf = rf_reg.predict(X_test)

    r2_rf = round(float(r2_score(y_test, y_pred_rf)), 4)
    mae_rf = round(float(mean_absolute_error(y_test, y_pred_rf)), 4)

    # Save actual vs predicted regression scatter chart
    reg_chart_path = os.path.join(CHARTS_DIR, "actual_vs_predicted_regression.png")
    plot_actual_vs_predicted(y_test, y_pred_lin, y_pred_rf, reg_chart_path)

    metrics = {
        "Linear_Regression": {
            "R2_Score": r2_lin,
            "MAE_LPA": mae_lin,
            "Chart_File": "actual_vs_predicted_regression.png"
        },
        "Random_Forest_Regressor": {
            "R2_Score": r2_rf,
            "MAE_LPA": mae_rf,
            "Chart_File": "actual_vs_predicted_regression.png"
        }
    }

    return metrics, lin_reg, rf_reg


def save_metrics_to_json(metrics_dict, file_path=METRICS_JSON_PATH):
    """
    Save the complete dictionary of classification and regression metrics to a JSON file.

    Parameters:
        metrics_dict (dict): Dictionary of all evaluated metrics.
        file_path (str): Destination path for the metrics file.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(metrics_dict, f, indent=4)
    print(f"[train_models.py] Successfully saved metrics summary to: {file_path}")


def run_model_training(processed_data):
    """
    Execute full training workflow for classification and regression.

    Parameters:
        processed_data (dict): Output from preprocessing_pipeline().

    Returns:
        dict: Complete dictionary containing all classification and regression metrics.
    """
    print("[train_models.py] Step 1: Training Classification Models (Placement Prediction)...")
    class_data = processed_data["classification"]
    class_metrics, log_reg, rf_clf = train_classification_models(
        class_data["X_train"], class_data["X_test"],
        class_data["y_train"], class_data["y_test"]
    )

    print("[train_models.py] Step 2: Training Regression Models (Salary LPA Prediction)...")
    reg_data = processed_data["regression"]
    reg_metrics, lin_reg, rf_reg = train_regression_models(
        reg_data["X_train"], reg_data["X_test"],
        reg_data["y_train"], reg_data["y_test"]
    )

    combined_metrics = {
        "classification_models": class_metrics,
        "regression_models": reg_metrics
    }

    save_metrics_to_json(combined_metrics)

    # --------------------------------------------------------------------------
    # SAVE TRAINED MODELS (For Web Application Deployment via Flask)
    # --------------------------------------------------------------------------
    os.makedirs(MODELS_DIR, exist_ok=True)

    # Choose best classifier based on F1-Score
    if class_metrics["Logistic_Regression"]["F1_Score"] >= class_metrics["Random_Forest_Classifier"]["F1_Score"]:
        best_classifier = log_reg
    else:
        best_classifier = rf_clf

    # Choose best regressor based on R² Score
    if reg_metrics["Linear_Regression"]["R2_Score"] >= reg_metrics["Random_Forest_Regressor"]["R2_Score"]:
        best_regressor = lin_reg
    else:
        best_regressor = rf_reg

    joblib.dump(best_classifier, os.path.join(MODELS_DIR, "best_classifier.joblib"))
    joblib.dump(best_regressor, os.path.join(MODELS_DIR, "best_regressor.joblib"))
    joblib.dump(class_data["scaler"], os.path.join(MODELS_DIR, "scaler.joblib"))
    joblib.dump(reg_data["scaler"], os.path.join(MODELS_DIR, "regression_scaler.joblib"))
    joblib.dump(processed_data["branch_encoder"], os.path.join(MODELS_DIR, "branch_encoder.joblib"))
    print("Models saved")

    return combined_metrics


if __name__ == "__main__":
    print("--- STEP 4: MODEL TRAINING DEMO ---")
    import pandas as pd
    from preprocessing import preprocess_pipeline

    data_csv = os.path.join(BASE_DIR, "data", "placement_data.csv")
    raw = pd.read_csv(data_csv)
    proc = preprocess_pipeline(raw)
    all_metrics = run_model_training(proc)
    print("[train_models.py] Training completed successfully!")
