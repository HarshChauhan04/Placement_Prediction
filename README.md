# Project 1: Student Placement & Salary Prediction

An end-to-end Machine Learning, NoSQL, and Web Application project built using **Python**, **Flask**, **MongoDB (PyMongo)**, and **scikit-learn**.

This project predicts:
1. **Classification:** Whether a college student will get placed (`1 = Placed`, `0 = Not Placed`).
2. **Regression:** The expected salary package in **Lakhs Per Annum (LPA)** for placed students.

Designed specifically for academic vivas and technical demonstrations, the codebase is logical, beginner-friendly, and free from hidden abstractions or magical code.

---

## 📁 Folder Structure

```text
project1_placement_prediction/
├── app/
│   ├── app.py                  # Flask app: creates app, loads config, registers routes
│   ├── config.py               # SECRET_KEY, DB name, session settings (named constants)
│   ├── db.py                   # MongoDB connection + users/predictions collections + indexes
│   ├── auth.py                 # register, login, logout, lockout logic, @login_required, @admin_required
│   ├── validators.py           # password strength + email + input checks
│   ├── predict.py              # loads saved models, returns placed/not placed + salary + tips
│   ├── admin.py                # admin dashboard routes + Chart.js data + user roster
│   ├── templates/
│   │   ├── base.html           # responsive navbar, flash messages, footer
│   │   ├── register.html       # student registration + live password meter
│   │   ├── login.html          # authentication form with lockout alerts
│   │   ├── dashboard.html      # student home: statistics + prediction history table
│   │   ├── predict.html        # profile assessment form with loading state
│   │   ├── result.html         # prediction card, probability bar, LPA salary, tips
│   │   ├── admin.html          # platform analytics, Chart.js charts, metrics, user list
│   │   ├── 403.html            # custom 403 Forbidden page
│   │   └── 404.html            # custom 404 Not Found page
│   └── static/
│       ├── css/style.css       # clean, responsive stylesheet
│       └── js/password_strength.js # live strength meter & rule checklist
├── data/
│   └── placement_data.csv      # 1000+ realistic synthetic records
├── models/                     # saved .joblib model files & scalers
│   ├── best_classifier.joblib
│   ├── best_regressor.joblib
│   ├── scaler.joblib
│   ├── regression_scaler.joblib
│   └── branch_encoder.joblib
├── outputs/
│   ├── metrics.json            # exported metrics (Accuracy, Precision, Recall, F1, R², MAE)
│   └── charts/
│       ├── confusion_matrix_logistic_regression.png
│       ├── confusion_matrix_random_forest.png
│       └── actual_vs_predicted_regression.png
├── src/
│   ├── generate_dataset.py     # Generates CSV with intentional duplicates & nulls
│   ├── mongo_utils.py          # MongoDB connection, insertion, fetch, find, aggregate, update
│   ├── preprocessing.py        # Deduplication, median imputation, label encoding, scaling, splitting
│   ├── train_models.py         # Classification & regression models, metrics, saves to models/
│   └── main.py                 # Master pipeline running all steps sequentially
├── create_admin.py             # CLI utility to create or reset the administrator account
├── test_app_flow.py            # Automated test suite covering all 8 security/functional cases
├── .env                        # Local secrets (never committed)
├── .env.example                # Secret template
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Python dependencies
├── SECURITY_AND_UI_EXPLANATION.md # Viva prep guide for Auth, Security, CSRF, and Lockout
├── EXPLANATION.md              # Viva prep guide for ML models, metrics, and MongoDB
└── README.md                   # Project documentation & run steps
```

---

## 🛠️ Prerequisites

1. **Python 3.10 or higher**
2. **MongoDB Community Server** installed and running on `localhost:27017`
   - Windows check command: `Get-Service -Name "*mongo*"` or `net start MongoDB`

---

## ⚙️ Installation & Setup

1. Open your terminal / PowerShell in this directory:
   ```bash
   cd "c:\Users\Vishu\Desktop\mongodb projects\project1_placement_prediction"
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Initialize administrator account:
   ```bash
   python create_admin.py
   ```
   *Default Admin Credentials:*
   - **Email:** `admin@placement.edu`
   - **Password:** `SuperSecure#2026`

---

## 🚀 Running the Web Application

Start the Flask development server:
```bash
python app/app.py
```
Open your web browser and visit: **`http://127.0.0.1:5000`**

### Application URLs & Sitemap

| Route | Method | Access | Purpose |
| :--- | :--- | :--- | :--- |
| `/login` | GET, POST | Public | User authentication with 5-attempt lockout |
| `/register` | GET, POST | Public | Student account registration (role is fixed to student) |
| `/logout` | GET | Authenticated | Clears user session |
| `/dashboard` | GET | Student | Student home: statistics & historical predictions |
| `/predict` | GET, POST | Student | Form to input student profile & view prediction result |
| `/admin` | GET | Admin Only | Platform statistics, Chart.js charts, metrics, user list |
| `/admin/charts/<file>` | GET | Admin Only | Safely serves confusion matrix and regression charts |

---

## 🧪 Automated Test Suite

To verify all security and functional requirements, run:
```bash
python test_app_flow.py
```
Tests verified:
1. Registration with weak password (rejected by server validator).
2. Registration with strong password (accepted, hashed, and stored).
3. Duplicate email registration (rejected with friendly error).
4. Account lockout after 5 consecutive bad logins (locked for 15 minutes).
5. Successful login with correct credentials.
6. Student attempting to access `/admin` (blocked with HTTP 403 Forbidden).
7. Placement prediction generated and saved into MongoDB `predictions` collection.
8. Admin dashboard loading live metrics from `outputs/metrics.json` and Chart.js analytics.

---

## 🤖 Running the ML Pipeline (Terminal Mode)

To regenerate synthetic data, retrain models, update `models/`, and regenerate charts:
```bash
python src/main.py
```

---

## 📘 Comprehensive Viva Guides
- **Authentication & Security Guide:** [SECURITY_AND_UI_EXPLANATION.md](file:///c:/Users/Vishu/Desktop/mongodb%20projects/project1_placement_prediction/SECURITY_AND_UI_EXPLANATION.md)
  *(Covers password hashing, CSRF prevention, session management, brute-force lockout, and 10 viva Q&As)*
- **Machine Learning & MongoDB Guide:** [EXPLANATION.md](file:///c:/Users/Vishu/Desktop/mongodb%20projects/project1_placement_prediction/EXPLANATION.md)
  *(Covers model choices, feature scaling, evaluation metrics, and 10 viva Q&As)*
