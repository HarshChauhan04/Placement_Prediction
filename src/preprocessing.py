"""
preprocessing.py
================
Purpose: Clean, encode, scale, and split student placement data.
Author: Student Project (Explainable Machine Learning with MongoDB)

This script performs:
1. Deduplication: Removing repeated student records.
2. Missing Value Imputation: Filling missing numerical scores with the median
   (because the median is not influenced by extreme outliers) and categorical values with the mode.
3. Categorical Encoding: Converting text branches (e.g. Computer Science) into numerical labels.
4. Feature Scaling: Standardizing numeric features using StandardScaler so features with large
   magnitudes (e.g., coding scores 0-100) do not dominate smaller features (e.g., internships 0-4).
5. Train/Test Splitting: Splitting data into 80% training and 20% testing sets.
   (80/20 provides enough data for model learning while leaving a clean hold-out set for evaluation).
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

# ==============================================================================
# NAMED CONSTANTS (No magic numbers)
# ==============================================================================
RANDOM_STATE = 42       # Ensures train/test split is identical across runs
TEST_SIZE = 0.2         # 80% train, 20% test (industry standard ratio)

# Feature column definitions
FEATURE_COLUMNS = [
    "cgpa",
    "10th_percent",
    "12th_percent",
    "internships",
    "projects",
    "certifications",
    "coding_score",
    "communication_score",
    "backlogs",
    "branch_encoded"
]


def remove_duplicates(df):
    """
    Remove duplicate student records based on student_id.

    Parameters:
        df (pd.DataFrame): Raw DataFrame from MongoDB.

    Returns:
        pd.DataFrame: Deduplicated DataFrame.
    """
    initial_count = len(df)
    # Deduplicate based on unique student identifier
    cleaned_df = df.drop_duplicates(subset=["student_id"]).copy()
    dropped_count = initial_count - len(cleaned_df)

    print(f"[preprocessing.py] Step 1 - Deduplication: Removed {dropped_count} duplicate rows (Remaining: {len(cleaned_df)})")
    return cleaned_df


def handle_missing_values(df):
    """
    Impute missing values in numerical and categorical columns.

    Parameters:
        df (pd.DataFrame): DataFrame possibly containing nulls.

    Returns:
        pd.DataFrame: Fully imputed DataFrame.
    """
    cleaned_df = df.copy()

    # List of numerical columns subject to missing values
    numeric_columns = [
        "cgpa",
        "10th_percent",
        "12th_percent",
        "internships",
        "projects",
        "certifications",
        "coding_score",
        "communication_score",
        "backlogs"
    ]

    for col in numeric_columns:
        if col in cleaned_df.columns:
            missing_count = cleaned_df[col].isnull().sum()
            if missing_count > 0:
                # WHY MEDIAN: We fill missing numerical values with the median because the median
                # is resilient to outliers (unlike the mean, which is pulled by extreme minimums/maximums).
                median_value = cleaned_df[col].median()
                cleaned_df[col] = cleaned_df[col].fillna(median_value)
                print(f"[preprocessing.py] Step 2 - Imputation: Filled {missing_count} missing values in '{col}' with median: {median_value:.2f}")

    # Handle categorical columns if any missing
    if "branch" in cleaned_df.columns and cleaned_df["branch"].isnull().sum() > 0:
        # WHY MODE: For categorical text variables, the mode (most frequent value) is the standard statistical imputation.
        mode_branch = cleaned_df["branch"].mode()[0]
        cleaned_df["branch"] = cleaned_df["branch"].fillna(mode_branch)
        print(f"[preprocessing.py] Step 2 - Imputation: Filled missing branch with mode: '{mode_branch}'")

    return cleaned_df


def encode_branch(df):
    """
    Encode categorical engineering branch names into integer labels.

    Parameters:
        df (pd.DataFrame): Cleaned DataFrame.

    Returns:
        tuple: (DataFrame with 'branch_encoded', LabelEncoder instance)
    """
    encoded_df = df.copy()
    label_encoder = LabelEncoder()

    # WHY LABEL ENCODING: Tree models and linear models require numeric inputs.
    # Label encoding assigns 0, 1, 2, ... to distinct categories cleanly.
    encoded_df["branch_encoded"] = label_encoder.fit_transform(encoded_df["branch"])

    print("[preprocessing.py] Step 3 - Encoding: Branch categories mapped to integers:")
    for idx, class_name in enumerate(label_encoder.classes_):
        print(f"                     {class_name} -> {idx}")

    return encoded_df, label_encoder


def prepare_classification_data(df, feature_cols=FEATURE_COLUMNS, test_size=TEST_SIZE, random_state=RANDOM_STATE):
    """
    Split and scale features for the classification task (predicting 'placed' 0 or 1).

    Parameters:
        df (pd.DataFrame): Preprocessed DataFrame.
        feature_cols (list): List of input feature names.
        test_size (float): Fraction of data reserved for testing.
        random_state (int): Seed for repeatable split.

    Returns:
        tuple: (X_train_scaled, X_test_scaled, y_train, y_test, scaler, feature_cols)
    """
    X = df[feature_cols].values
    y = df["placed"].values

    # WHY 80/20 SPLIT & STRATIFY:
    # 80/20 gives 800 training examples for good parameter convergence and 200 test examples for validation.
    # stratify=y preserves the exact class balance (placed vs unplaced) in both train and test partitions.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # WHY STANDARD SCALER:
    # Features have vastly different units (e.g. CGPA is 5-10, coding score is 30-100).
    # StandardScaler transforms each feature to mean=0 and standard deviation=1.
    # We fit the scaler ONLY on X_train to prevent test data leakage into training.
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print(f"[preprocessing.py] Step 4 - Classification Split: {len(X_train_scaled)} train samples, {len(X_test_scaled)} test samples")
    return X_train_scaled, X_test_scaled, y_train, y_test, scaler, feature_cols


def prepare_regression_data(df, feature_cols=FEATURE_COLUMNS, test_size=TEST_SIZE, random_state=RANDOM_STATE):
    """
    Split and scale features for the regression task (predicting 'salary_lpa' for placed students only).

    Parameters:
        df (pd.DataFrame): Preprocessed DataFrame.
        feature_cols (list): List of input feature names.
        test_size (float): Fraction of data reserved for testing.
        random_state (int): Seed for repeatable split.

    Returns:
        tuple: (X_train_scaled, X_test_scaled, y_train, y_test, scaler, feature_cols)
    """
    # WHY PLACED STUDENTS ONLY:
    # Unplaced students do not receive salary offers. Assigning them 0 LPA would distort
    # the regression model line and penalize realistic package estimates for actual hires.
    placed_df = df[df["placed"] == 1].copy()

    X = placed_df[feature_cols].values
    y = placed_df["salary_lpa"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print(f"[preprocessing.py] Step 5 - Regression Split (Placed Only): {len(X_train_scaled)} train samples, {len(X_test_scaled)} test samples")
    return X_train_scaled, X_test_scaled, y_train, y_test, scaler, feature_cols


def preprocess_pipeline(raw_df):
    """
    Run the end-to-end preprocessing pipeline on raw data retrieved from MongoDB.

    Parameters:
        raw_df (pd.DataFrame): Raw DataFrame from MongoDB.

    Returns:
        dict: Processed classification datasets, regression datasets, and transformers.
    """
    cleaned_df = remove_duplicates(raw_df)
    imputed_df = handle_missing_values(cleaned_df)
    encoded_df, branch_encoder = encode_branch(imputed_df)

    X_train_c, X_test_c, y_train_c, y_test_c, scaler_c, feat_cols = prepare_classification_data(encoded_df)
    X_train_r, X_test_r, y_train_r, y_test_r, scaler_r, _ = prepare_regression_data(encoded_df)

    return {
        "cleaned_df": encoded_df,
        "branch_encoder": branch_encoder,
        "classification": {
            "X_train": X_train_c,
            "X_test": X_test_c,
            "y_train": y_train_c,
            "y_test": y_test_c,
            "scaler": scaler_c,
            "feature_names": feat_cols
        },
        "regression": {
            "X_train": X_train_r,
            "X_test": X_test_r,
            "y_train": y_train_r,
            "y_test": y_test_r,
            "scaler": scaler_r,
            "feature_names": feat_cols
        }
    }


if __name__ == "__main__":
    print("--- STEP 3: PREPROCESSING DEMO ---")
    import os
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "placement_data.csv")
    raw_data = pd.read_csv(data_path)
    processed = preprocess_pipeline(raw_data)
    print("[preprocessing.py] Preprocessing pipeline finished successfully!")
