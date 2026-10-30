"""
generate_dataset.py
===================
Purpose: Generate a realistic 1000-row synthetic placement dataset for college students.
Author: Student Project (Explainable Machine Learning with MongoDB)

This script creates student academic and skill profiles, determines placement status
and salary packages realistically, and introduces intentional missing values and
duplicate rows so we can demonstrate real-world data cleaning in preprocessing.
"""

import os
import numpy as np
import pandas as pd

# ==============================================================================
# NAMED CONSTANTS (No magic numbers)
# ==============================================================================
RANDOM_SEED = 42          # Ensures reproducible random dataset generation
TOTAL_STUDENTS = 1000     # Total student records to generate
DUPLICATE_COUNT = 15      # Number of duplicate records injected to test deduplication
MISSING_CGPA_COUNT = 25   # Number of missing values injected into CGPA
MISSING_CODING_COUNT = 20 # Number of missing values injected into coding score
MISSING_12TH_COUNT = 15   # Number of missing values injected into 12th percentage

# Output directory and file path
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CSV_OUTPUT_PATH = os.path.join(DATA_DIR, "placement_data.csv")

# Available engineering branches
BRANCH_OPTIONS = [
    "Computer Science",
    "Information Technology",
    "Electronics",
    "Mechanical",
    "Civil"
]


def generate_placement_dataset(num_records=TOTAL_STUDENTS, seed=RANDOM_SEED):
    """
    Generate synthetic student records with realistic academic and skill metrics.

    Parameters:
        num_records (int): Number of student records to generate.
        seed (int): Random seed for reproducibility.

    Returns:
        pd.DataFrame: A DataFrame containing raw student records with deliberate flaws.
    """
    np.random.seed(seed)

    # 1. Generate unique student IDs (e.g., STU1001 to STU2000)
    student_ids = [f"STU{1001 + i}" for i in range(num_records)]

    # 2. Academic Scores
    # CGPA: Normal distribution centered around 7.4, bounded between 5.0 and 9.9
    cgpa = np.clip(np.random.normal(loc=7.4, scale=1.0, size=num_records), 5.0, 9.9)
    cgpa = np.round(cgpa, 2)

    # 10th and 12th Board percentages (bounded between 50% and 98%)
    tenth_percent = np.clip(np.random.normal(loc=75.0, scale=10.0, size=num_records), 50.0, 98.0)
    tenth_percent = np.round(tenth_percent, 1)

    twelfth_percent = np.clip(np.random.normal(loc=73.0, scale=10.5, size=num_records), 50.0, 98.0)
    twelfth_percent = np.round(twelfth_percent, 1)

    # 3. Practical Experience and Skills
    # Internships: Most students have 0 to 2, a few have 3 or 4
    internships = np.random.choice([0, 1, 2, 3, 4], size=num_records, p=[0.35, 0.35, 0.20, 0.08, 0.02])

    # Projects completed: Range from 0 to 5
    projects = np.random.choice([0, 1, 2, 3, 4, 5], size=num_records, p=[0.10, 0.25, 0.30, 0.20, 0.10, 0.05])

    # Certifications earned: Range from 0 to 4
    certifications = np.random.choice([0, 1, 2, 3, 4], size=num_records, p=[0.20, 0.35, 0.25, 0.15, 0.05])

    # Coding and communication test scores (out of 100)
    coding_score = np.clip(np.random.normal(loc=65.0, scale=15.0, size=num_records), 30.0, 100.0)
    coding_score = np.round(coding_score, 1)

    communication_score = np.clip(np.random.normal(loc=68.0, scale=14.0, size=num_records), 30.0, 100.0)
    communication_score = np.round(communication_score, 1)

    # Active backlogs: Most students have 0, some have 1 or 2, rare have 3 or 4
    backlogs = np.random.choice([0, 1, 2, 3, 4], size=num_records, p=[0.70, 0.18, 0.07, 0.03, 0.02])

    # Engineering Branch
    branch = np.random.choice(BRANCH_OPTIONS, size=num_records, p=[0.35, 0.25, 0.20, 0.10, 0.10])

    # 4. Realistic Placement Logic
    # Placement depends strongly on CGPA, coding ability, internships, and having zero backlogs.
    # We build a weighted composite score between 0.0 and 1.0.
    composite_score = (
        0.35 * (cgpa / 10.0) +
        0.25 * (coding_score / 100.0) +
        0.15 * (communication_score / 100.0) +
        0.10 * (internships / 4.0) +
        0.10 * (projects / 5.0) -
        0.20 * (backlogs / 4.0)
    )

    # Add small random noise to simulate human interview variance
    noise = np.random.normal(0, 0.05, size=num_records)
    placement_probability = 1.0 / (1.0 + np.exp(-12.0 * (composite_score + noise - 0.52)))

    # Convert probability to binary placement flag (0 = Not Placed, 1 = Placed)
    placed = (np.random.rand(num_records) < placement_probability).astype(int)

    # 5. Realistic Salary Package (LPA) Logic for Placed Students
    # Placed students receive between 3.2 LPA and 24.0 LPA based on skills and grades.
    # Unplaced students have NaN because no package was offered.
    salary_lpa = []
    for i in range(num_records):
        if placed[i] == 1:
            # Base salary is 3.5 LPA
            base = 3.5
            # Premium for good CGPA above 6.0
            cgpa_bonus = max(0.0, (cgpa[i] - 6.0)) * 1.4
            # Premium for high coding performance above 50
            coding_bonus = max(0.0, (coding_score[i] - 50.0)) * 0.12
            # Premium for internships and projects
            experience_bonus = (internships[i] * 0.8) + (projects[i] * 0.4)
            # Small random variation per hiring company
            market_noise = np.random.normal(0, 0.5)

            calculated_salary = base + cgpa_bonus + coding_bonus + experience_bonus + market_noise
            # Clip between entry level minimum (3.2 LPA) and top bracket (24.0 LPA)
            clipped_salary = round(float(np.clip(calculated_salary, 3.2, 24.0)), 2)
            salary_lpa.append(clipped_salary)
        else:
            salary_lpa.append(np.nan)

    # Assemble into a pandas DataFrame
    df = pd.DataFrame({
        "student_id": student_ids,
        "cgpa": cgpa,
        "10th_percent": tenth_percent,
        "12th_percent": twelfth_percent,
        "internships": internships,
        "projects": projects,
        "certifications": certifications,
        "coding_score": coding_score,
        "communication_score": communication_score,
        "backlogs": backlogs,
        "branch": branch,
        "placed": placed,
        "salary_lpa": salary_lpa
    })

    # ==========================================================================
    # INTENTIONAL DATA FLAWS FOR PREPROCESSING DEMONSTRATION
    # In real world datasets, data is never clean. We inject missing values
    # and duplicate rows so the student can explain data cleaning during viva.
    # ==========================================================================

    # Inject missing values in numerical columns
    missing_cgpa_indices = np.random.choice(df.index, size=MISSING_CGPA_COUNT, replace=False)
    df.loc[missing_cgpa_indices, "cgpa"] = np.nan

    missing_coding_indices = np.random.choice(df.index, size=MISSING_CODING_COUNT, replace=False)
    df.loc[missing_coding_indices, "coding_score"] = np.nan

    missing_12th_indices = np.random.choice(df.index, size=MISSING_12TH_COUNT, replace=False)
    df.loc[missing_12th_indices, "12th_percent"] = np.nan

    # Inject duplicate rows by sampling existing rows and appending them
    duplicate_indices = np.random.choice(df.index, size=DUPLICATE_COUNT, replace=False)
    duplicates = df.loc[duplicate_indices].copy()
    df = pd.concat([df, duplicates], ignore_index=True)

    return df


def save_dataset_to_csv(df, output_path=CSV_OUTPUT_PATH):
    """
    Save the generated DataFrame to a CSV file.

    Parameters:
        df (pd.DataFrame): DataFrame to save.
        output_path (str): File destination path.

    Returns:
        str: Absolute path of the saved CSV.
    """
    # Ensure destination folder exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"[generate_dataset.py] Successfully generated and saved dataset to: {output_path}")
    print(f"                      Total rows generated (including {DUPLICATE_COUNT} duplicates): {len(df)}")
    return output_path


if __name__ == "__main__":
    print("--- STEP 1: GENERATING DATASET ---")
    data_frame = generate_placement_dataset()
    save_dataset_to_csv(data_frame)
