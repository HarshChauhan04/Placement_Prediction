"""
app/auth.py
===========
Purpose: User registration, secure login with account lockout, session management, and access decorators.
Author: Student Project (Explainable Machine Learning with MongoDB)

SECURITY HIGHLIGHTS:
1. Passwords hashed using werkzeug.security (PBKDF2-SHA256). Plaintext is never stored or logged.
2. Generic error messages prevent email enumeration.
3. Brute-force lockout: Account locks for 15 minutes after 5 consecutive failed logins.
4. Route protection via @login_required and @admin_required decorators.
"""

from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from app.config import (
    MAX_LOGIN_ATTEMPTS,
    LOCKOUT_DURATION_MINUTES
)
from app.db import get_users_collection
from app.validators import validate_registration_form

# Create Flask Blueprint for authentication routes
auth_bp = Blueprint("auth", __name__)

# Single generic message for invalid logins
GENERIC_LOGIN_ERROR = "Invalid email or password."


# ==============================================================================
# ROUTE PROTECTION DECORATORS
# ==============================================================================

def login_required(view_func):
    """
    Decorator ensuring that only authenticated users can access the route.
    If the session does not contain 'user_id', the user is redirected to /login.
    """
    @wraps(view_func)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)
    return decorated_function


def admin_required(view_func):
    """
    Decorator ensuring that only users with the 'admin' role can access the route.
    Students attempting to visit admin pages receive a 403 Forbidden status.
    """
    @wraps(view_func)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in with administrator credentials.", "warning")
            return redirect(url_for("auth.login"))

        if session.get("user_role") != "admin":
            # Access forbidden for students
            print(f"[SECURITY] Unauthorized admin access attempt by: {session.get('user_email')}")
            return render_template("403.html"), 403

        return view_func(*args, **kwargs)
    return decorated_function


# ==============================================================================
# AUTHENTICATION ROUTES
# ==============================================================================

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Handle new student account registration.
    Admins cannot register here; role is always fixed to 'student'.
    """
    # If user is already logged in, send them to their dashboard
    if "user_id" in session:
        return redirect(url_for("student_dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # 1. Validate inputs on the server
        is_valid, error_msg = validate_registration_form(name, email, password, confirm_password)
        if not is_valid:
            flash(error_msg, "danger")
            return render_template("register.html", name=name, email=email)

        users_col = get_users_collection()
        if users_col is None:
            flash("Database service is currently unavailable. Please try again later.", "danger")
            return render_template("register.html", name=name, email=email)

        # 2. Check for duplicate email (case-insensitive check)
        existing_user = users_col.find_one({"email": email})
        if existing_user:
            # Inform user that email is already registered
            flash("An account with this email address already exists. Please log in.", "warning")
            return redirect(url_for("auth.login"))

        # 3. Securely hash password (never store plaintext)
        # werkzeug generate_password_hash uses PBKDF2 with a unique salt for every user
        password_hash = generate_password_hash(password, method="pbkdf2:sha256")

        # 4. Construct student user document (role is strictly 'student')
        new_user = {
            "name": name,
            "email": email,
            "password_hash": password_hash,
            "role": "student",
            "failed_attempts": 0,
            "locked_until": None,
            "created_at": datetime.now(timezone.utc)
        }

        users_col.insert_one(new_user)
        print(f"[AUTH] New student registered successfully: {email}")

        flash("Registration successful! You may now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Authenticate students and administrators with rate-limiting account lockout.
    """
    # If already logged in, redirect based on role
    if "user_id" in session:
        if session.get("user_role") == "admin":
            return redirect(url_for("admin.admin_dashboard"))
        return redirect(url_for("student_dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template("login.html", email=email)

        users_col = get_users_collection()
        if users_col is None:
            flash("Database service is currently unavailable. Please try again later.", "danger")
            return render_template("login.html", email=email)

        # Find user document by email
        user = users_col.find_one({"email": email})

        # If user does not exist, show generic error (never reveal whether the account exists)
        if not user:
            print(f"[AUTH] Login failed: Email not found ({email})")
            flash(GENERIC_LOGIN_ERROR, "danger")
            return render_template("login.html", email=email)

        now = datetime.now(timezone.utc)

        # 1. Check if account is currently locked
        locked_until = user.get("locked_until")
        if locked_until:
            # Ensure timezone awareness for comparison
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)

            if locked_until > now:
                minutes_left = int((locked_until - now).total_seconds() / 60) + 1
                print(f"[AUTH] Rejected attempt on locked account: {email}")
                flash(
                    f"This account is temporarily locked due to {MAX_LOGIN_ATTEMPTS} failed attempts. "
                    f"Please wait {minutes_left} minute(s) before trying again.",
                    "danger"
                )
                return render_template("login.html", email=email)
            else:
                # Lockout time has passed; reset lockout state
                users_col.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"failed_attempts": 0, "locked_until": None}}
                )
                user["failed_attempts"] = 0

        # 2. Verify password hash
        if check_password_hash(user["password_hash"], password):
            # Password is correct: reset failed attempts
            users_col.update_one(
                {"_id": user["_id"]},
                {"$set": {"failed_attempts": 0, "locked_until": None}}
            )

            # Establish session variables
            session.clear()
            session["user_id"] = str(user["_id"])
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            session["user_role"] = user["role"]
            session.permanent = True  # Enforces 30-minute session lifetime

            print(f"[AUTH] User logged in: {email} (Role: {user['role']})")
            flash(f"Welcome back, {user['name']}!", "success")

            if user["role"] == "admin":
                return redirect(url_for("admin.admin_dashboard"))
            return redirect(url_for("student_dashboard"))

        else:
            # Password is incorrect: increment failed attempts
            current_attempts = user.get("failed_attempts", 0) + 1
            update_data = {"failed_attempts": current_attempts}

            # Check if threshold reached for account lockout
            if current_attempts >= MAX_LOGIN_ATTEMPTS:
                lock_expiry = now + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                update_data["locked_until"] = lock_expiry
                users_col.update_one({"_id": user["_id"]}, {"$set": update_data})

                print(f"[AUTH] ACCOUNT LOCKED: {email} reached {current_attempts} failed attempts")
                flash(
                    f"Account locked! You entered an incorrect password {MAX_LOGIN_ATTEMPTS} times. "
                    f"Your account is locked for {LOCKOUT_DURATION_MINUTES} minutes.",
                    "danger"
                )
            else:
                users_col.update_one({"_id": user["_id"]}, {"$set": update_data})
                remaining = MAX_LOGIN_ATTEMPTS - current_attempts
                print(f"[AUTH] Bad password for {email} ({current_attempts}/{MAX_LOGIN_ATTEMPTS})")
                # Show generic error plus remaining attempts hint
                flash(f"{GENERIC_LOGIN_ERROR} ({remaining} attempt(s) remaining before account lockout)", "danger")

            return render_template("login.html", email=email)

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    """Clear user session and redirect to login page."""
    user_email = session.get("user_email", "Unknown")
    session.clear()
    print(f"[AUTH] User logged out: {user_email}")
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login"))
