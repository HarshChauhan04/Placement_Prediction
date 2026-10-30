"""
main.py
=======
Purpose: End-to-end execution pipeline for Project 1: Placement Prediction.
Author: Student Project (Explainable Machine Learning with MongoDB)

This script automates the complete lifecycle:
1. Synthetic data generation with intentional flaws.
2. MongoDB database creation, document insertion, and query demonstrations.
3. Data extraction from MongoDB into a pandas DataFrame.
4. Preprocessing: deduplication, median imputation, branch encoding, and standard scaling.
5. Machine learning model training for both Classification and Regression.
6. Metric logging, chart generation, and console summary display.
"""

import os
import sys

# Ensure local source imports work seamlessly whether run from src/ or project root
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from generate_dataset import generate_placement_dataset, save_dataset_to_csv, CSV_OUTPUT_PATH
from mongo_utils import (
    get_mongo_client,
    insert_csv_to_mongodb,
    fetch_data_from_mongodb,
    find_high_performers_example,
    aggregate_salary_by_branch_example,
    update_student_record_example,
    DATABASE_NAME,
    COLLECTION_NAME
)
from preprocessing import preprocess_pipeline
from train_models import run_model_training


def print_banner(title):
    """Print an attractive, easily readable stage banner for terminal demonstrations."""
    separator = "=" * 80
    print("\n" + separator)
    print(f" {title.upper()}")
    print(separator)


def display_results_summary_table(metrics):
    """
    Format and print a clean summary table of classification and regression results.

    Parameters:
        metrics (dict): Dictionary with classification and regression scores.
    """
    print_banner("Final Model Performance Summary")

    print("\n--- 1. CLASSIFICATION RESULTS (Predicting Placement: Placed vs. Not Placed) ---")
    header_clf = f"{'Model':<28} | {'Accuracy':<10} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10}"
    print("-" * len(header_clf))
    print(header_clf)
    print("-" * len(header_clf))

    clf_models = metrics["classification_models"]
    for model_name, scores in clf_models.items():
        name_clean = model_name.replace("_", " ")
        acc = f"{scores['Accuracy']:.4f}"
        prec = f"{scores['Precision']:.4f}"
        rec = f"{scores['Recall']:.4f}"
        f1 = f"{scores['F1_Score']:.4f}"
        print(f"{name_clean:<28} | {acc:<10} | {prec:<10} | {rec:<10} | {f1:<10}")
    print("-" * len(header_clf))

    print("\n--- 2. REGRESSION RESULTS (Predicting Package: Salary in LPA for Placed Students) ---")
    header_reg = f"{'Model':<28} | {'R2 Score':<12} | {'MAE (LPA)':<12}"
    print("-" * len(header_reg))
    print(header_reg)
    print("-" * len(header_reg))

    reg_models = metrics["regression_models"]
    for model_name, scores in reg_models.items():
        name_clean = model_name.replace("_", " ")
        r2 = f"{scores['R2_Score']:.4f}"
        mae = f"{scores['MAE_LPA']:.4f} LPA"
        print(f"{name_clean:<28} | {r2:<12} | {mae:<12}")
    print("-" * len(header_reg))

    print("\n[INFO] Generated Visualizations in 'outputs/charts/':")
    print("       1. outputs/charts/confusion_matrix_logistic_regression.png")
    print("       2. outputs/charts/confusion_matrix_random_forest.png")
    print("       3. outputs/charts/actual_vs_predicted_regression.png")
    print("[INFO] Metrics JSON saved to 'outputs/metrics.json'")


def main():
    """Execute all project steps in sequential order."""
    print_banner("Student Placement Prediction Pipeline (MongoDB + Scikit-Learn)")

    # --------------------------------------------------------------------------
    # STEP 1: Generate Dataset CSV
    # --------------------------------------------------------------------------
    print("\n>> STEP 1: Generating Realistic Student Placement Dataset...")
    raw_df = generate_placement_dataset()
    save_dataset_to_csv(raw_df, CSV_OUTPUT_PATH)

    # --------------------------------------------------------------------------
    # STEP 2: MongoDB Connection & Data Ingestion
    # --------------------------------------------------------------------------
    print("\n>> STEP 2: Verifying MongoDB Connection and Ingesting CSV...")
    client = get_mongo_client()
    if client is None:
        print("[ERROR] MongoDB connection failed. Please ensure the MongoDB server is running on localhost:27017.")
        sys.exit(1)
    client.close()

    inserted_count = insert_csv_to_mongodb(CSV_OUTPUT_PATH, DATABASE_NAME, COLLECTION_NAME)
    print(f"Step 2 Completed: {inserted_count} records inserted into MongoDB ('{DATABASE_NAME}.{COLLECTION_NAME}').")

    # --------------------------------------------------------------------------
    # STEP 3: Demonstrate MongoDB NoSQL Operations
    # --------------------------------------------------------------------------
    print("\n>> STEP 3: Demonstrating MongoDB Queries (find, aggregate, update_one)...")
    find_high_performers_example(min_cgpa=8.5)
    aggregate_salary_by_branch_example()
    update_student_record_example(student_id="STU1001", new_certifications=3)

    # --------------------------------------------------------------------------
    # STEP 4: Fetch Data from MongoDB for ML Pipeline
    # --------------------------------------------------------------------------
    print("\n>> STEP 4: Fetching Data from MongoDB into Pandas...")
    mongo_df = fetch_data_from_mongodb(DATABASE_NAME, COLLECTION_NAME)
    print(f"Step 4 Completed: Retrieved {len(mongo_df)} documents from MongoDB.")

    # --------------------------------------------------------------------------
    # STEP 5: Data Preprocessing (Cleaning, Imputation, Encoding, Scaling)
    # --------------------------------------------------------------------------
    print("\n>> STEP 5: Preprocessing Data (Deduplication, Imputation, Encoding, Scaling)...")
    processed_data = preprocess_pipeline(mongo_df)
    print("Step 5 Completed: Train/Test datasets ready for Classification & Regression.")

    # --------------------------------------------------------------------------
    # STEP 6: Model Training & Evaluation
    # --------------------------------------------------------------------------
    print("\n>> STEP 6: Training Machine Learning Models and Plotting Charts...")
    metrics = run_model_training(processed_data)
    print("Step 6 Completed: Models trained, evaluation charts plotted, metrics saved.")

    # --------------------------------------------------------------------------
    # STEP 7: Display Final Summary Table
    # --------------------------------------------------------------------------
    display_results_summary_table(metrics)
    print_banner("Pipeline Execution Successfully Completed!")


if __name__ == "__main__":
    main()
