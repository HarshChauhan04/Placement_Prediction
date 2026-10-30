"""
app/config.py
=============
Purpose: Central configuration file storing all application settings as named constants.
Author: Student Project (Explainable Machine Learning with MongoDB)

This file loads environment variables securely from .env and defines:
- Security keys and session policies
- MongoDB database and collection names
- Account lockout rules (attempts and duration)
- Password validation parameters
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Base paths
APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(APP_DIR)

# Load environment variables from .env file located at project root
ENV_FILE_PATH = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(ENV_FILE_PATH)

# ==============================================================================
# SECURITY & FLASK SETTINGS
# ==============================================================================
# SECRET_KEY is used by Flask to sign session cookies and by Flask-WTF for CSRF tokens.
# Loading from environment ensures secrets are never committed into source control.
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_dev_secret_key_change_in_production_123456")

# Session Inactivity Timeout: 30 minutes
# If the student is idle for 30 minutes, their session expires automatically.
SESSION_TIMEOUT_MINUTES = 30
PERMANENT_SESSION_LIFETIME = timedelta(minutes=SESSION_TIMEOUT_MINUTES)

# Cookie Security Flags:
# HttpOnly prevents client-side JavaScript from reading the session cookie (mitigates XSS).
# SameSite='Lax' protects against Cross-Site Request Forgery (CSRF).
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# ==============================================================================
# MONGODB CONFIGURATION
# ==============================================================================
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "placement_db")

# Collection Names
USERS_COLLECTION = "users"
PREDICTIONS_COLLECTION = "predictions"
STUDENTS_COLLECTION = "students"

# Connection Timeout
MONGO_TIMEOUT_MS = 3000

# ==============================================================================
# AUTHENTICATION & LOCKOUT POLICIES (Brute-Force Protection)
# ==============================================================================
# After 5 consecutive failed logins, the account is locked for 15 minutes.
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

# Password Strength Rules
MIN_PASSWORD_LENGTH = 8

# Common blocked passwords that are trivially guessable
COMMON_PASSWORDS_BLOCKLIST = {
    "password", "password123", "qwerty123", "admin123",
    "12345678", "welcome123", "placement123", "student123",
    "letmein123", "iloveyou123"
}

# ==============================================================================
# FILE SYSTEM PATHS FOR MACHINE LEARNING ASSETS
# ==============================================================================
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")
CHARTS_DIR = os.path.join(OUTPUTS_DIR, "charts")
METRICS_JSON_PATH = os.path.join(OUTPUTS_DIR, "metrics.json")
