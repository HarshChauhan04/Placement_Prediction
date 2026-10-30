"""
create_admin.py
===============
Purpose: Terminal utility to initialize the system administrator account in MongoDB.
Author: Student Project (Explainable Machine Learning with MongoDB)

WHY A SEPARATE SCRIPT:
Normal users must never be able to register as an administrator through the web interface.
System administrators must be provisioned out-of-band via secure server access or CLI.
"""

import os
import sys
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash

# Ensure project root is in python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from app.db import get_users_collection, init_db_indexes
from app.validators import check_password_strength

DEFAULT_ADMIN_NAME = "System Administrator"
DEFAULT_ADMIN_EMAIL = "admin@placement.edu"
DEFAULT_ADMIN_PASSWORD = "SuperSecure#2026"


def create_or_reset_admin(name=DEFAULT_ADMIN_NAME, email=DEFAULT_ADMIN_EMAIL, password=DEFAULT_ADMIN_PASSWORD):
    """
    Create an administrator document in MongoDB or update credentials if one already exists.

    Parameters:
        name (str): Administrator name.
        email (str): Administrator email.
        password (str): Plaintext password (will be hashed immediately).
    """
    print("----------------------------------------------------------------------")
    print(" Provisioning Administrator Account")
    print("----------------------------------------------------------------------")

    # Validate admin password against security criteria
    is_strong, err_msg = check_password_strength(password, user_name=name, email=email)
    if not is_strong:
        print(f"[ERROR] Password does not meet security rules: {err_msg}")
        return False

    init_db_indexes()
    users_col = get_users_collection()
    if users_col is None:
        print("[ERROR] Could not connect to MongoDB. Please ensure MongoDB is running.")
        return False

    password_hash = generate_password_hash(password, method="pbkdf2:sha256")
    email_clean = email.lower().strip()

    existing_admin = users_col.find_one({"email": email_clean})

    if existing_admin:
        users_col.update_one(
            {"email": email_clean},
            {
                "$set": {
                    "name": name,
                    "password_hash": password_hash,
                    "role": "admin",
                    "failed_attempts": 0,
                    "locked_until": None,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
        print(f"[SUCCESS] Existing admin account '{email_clean}' credentials updated successfully.")
    else:
        new_admin = {
            "name": name,
            "email": email_clean,
            "password_hash": password_hash,
            "role": "admin",
            "failed_attempts": 0,
            "locked_until": None,
            "created_at": datetime.now(timezone.utc)
        }
        users_col.insert_one(new_admin)
        print(f"[SUCCESS] Administrator created successfully!")

    print(f"          Email    : {email_clean}")
    print(f"          Password : {password}")
    print(f"          Role     : admin")
    print("----------------------------------------------------------------------")
    return True


if __name__ == "__main__":
    create_or_reset_admin()
