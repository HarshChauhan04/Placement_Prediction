"""
app/validators.py
=================
Purpose: Server-side input validation and security checks for authentication and prediction forms.
Author: Student Project (Explainable Machine Learning with MongoDB)

WHY SERVER-SIDE VALIDATION:
Client-side browser checks (HTML5 required attributes or JavaScript) can easily be bypassed
or disabled by attackers using Postman, curl, or browser dev tools. Therefore, the server
MUST strictly validate and sanitize all incoming parameters before processing.
"""

import re
from app.config import (
    MIN_PASSWORD_LENGTH,
    COMMON_PASSWORDS_BLOCKLIST
)

# Standard email regex pattern
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# Valid engineering branch choices
VALID_BRANCHES = [
    "Computer Science",
    "Information Technology",
    "Electronics",
    "Mechanical",
    "Civil"
]


def validate_email_format(email):
    """
    Check if an email string complies with standard email address formatting.

    Parameters:
        email (str): Email string to check.

    Returns:
        bool: True if valid, False otherwise.
    """
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def check_password_strength(password, user_name="", email=""):
    """
    Verify that a password satisfies all server-side complexity rules.

    Rules enforced:
    1. At least 8 characters in length.
    2. At least one uppercase letter (A-Z).
    3. At least one lowercase letter (a-z).
    4. At least one numeric digit (0-9).
    5. At least one special symbol (!@#$%^&* etc.).
    6. Does not contain the user's name or email username.
    7. Is not found in the common passwords blocklist.

    Parameters:
        password (str): Raw plaintext password.
        user_name (str): Full name of the user to test for obvious patterns.
        email (str): User's email to test for obvious patterns.

    Returns:
        tuple: (is_strong: bool, error_message: str or None)
    """
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."

    if not re.search(r"[A-Z]", password):
        return False, "Password must include at least one uppercase letter (A-Z)."

    if not re.search(r"[a-z]", password):
        return False, "Password must include at least one lowercase letter (a-z)."

    if not re.search(r"[0-9]", password):
        return False, "Password must include at least one number (0-9)."

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_=+/\\~`]", password):
        return False, "Password must include at least one special character (e.g. !@#$%^&*)."

    # Check blocklist of trivially guessed passwords
    if password.lower() in COMMON_PASSWORDS_BLOCKLIST:
        return False, "This password is too common and easily guessed. Please choose a more unique password."

    # Ensure password does not contain parts of user's name (case-insensitive)
    if user_name:
        name_parts = [part.lower() for part in user_name.split() if len(part) >= 3]
        for part in name_parts:
            if part in password.lower():
                return False, "Password must not contain your name."

    # Ensure password does not contain the email prefix (before the @)
    if email and "@" in email:
        email_handle = email.split("@")[0].lower()
        if len(email_handle) >= 3 and email_handle in password.lower():
            return False, "Password must not contain your email username."

    return True, None


def validate_registration_form(name, email, password, confirm_password):
    """
    Validate the full registration submission.

    Parameters:
        name (str): Full name.
        email (str): Email address.
        password (str): Password.
        confirm_password (str): Confirmation password.

    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not name or len(name.strip()) < 2:
        return False, "Please enter your full name (at least 2 characters)."

    if not validate_email_format(email):
        return False, "Please provide a valid email address."

    if password != confirm_password:
        return False, "Password and Confirm Password do not match."

    is_strong, strength_err = check_password_strength(password, user_name=name, email=email)
    if not is_strong:
        return False, strength_err

    return True, None


def validate_prediction_inputs(form_dict):
    """
    Validate and parse numerical input features for placement prediction.

    Parameters:
        form_dict (dict): Dictionary from request.form.

    Returns:
        tuple: (is_valid: bool, error_message: str or None, cleaned_dict: dict or None)
    """
    cleaned = {}
    try:
        # 1. CGPA (5.0 to 10.0)
        cgpa = float(form_dict.get("cgpa", -1))
        if not (5.0 <= cgpa <= 10.0):
            return False, "CGPA must be between 5.0 and 10.0.", None
        cleaned["cgpa"] = round(cgpa, 2)

        # 2. 10th Board Percentage (40.0 to 100.0)
        tenth = float(form_dict.get("10th_percent", -1))
        if not (40.0 <= tenth <= 100.0):
            return False, "10th percentage must be between 40% and 100%.", None
        cleaned["10th_percent"] = round(tenth, 1)

        # 3. 12th Board Percentage (40.0 to 100.0)
        twelfth = float(form_dict.get("12th_percent", -1))
        if not (40.0 <= twelfth <= 100.0):
            return False, "12th percentage must be between 40% and 100%.", None
        cleaned["12th_percent"] = round(twelfth, 1)

        # 4. Internships (0 to 10)
        internships = int(form_dict.get("internships", -1))
        if not (0 <= internships <= 10):
            return False, "Internships count must be between 0 and 10.", None
        cleaned["internships"] = internships

        # 5. Projects (0 to 15)
        projects = int(form_dict.get("projects", -1))
        if not (0 <= projects <= 15):
            return False, "Projects count must be between 0 and 15.", None
        cleaned["projects"] = projects

        # 6. Certifications (0 to 15)
        certifications = int(form_dict.get("certifications", -1))
        if not (0 <= certifications <= 15):
            return False, "Certifications count must be between 0 and 15.", None
        cleaned["certifications"] = certifications

        # 7. Coding Score (0.0 to 100.0)
        coding = float(form_dict.get("coding_score", -1))
        if not (0.0 <= coding <= 100.0):
            return False, "Coding score must be between 0 and 100.", None
        cleaned["coding_score"] = round(coding, 1)

        # 8. Communication Score (0.0 to 100.0)
        comm = float(form_dict.get("communication_score", -1))
        if not (0.0 <= comm <= 100.0):
            return False, "Communication score must be between 0 and 100.", None
        cleaned["communication_score"] = round(comm, 1)

        # 9. Backlogs (0 to 10)
        backlogs = int(form_dict.get("backlogs", -1))
        if not (0 <= backlogs <= 10):
            return False, "Backlogs count must be between 0 and 10.", None
        cleaned["backlogs"] = backlogs

        # 10. Branch selection
        branch = form_dict.get("branch", "").strip()
        if branch not in VALID_BRANCHES:
            return False, f"Please select a valid branch from: {', '.join(VALID_BRANCHES)}.", None
        cleaned["branch"] = branch

        return True, None, cleaned

    except (ValueError, TypeError):
        return False, "Invalid numeric input. Please verify that all scores and counts are valid numbers.", None
