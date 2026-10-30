"""
app/db.py
=========
Purpose: MongoDB connection management and schema definition for users and predictions.
Author: Student Project (Explainable Machine Learning with MongoDB)

MONGODB COLLECTIONS SCHEMA DOCUMENTATION:
-----------------------------------------
1. Collection: 'users'
   Stores authentication and access control credentials.
   Schema:
   {
       "_id": ObjectId(...),
       "name": str,                  # Student or Admin full name
       "email": str,                 # Unique student/admin email address (UNIQUE INDEX)
       "password_hash": str,         # Secure password hash generated via werkzeug.security
       "role": str,                  # 'student' or 'admin'
       "failed_attempts": int,       # Counter for consecutive bad logins (reset to 0 on success)
       "locked_until": datetime,     # Expiration timestamp for temporary lockout (or None)
       "created_at": datetime        # Registration timestamp
   }

2. Collection: 'predictions'
   Stores history of all student placement predictions.
   Schema:
   {
       "_id": ObjectId(...),
       "user_id": str,               # Stringified ObjectId of the student
       "user_email": str,            # Student email for display convenience
       "inputs": {                   # Dictionary of input features
           "cgpa": float,
           "10th_percent": float,
           "12th_percent": float,
           "internships": int,
           "projects": int,
           "certifications": int,
           "coding_score": float,
           "communication_score": float,
           "backlogs": int,
           "branch": str
       },
       "placed": int,                # 1 = Placed, 0 = Not Placed
       "probability": float,         # Placement probability in % (e.g. 84.5%)
       "salary_lpa": float or None,  # Estimated salary (LPA) if placed, else None
       "created_at": datetime        # Timestamp of prediction
   }
"""

import sys
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from app.config import (
    MONGO_URI,
    DATABASE_NAME,
    USERS_COLLECTION,
    PREDICTIONS_COLLECTION,
    MONGO_TIMEOUT_MS
)

# Global client cache to avoid recreating connection on every request
_mongo_client = None


def get_db_client():
    """
    Get or create a verified MongoClient instance.

    Returns:
        MongoClient or None: Connected client, or None if connection fails.
    """
    global _mongo_client
    if _mongo_client is None:
        try:
            _mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=MONGO_TIMEOUT_MS)
            # Ping database to confirm live connectivity
            _mongo_client.admin.command("ping")
        except (ConnectionFailure, ServerSelectionTimeoutError) as err:
            print(f"[db.py] ERROR: MongoDB connection failed: {err}")
            return None
    return _mongo_client


def get_database():
    """
    Retrieve the placement database handle.

    Returns:
        Database or None: The MongoDB database object.
    """
    client = get_db_client()
    if client is None:
        return None
    return client[DATABASE_NAME]


def get_users_collection():
    """
    Retrieve the users collection handle.

    Returns:
        Collection or None
    """
    db = get_database()
    if db is None:
        return None
    return db[USERS_COLLECTION]


def get_predictions_collection():
    """
    Retrieve the predictions collection handle.

    Returns:
        Collection or None
    """
    db = get_database()
    if db is None:
        return None
    return db[PREDICTIONS_COLLECTION]


def init_db_indexes():
    """
    Ensure essential database indexes exist.
    Creates a unique index on 'email' in the users collection to guarantee
    that duplicate accounts cannot be created at the database level.
    """
    users_col = get_users_collection()
    if users_col is not None:
        try:
            # WHY UNIQUE INDEX: Enforcing uniqueness at the database level prevents race
            # conditions where two simultaneous registrations with the same email could succeed.
            users_col.create_index([("email", ASCENDING)], unique=True)
            print("[db.py] Unique index on 'users.email' verified.")
        except Exception as e:
            print(f"[db.py] Warning creating index on users: {e}")

    preds_col = get_predictions_collection()
    if preds_col is not None:
        try:
            # Index on user_id and created_at speeds up student history lookups
            preds_col.create_index([("user_id", ASCENDING), ("created_at", ASCENDING)])
            print("[db.py] Index on 'predictions.user_id' verified.")
        except Exception as e:
            print(f"[db.py] Warning creating index on predictions: {e}")
