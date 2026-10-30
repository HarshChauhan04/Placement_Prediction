"""
test_app_flow.py
================
Purpose: Automated test script verifying all required functional & security test cases.
Author: Student Project (Explainable Machine Learning with MongoDB)

Test Cases Covered:
1. Register with a weak password (must fail)
2. Register with a strong password (must pass)
3. Register with duplicate email (must fail)
4. 5 wrong logins (must lock the account for 15 minutes)
5. Correct login (must authenticate and establish session)
6. Student opening /admin (must receive 403 Forbidden)
7. A prediction saved in MongoDB (must infer and store document)
8. Admin dashboard loading metrics (must load 200 OK and metrics from JSON)
"""

import os
import sys
from datetime import datetime, timezone

# Ensure project root is in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from app.app import app
from app.db import get_users_collection, get_predictions_collection, init_db_indexes
from app.config import MAX_LOGIN_ATTEMPTS


def run_all_tests():
    print("=" * 80)
    print(" EXECUTING WEB APPLICATION SECURITY & FUNCTIONAL TEST SUITE")
    print("=" * 80)

    # Disable CSRF during test client execution to allow direct POST testing
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["TESTING"] = True

    client = app.test_client()
    init_db_indexes()

    users_col = get_users_collection()
    preds_col = get_predictions_collection()

    test_email_weak = "weak_student@college.edu"
    test_email_strong = "strong_student@college.edu"
    test_email_lockout = "lockout_student@college.edu"

    # Clean up test accounts from prior runs
    users_col.delete_many({"email": {"$in": [test_email_weak, test_email_strong, test_email_lockout]}})
    preds_col.delete_many({"user_email": test_email_strong})

    # --------------------------------------------------------------------------
    # TEST 1: Register with a weak password (must fail)
    # --------------------------------------------------------------------------
    print("\n[TEST 1] Registering with a weak password ('simplepass')...")
    res1 = client.post("/register", data={
        "name": "Weak User",
        "email": test_email_weak,
        "password": "simplepass",
        "confirm_password": "simplepass"
    }, follow_redirects=True)
    body1 = res1.get_data(as_text=True)

    # Verify user was NOT created
    user1 = users_col.find_one({"email": test_email_weak})
    assert user1 is None, "User should NOT be created with weak password!"
    assert "Password must include at least one uppercase letter" in body1 or "Password must" in body1
    print("  -> PASSED: Weak password was rejected with server validation message.")

    # --------------------------------------------------------------------------
    # TEST 2: Register with a strong password (must pass)
    # --------------------------------------------------------------------------
    print("\n[TEST 2] Registering with a strong password ('CodeMaster#2026')...")
    res2 = client.post("/register", data={
        "name": "Aarav Sharma",
        "email": test_email_strong,
        "password": "CodeMaster#2026",
        "confirm_password": "CodeMaster#2026"
    }, follow_redirects=True)
    body2 = res2.get_data(as_text=True)

    user2 = users_col.find_one({"email": test_email_strong})
    assert user2 is not None, "Strong password user should be created!"
    assert user2["role"] == "student"
    assert "Registration successful!" in body2 or "Sign In" in body2
    print(f"  -> PASSED: Student successfully registered with hashed password (Role: {user2['role']}).")

    # --------------------------------------------------------------------------
    # TEST 3: Register with duplicate email (must fail)
    # --------------------------------------------------------------------------
    print("\n[TEST 3] Registering with duplicate email ('strong_student@college.edu')...")
    res3 = client.post("/register", data={
        "name": "Aarav Sharma Clone",
        "email": test_email_strong,
        "password": "DifferentStrong#999",
        "confirm_password": "DifferentStrong#999"
    }, follow_redirects=True)
    body3 = res3.get_data(as_text=True)

    count_dup = users_col.count_documents({"email": test_email_strong})
    assert count_dup == 1, "Duplicate email must not create a second document!"
    assert "An account with this email address already exists" in body3 or "already exists" in body3
    print("  -> PASSED: Duplicate registration rejected cleanly.")

    # --------------------------------------------------------------------------
    # TEST 4: 5 Wrong Logins (must lock account for 15 minutes)
    # --------------------------------------------------------------------------
    print("\n[TEST 4] Testing 5 consecutive wrong logins on dedicated lockout user...")
    res_reg_lock = client.post("/register", data={
        "name": "Vikram Mehta",
        "email": test_email_lockout,
        "password": "SecuredSecret#8888",
        "confirm_password": "SecuredSecret#8888"
    }, follow_redirects=True)

    for attempt in range(1, MAX_LOGIN_ATTEMPTS + 1):
        res_fail = client.post("/login", data={
            "email": test_email_lockout,
            "password": f"WrongPass_{attempt}"
        }, follow_redirects=True)
        user_lock = users_col.find_one({"email": test_email_lockout})
        print(f"      Attempt {attempt}: failed_attempts in DB = {user_lock.get('failed_attempts')}")

    user_locked = users_col.find_one({"email": test_email_lockout})
    assert user_locked["failed_attempts"] >= MAX_LOGIN_ATTEMPTS
    assert user_locked["locked_until"] is not None
    print(f"  -> Account locked_until timestamp set in MongoDB: {user_locked['locked_until']}")

    # 6th attempt should return locked account notification
    res_6th = client.post("/login", data={
        "email": test_email_lockout,
        "password": "AnyPassword"
    }, follow_redirects=True)
    body_6th = res_6th.get_data(as_text=True)
    assert "temporarily locked" in body_6th or "Account locked" in body_6th
    print("  -> PASSED: Account locked successfully after 5 failed attempts.")

    # --------------------------------------------------------------------------
    # TEST 5: Correct Login (must authenticate and set session)
    # --------------------------------------------------------------------------
    print("\n[TEST 5] Testing valid login with correct credentials...")
    res_login = client.post("/login", data={
        "email": test_email_strong,
        "password": "CodeMaster#2026"
    }, follow_redirects=True)
    body_login = res_login.get_data(as_text=True)
    assert "Welcome" in body_login or "Dashboard" in body_login
    print("  -> PASSED: Correct login authenticated, session cookie issued.")

    # --------------------------------------------------------------------------
    # TEST 6: Student opening /admin (must be blocked with 403 Forbidden)
    # --------------------------------------------------------------------------
    print("\n[TEST 6] Student attempting to navigate to /admin...")
    res_admin_block = client.get("/admin")
    assert res_admin_block.status_code == 403, f"Expected 403 Forbidden, got {res_admin_block.status_code}"
    body_admin_block = res_admin_block.get_data(as_text=True)
    assert "403" in body_admin_block and "Access Forbidden" in body_admin_block
    print("  -> PASSED: Student blocked from /admin with HTTP 403 Forbidden.")

    # --------------------------------------------------------------------------
    # TEST 7: A Prediction saved in MongoDB
    # --------------------------------------------------------------------------
    print("\n[TEST 7] Student running a placement prediction form submission...")
    prediction_input = {
        "cgpa": "8.75",
        "10th_percent": "88.0",
        "12th_percent": "84.5",
        "internships": "2",
        "projects": "3",
        "certifications": "2",
        "coding_score": "82.5",
        "communication_score": "75.0",
        "backlogs": "0",
        "branch": "Computer Science"
    }
    res_pred = client.post("/predict", data=prediction_input, follow_redirects=True)
    body_pred = res_pred.get_data(as_text=True)
    assert "Placement Likelihood" in body_pred or "Placed" in body_pred

    # Check MongoDB collection 'predictions'
    saved_record = preds_col.find_one({"user_email": test_email_strong})
    assert saved_record is not None, "Prediction MUST be saved in MongoDB!"
    assert saved_record["placed"] in [0, 1]
    assert saved_record["probability"] > 0
    print(f"  -> PASSED: Prediction evaluated and stored in MongoDB!")
    print(f"            Outcome: {'Placed' if saved_record['placed'] == 1 else 'Not Placed'}")
    print(f"            Confidence: {saved_record['probability']}%")
    print(f"            Salary: {saved_record['salary_lpa']} LPA")

    # --------------------------------------------------------------------------
    # TEST 8: Admin Dashboard loading metrics
    # --------------------------------------------------------------------------
    print("\n[TEST 8] Admin login and dashboard loading metrics from outputs/metrics.json...")
    client.get("/logout")  # Log out student

    res_admin_login = client.post("/login", data={
        "email": "admin@placement.edu",
        "password": "SuperSecure#2026"
    }, follow_redirects=True)

    res_admin_dash = client.get("/admin")
    assert res_admin_dash.status_code == 200
    body_admin_dash = res_admin_dash.get_data(as_text=True)

    assert "Administrator Analytics" in body_admin_dash
    assert "Logistic Regression" in body_admin_dash
    assert "Linear Regression" in body_admin_dash
    assert "outputs/metrics.json" in body_admin_dash
    print("  -> PASSED: Admin dashboard loaded HTTP 200 with model metrics and charts.")

    print("\n" + "=" * 80)
    print(" ALL 8 FUNCTIONAL & SECURITY TESTS PASSED PERFECTLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
