# Authentication, Web Security & UI Design
## Comprehensive Viva & Technical Guide

This document is your preparation guide for viva examinations and technical reviews focusing on the **Web Application Architecture**, **Authentication Flow**, **Session Management**, and **Defensive Security Controls**.

---

## 1. End-to-End Authentication & Authorization Flow

```text
[ Browser / Client ]
        |
        |  1. POST /register (name, email, password, confirm_password)
        v
[ Server: validators.py ]
        |  2. Server verifies length, uppercase, lowercase, number, symbol,
        |     blocklist, and ensures password does not contain name/email.
        v
[ Server: auth.py ]
        |  3. Hashes password using PBKDF2-SHA256 with a unique salt.
        |  4. Sets role = "student", failed_attempts = 0, locked_until = None.
        v
[ MongoDB: users collection ]
        |  5. Stores user document with unique index on email.
        |
        |  6. POST /login (email, password)
        v
[ Server: auth.py ]
        |  7. Checks if account is currently locked (locked_until > now).
        |  8. Verifies hash using check_password_hash().
        |     - If FAIL: increments failed_attempts. If attempts >= 5, sets locked_until = now + 15 min.
        |     - If SUCCESS: resets failed_attempts to 0, issues Flask session cookie.
        v
[ Browser Cookie ]
        |  9. Session Cookie stored (HttpOnly, SameSite=Lax, 30 min lifetime).
        |
        | 10. GET /dashboard (Student) or GET /admin (Admin)
        v
[ Route Decorators ]
        - @login_required: checks if user_id in session.
        - @admin_required: checks if session.user_role == 'admin' (otherwise returns 403 Forbidden).
```

---

## 2. Key Security Mechanisms Explained

### A. Why We Hash Passwords (Never Plaintext)
- **The Problem:** If an attacker breaches the database or a backup is leaked, plaintext passwords immediately expose all users. Furthermore, since users frequently reuse passwords across multiple websites, a plaintext leak compromises accounts elsewhere.
- **The Solution:** We use `werkzeug.security.generate_password_hash` with **PBKDF2-SHA256** (Password-Based Key Derivation Function 2).
- **How Hashing Works:**
  1. Hashing is a **one-way mathematical function** ($y = H(x)$); it cannot be reversed.
  2. **Salting:** A random cryptographic salt string is generated for each password before hashing. Even if two students choose the exact same password, their stored hashes will look completely different, preventing precomputed Rainbow Table attacks.
  3. **Work Factor (Key Stretching):** PBKDF2 runs thousands of hash iterations, intentionally slowing down brute-force and dictionary attacks on high-speed GPUs.

### B. What is Cross-Site Request Forgery (CSRF) & How We Prevent It
- **The Attack Scenario:** An authenticated student is logged into the placement portal. In another browser tab, the student visits a malicious website. That website executes a hidden form submission or script targeting `http://127.0.0.1:5000/predict`. The browser automatically attaches the student's session cookie, causing the server to execute the request on the student's behalf.
- **The Defense:** We integrate **Flask-WTF `CSRFProtect`**:
  1. For every active user session, Flask generates a unique, cryptographically signed CSRF token.
  2. Every HTML form embeds this token in a hidden input field:
     ```html
     <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
     ```
  3. When a POST request arrives, `CSRFProtect` verifies that the token submitted inside the request body matches the token stored in the session.
  4. An external attacker site cannot read the student's CSRF token due to the browser's Same-Origin Policy (SOP), so forged requests are immediately rejected with HTTP 400 Bad Request.

### C. Brute-Force Protection via Account Lockout
- **The Threat:** Automated dictionary attacks testing thousands of password guesses per minute.
- **Our Implementation:**
  - In `app/config.py`, we define `MAX_LOGIN_ATTEMPTS = 5` and `LOCKOUT_DURATION_MINUTES = 15`.
  - The `users` collection maintains two fields:
    - `failed_attempts`: Count of consecutive incorrect attempts.
    - `locked_until`: UTC timestamp until which logins are rejected.
  - On the 5th bad attempt, `locked_until` is set to `now + 15 minutes`.
  - Any subsequent login attempt during this window immediately fails with a notification indicating how many minutes remain.
  - Upon a successful login, `failed_attempts` is reset to 0.

### D. Why We Use Generic Error Messages
- **The Vulnerability (User Enumeration):** If the server responds with *"Email does not exist"* when an email is wrong, and *"Incorrect password"* when the password is wrong, an attacker can test a list of employee or student emails to determine exactly which accounts exist on the platform.
- **Our Defense:** Both invalid emails and wrong passwords display the identical message:
  `"Invalid email or password."`
  This denies attackers confirmation of valid email accounts.

### E. Session Cookie Hardening
- **`SESSION_COOKIE_HTTPONLY = True`:**
  Ensures client-side JavaScript (e.g., via a malicious script or browser extension) cannot read `document.cookie`. This prevents session hijacking via Cross-Site Scripting (XSS).
- **`SESSION_COOKIE_SAMESITE = 'Lax'`:**
  Instructs modern browsers not to send the session cookie on cross-site requests, providing defense-in-depth against CSRF.
- **`PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)`:**
  Inactivity timeout ensures that unattended computers automatically terminate active sessions after 30 minutes.

---

## 3. Top 10 Viva Questions on Authentication & Web Security

### Q1: Why did you enforce password rules on the server when you already have JavaScript validation in the browser?
> **Answer:** Client-side JavaScript validation is purely for user experience (UX) to provide instant visual feedback. It can be bypassed completely using tools like curl, Postman, or by disabling JavaScript in browser settings. The server is the true security boundary; all validation rules must be enforced on the server in `validators.py`.

### Q2: Why is storing MD5 or SHA-256 hashes of passwords no longer acceptable?
> **Answer:** MD5 and plain SHA-256 are general-purpose cryptographic hash functions designed to be extremely fast. Modern GPUs can compute billions of MD5 or SHA-256 hashes per second, making offline dictionary attacks trivial. Secure password hashing requires slow, salted, and iterated key-derivation algorithms like PBKDF2, bcrypt, or scrypt.

### Q3: How does the @admin_required decorator prevent privilege escalation?
> **Answer:** Normal users are assigned the `student` role upon registration. The `@admin_required` decorator wraps administrative routes (like `/admin`). Before allowing access, it checks `session.get("user_role") == "admin"`. If a logged-in student attempts to access `/admin`, the decorator intercepts the request and returns an HTTP 403 Forbidden error.

### Q4: How are administrators created if they cannot register through the web UI?
> **Answer:** To prevent unauthorized users from registering as administrators, the `/register` route hardcodes the role to `'student'`. The administrator account is created out-of-band via a secure terminal script, `python create_admin.py`, which requires direct server access.

### Q5: What is the difference between Authentication and Authorization?
> **Answer:**
> - **Authentication (AuthN):** Verifying *who you are* (e.g., checking email and password on `/login`).
> - **Authorization (AuthZ):** Verifying *what you are allowed to do* (e.g., checking if the logged-in user has the `admin` role before allowing access to `/admin`).

### Q6: What does the unique index on `users.email` accomplish in MongoDB?
> **Answer:** It enforces uniqueness at the database engine level. If two registration requests with the same email arrive simultaneously, application-level checks might experience a race condition where both pass. The unique database index guarantees that MongoDB will reject duplicate emails.

### Q7: Why are prediction tips generated using if/else rules instead of the machine learning model?
> **Answer:** Machine learning models are statistical estimators; they do not natively provide actionable, deterministic causal advice. By using rule-based logic (e.g., `if backlogs > 0` or `if coding_score < 70`), we provide transparent, deterministic, and easily explainable guidance directly tied to college placement eligibility rules.

### Q8: What is the risk of constructing MongoDB queries using string concatenation?
> **Answer:** String concatenation creates NoSQL injection vulnerabilities, where special characters or operators (like `$gt` or `$ne`) can alter query logic. In our project, all PyMongo queries pass plain Python dictionaries with sanitized primitive values (e.g., `{"email": email}`), preventing query injection.

### Q9: Why is the secret key stored in `.env` rather than directly in `config.py`?
> **Answer:** Storing secrets in source code files exposes them if the codebase is uploaded to GitHub or shared. By keeping `SECRET_KEY` in `.env` and adding `.env` to `.gitignore`, secrets remain localized to the server environment.

### Q10: How does the application prevent unplaced candidates from having a salary prediction?
> **Answer:** In `predict.py`, the salary regression model is executed *only* if the classification model outputs `placed == 1`. If `placed == 0`, the salary is set to `None`. This matches the business logic that an unplaced student has no job offer, preventing meaningless salary numbers.
