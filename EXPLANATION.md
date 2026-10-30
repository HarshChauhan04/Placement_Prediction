# Student Placement Prediction & Salary Estimation
## Comprehensive Viva & Technical Guide

This document is your complete preparation handbook for project presentations, viva examinations, and technical demos. Everything is explained in clear, plain English without academic jargon or unnecessary math.

---

## 1. Project Goal & Overview

In college campus placements, institutions and students want answers to two key questions:
1. **Will this student get placed?** (A **binary classification** problem: `1` for Placed, `0` for Not Placed).
2. **If placed, what salary package can they expect?** (A **regression** problem: continuous salary in Lakhs Per Annum - LPA).

This project demonstrates the complete end-to-end Machine Learning lifecycle combined with **MongoDB** as a modern NoSQL document database:
- Raw student data is stored as JSON/BSON documents in MongoDB.
- Analytical queries and aggregation pipelines are run directly on MongoDB.
- Data is retrieved into Pandas, cleaned, scaled, and split without data leakage.
- Machine learning models are trained and evaluated with real metrics and visualizations.

---

## 2. End-to-End Architecture & Data Flow

```text
+-----------------------+
|  generate_dataset.py  |  --> Synthesizes 1000 student records with realistic
+-----------------------+      correlations + intentional flaws (duplicates & nulls)
            |
            v
+-----------------------+
|   placement_data.csv  |  --> Stored under data/
+-----------------------+
            |
            v
+-----------------------+
|    mongo_utils.py     |  --> Connects to MongoDB ("placement_db", "students")
+-----------------------+      - Inserts raw documents
            |                  - Executes find(), aggregate(), update_one()
            v                  - Fetches data back into Pandas DataFrame
+-----------------------+
|   preprocessing.py    |  --> 1. Deduplication (removes duplicate student_ids)
+-----------------------+      2. Median Imputation for numerical features
            |                  3. Mode Imputation for categorical branch
            |                  4. Label Encoding for branch categories
            |                  5. 80/20 Train-Test Split (with stratification for clf)
            |                  6. StandardScaler (fit on train only to prevent leakage)
            v
+-----------------------+
|    train_models.py    |  --> Classification: Logistic Regression & Random Forest
+-----------------------+      Regression: Linear Regression & Random Forest Regressor
            |                  Calculates real metrics & generates charts
            v
+-----------------------+
|  outputs/ & main.py   |  --> outputs/metrics.json
+-----------------------+      outputs/charts/ (Confusion matrices & actual vs pred)
                               Prints final summary table in console
```

---

## 3. What Each File Does (File-by-File Breakdown)

### `src/generate_dataset.py`
- **Role:** Generates 1000 student rows based on academic indicators (CGPA, 10th %, 12th %) and skill indicators (internships, projects, certifications, coding score, communication score, backlogs, branch).
- **Placement Logic:** Calculates a weighted composite score reflecting real hiring criteria (CGPA + coding skills + zero backlogs have highest weight) passed through a sigmoid probability curve.
- **Salary Logic:** For placed candidates, package starts at 3.5 LPA base, augmented by bonuses for high CGPA (>6.0), coding proficiency (>50), internships, and projects.
- **Intentional Flaws:** Injects 15 duplicate rows and ~60 missing values across `cgpa`, `coding_score`, and `12th_percent` to simulate messy real-world data for cleaning.

### `src/mongo_utils.py`
- **Role:** Centralizes all database operations using `pymongo.MongoClient`.
- **Key Functions:**
  1. `get_mongo_client()`: Connects with a 3000ms timeout and pings the admin command to verify the server is live.
  2. `insert_csv_to_mongodb()`: Clears stale collections and bulk-inserts student dictionaries using `insert_many()`.
  3. `fetch_data_from_mongodb()`: Queries `collection.find({}, {"_id": 0})` to read all documents into Pandas without exposing the internal MongoDB ObjectId.
  4. `find_high_performers_example()`: Demonstrates filtering with `$gte` (students with CGPA >= 8.5 who are placed).
  5. `aggregate_salary_by_branch_example()`: Executes a 3-stage aggregation pipeline (`$match`, `$group`, `$sort`) to calculate average salary and placement headcount by engineering branch.
  6. `update_student_record_example()`: Demonstrates atomic document updates using `collection.update_one()` with the `$set` operator.

### `src/preprocessing.py`
- **Role:** Transforms raw database records into clean, scaled numeric matrices ready for scikit-learn models.
- **Step 1 (Deduplication):** Uses `drop_duplicates(subset=["student_id"])`.
- **Step 2 (Imputation):**
  - Numerical missing values are replaced with the **median**.
  - *Why Median?* The mean is pulled by extreme minimums or maximums (outliers). The median is the middle value and represents typical student performance accurately.
  - Categorical missing values are replaced with the **mode** (most frequent class).
- **Step 3 (Categorical Encoding):** `LabelEncoder` maps branches to distinct integers (e.g., Computer Science $\rightarrow$ 1, Mechanical $\rightarrow$ 4).
- **Step 4 (Feature Scaling):** `StandardScaler` centers data to mean = 0 and standard deviation = 1.
  - *Why?* Coding scores range from 30 to 100, while internships range from 0 to 4. Without scaling, linear models would treat coding scores as 25x more important solely due to their larger numbers.
- **Step 5 (80/20 Train/Test Split):**
  - 80% (800 rows) is used for training model weights; 20% (200 rows) is held out as unseen test data.
  - Classification split uses `stratify=y` to ensure the exact same proportion of placed vs unplaced candidates in both sets.
  - Regression uses only students where `placed == 1` because unplaced students have no legitimate offer package.

### `src/train_models.py`
- **Role:** Fits models, computes performance metrics, plots diagnostic graphs, and saves JSON output.
- **Classification Models:** Logistic Regression and Random Forest Classifier.
- **Regression Models:** Linear Regression and Random Forest Regressor.
- **Outputs Produced:**
  - `outputs/metrics.json`: JSON document storing exact scores for all 4 models.
  - `outputs/charts/confusion_matrix_logistic_regression.png`
  - `outputs/charts/confusion_matrix_random_forest.png`
  - `outputs/charts/actual_vs_predicted_regression.png`

### `src/main.py`
- **Role:** The conductor of the entire project. Executes all functions in sequence, prints step-by-step progress banners, and displays a formatted summary table at the end.

---

## 4. Why These Models Were Chosen

| Task | Model | Why This Model? |
| :--- | :--- | :--- |
| **Classification** | **Logistic Regression** | **Baseline & Interpretable:** Standard linear model for binary classification. It outputs probabilities using the sigmoid curve ($S(z) = \frac{1}{1 + e^{-z}}$) and lets you inspect feature weights directly. |
| **Classification** | **Random Forest Classifier** | **Non-Linear & Robust:** An ensemble of 100 decision trees trained with bagging (bootstrap aggregation). It captures non-linear thresholds (e.g., "if CGPA > 8.0 AND backlogs == 0") and resists overfitting. |
| **Regression** | **Linear Regression** | **Parametric Baseline:** Computes the best-fit hyperplane by minimizing Ordinary Least Squares (OLS) residual error. Easy to explain to an examiner. |
| **Regression** | **Random Forest Regressor** | **Ensemble Non-Linearity:** Averages predictions across 100 regression trees. Easily models complex package tiers (e.g., elite coders receiving disproportionately higher CTCs). |

---

## 5. What Each Metric Means in Plain English

### Classification Metrics

1. **Accuracy**:
   - *Formula:* $\frac{\text{Correct Predictions}}{\text{Total Predictions}}$
   - *Plain English:* Out of 100 students tested, how many did the model predict correctly overall?
   - *Example:* 0.6800 means 68% of student outcomes were correctly classified.

2. **Precision**:
   - *Formula:* $\frac{\text{True Positives}}{\text{True Positives} + \text{False Positives}}$
   - *Plain English:* When the model claims "This student will get placed", how often is it actually right?
   - *High precision matters to:* A company recruiter who only wants to interview candidates who will actually accept and qualify.

3. **Recall (Sensitivity)**:
   - *Formula:* $\frac{\text{True Positives}}{\text{True Positives} + \text{False Negatives}}$
   - *Plain English:* Out of all students who actually got placed in real life, how many did the model manage to find?
   - *High recall matters to:* College training officers who want to ensure no employable candidate gets overlooked.

4. **F1-Score**:
   - *Formula:* $2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$
   - *Plain English:* The harmonic mean balancing precision and recall. It gives an honest single score even if classes are moderately imbalanced.

5. **Confusion Matrix**:
   - A 2x2 grid displaying:
     - **True Negatives (TN):** Correctly predicted Not Placed.
     - **False Positives (FP):** Predicted Placed, but actually Not Placed (Type I Error).
     - **False Negatives (FN):** Predicted Not Placed, but actually Placed (Type II Error).
     - **True Positives (TP):** Correctly predicted Placed.

### Regression Metrics (Salary in LPA)

1. **$R^2$ Score (Coefficient of Determination)**:
   - *Plain English:* What percentage of the variation in salary packages is successfully explained by our student's features (CGPA, coding score, internships)?
   - *Scale:* Up to 1.0 (1.0 = perfect prediction; 0.0 = no better than guessing the average salary).
   - *Our Result:* ~0.91 means 91% of salary variations are explained by the input features.

2. **MAE (Mean Absolute Error)**:
   - *Plain English:* On average, by how many Lakhs Per Annum is our salary prediction off from the real offer?
   - *Unit:* LPA.
   - *Our Result:* ~0.49 LPA means the model's prediction is, on average, within $\pm 0.49$ Lakhs (under ₹50,000) of the real package.

---

## 6. Why MongoDB is Used in This ML Project

Examiners frequently ask: *"Why did you use MongoDB instead of MySQL or SQLite?"*

1. **Native JSON/BSON Alignment:**
   Student records naturally exist as nested JSON objects (e.g., skill profiles, certification lists). PyMongo allows seamless conversions:
   `DataFrame -> dict -> MongoDB Collection -> DataFrame`.
2. **Schema Flexibility:**
   Different branches or future college batches may record new attributes (e.g., GitHub profile link, hackathon rankings, LeetCode ratings). MongoDB collections can store documents with varying fields without requiring expensive `ALTER TABLE` schema migrations.
3. **Powerful Aggregation Framework:**
   MongoDB computes server-side aggregations (such as grouping average package by engineering branch) in memory before data is ever sent across the network.
4. **Separation of Raw Data Store and ML Engine:**
   MongoDB acts as the enterprise central data lake. Data scientists query, clean, and extract only the relevant subsets into memory without altering raw candidate records.

---

## 7. Top 10 Viva Questions & High-Scoring Answers

### Q1: Why did you split the dataset 80/20 instead of training on 100% of the data?
> **Answer:** If we trained on 100% of the data, the model could simply memorize the students (overfitting). By holding out 20% of the data as an unseen test set, we test how well the model generalizes to new, unseen students. 80/20 is an industry-standard split providing enough data for training while maintaining statistical reliability in testing.

### Q2: What is Data Leakage and how did you prevent it?
> **Answer:** Data leakage occurs when information from the test dataset accidentally influences the training process, causing overly optimistic results. In our code, we prevented data leakage by:
> 1. Splitting train and test sets *before* scaling.
> 2. Calling `scaler.fit_transform(X_train)` on training data only.
> 3. Calling `scaler.transform(X_test)` on testing data without refitting.

### Q3: Why did you use Median instead of Mean to fill missing values?
> **Answer:** The mean is sensitive to extreme values (outliers). For example, if a few students had a 0 or 100 in coding score, the mean would be pulled in that direction. The median is the middle value and remains robust against outliers, preserving the natural distribution.

### Q4: Why did you predict salary only for placed students?
> **Answer:** Unplaced students do not receive salary offers. If we assigned them 0 LPA, the regression line would be heavily pulled downward, treating non-placement as an extreme low-salary outlier and corrupting the salary predictions for actual corporate packages. Therefore, placement is a two-stage process: first classification (Placed vs. Unplaced), then regression (Package in LPA) on the placed subset.

### Q5: What is the difference between Logistic Regression and Linear Regression?
> **Answer:**
> - **Linear Regression** predicts a continuous numeric output (e.g., salary = 8.5 LPA) by fitting a straight line ($y = mx + c$).
> - **Logistic Regression** predicts a probability between 0 and 1 for classification by wrapping the linear equation in a sigmoid activation function ($p = \frac{1}{1 + e^{-z}}$), then thresholding at 0.5 for Placed (1) vs Not Placed (0).

### Q6: What does the Confusion Matrix show that Accuracy does not?
> **Answer:** Accuracy only gives the overall percentage of correct guesses. The Confusion Matrix breaks down *where* errors occurred: specifically, whether the model made False Positive errors (promising a job to someone who didn't get placed) or False Negative errors (failing to identify an eligible student).

### Q7: Why do we scale features with `StandardScaler`?
> **Answer:** Our features have different measurement scales. CGPA is between 5 and 10, whereas coding test score is between 30 and 100. Algorithms like Logistic Regression calculate distances and gradients. Features with large numbers would artificially dominate the model weights. `StandardScaler` transforms all features to have a mean of 0 and standard deviation of 1.

### Q8: What is the difference between a single Decision Tree and Random Forest?
> **Answer:** A single Decision Tree creates a set of if-else rules, but tends to overfit and is sensitive to small changes in training data. A Random Forest builds 100 decision trees on random subsets of data and features (bagging), then averages their votes. This drastically reduces variance and produces more stable, accurate predictions.

### Q9: How did you implement MongoDB in this project?
> **Answer:** We used the official `pymongo` Python driver. We connected to a local MongoDB server on port 27017, created a database called `placement_db`, and stored raw student records in the `students` collection. We demonstrated `insert_many()`, `find()` with filters, `update_one()` with the `$set` operator, and a 3-stage `aggregate()` pipeline for branch-wise statistics.

### Q10: What is the difference between R² Score and MAE in evaluating regression?
> **Answer:**
> - **$R^2$** is a unitless statistical measure indicating the proportion of variance explained by the model (relative to simply predicting the mean). A score of 0.91 means 91% of package variation is explained.
> - **MAE (Mean Absolute Error)** is expressed in real-world units (LPA). An MAE of 0.49 LPA directly tells us that on average, our salary estimate is off by roughly ₹49,000.
