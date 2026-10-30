/**
 * password_strength.js
 * ====================
 * Purpose: Real-time client-side password strength meter, rule checklist, and show/hide toggle.
 * Author: Student Project (Explainable Machine Learning with MongoDB)
 *
 * NOTE FOR VIVA: This script provides immediate visual feedback to improve User Experience (UX).
 * However, the SERVER (validators.py) always re-validates all rules because client-side JS can be disabled.
 */

document.addEventListener("DOMContentLoaded", function () {
    const passwordInput = document.getElementById("password");
    const confirmInput = document.getElementById("confirm_password");
    const nameInput = document.getElementById("name");
    const emailInput = document.getElementById("email");
    const toggleBtn = document.getElementById("togglePasswordBtn");

    const strengthBar = document.getElementById("strengthBar");
    const strengthText = document.getElementById("strengthText");

    // Rule checklist DOM elements
    const ruleLength = document.getElementById("rule-length");
    const ruleUpper = document.getElementById("rule-upper");
    const ruleLower = document.getElementById("rule-lower");
    const ruleNumber = document.getElementById("rule-number");
    const ruleSpecial = document.getElementById("rule-special");
    const ruleNameEmail = document.getElementById("rule-name-email");
    const matchStatus = document.getElementById("matchStatus");

    // 1. Show / Hide Password Toggle
    if (toggleBtn && passwordInput) {
        toggleBtn.addEventListener("click", function () {
            const isPassword = passwordInput.getAttribute("type") === "password";
            const newType = isPassword ? "text" : "password";
            passwordInput.setAttribute("type", newType);
            if (confirmInput) {
                confirmInput.setAttribute("type", newType);
            }
            toggleBtn.innerHTML = isPassword
                ? '<i class="bi bi-eye-slash"></i> Hide'
                : '<i class="bi bi-eye"></i> Show';
        });
    }

    // Helper to toggle rule visual checkmark
    function updateRule(element, isValid) {
        if (!element) return;
        const icon = element.querySelector("i");
        if (isValid) {
            element.classList.add("valid");
            if (icon) {
                icon.className = "bi bi-check-circle-fill text-success";
            }
        } else {
            element.classList.remove("valid");
            if (icon) {
                icon.className = "bi bi-circle text-muted";
            }
        }
    }

    // 2. Evaluate Password Strength on keystroke
    if (passwordInput) {
        passwordInput.addEventListener("input", function () {
            const pwd = passwordInput.value;
            const nameVal = nameInput ? nameInput.value.toLowerCase().trim() : "";
            const emailVal = emailInput ? emailInput.value.toLowerCase().trim() : "";
            const emailHandle = emailVal.includes("@") ? emailVal.split("@")[0] : "";

            // Evaluate individual rules
            const hasLength = pwd.length >= 8;
            const hasUpper = /[A-Z]/.test(pwd);
            const hasLower = /[a-z]/.test(pwd);
            const hasNumber = /[0-9]/.test(pwd);
            const hasSpecial = /[!@#$%^&*(),.?":{}|<>\-_=+/\\~`]/.test(pwd);

            // Check if password contains name or email handle
            let containsNameOrEmail = false;
            if (nameVal && nameVal.length >= 3) {
                const parts = nameVal.split(" ");
                for (const part of parts) {
                    if (part.length >= 3 && pwd.toLowerCase().includes(part)) {
                        containsNameOrEmail = true;
                    }
                }
            }
            if (emailHandle && emailHandle.length >= 3 && pwd.toLowerCase().includes(emailHandle)) {
                containsNameOrEmail = true;
            }
            const isNameEmailClean = !containsNameOrEmail;

            // Update individual checklist items
            updateRule(ruleLength, hasLength);
            updateRule(ruleUpper, hasUpper);
            updateRule(ruleLower, hasLower);
            updateRule(ruleNumber, hasNumber);
            updateRule(ruleSpecial, hasSpecial);
            updateRule(ruleNameEmail, isNameEmailClean && pwd.length > 0);

            // Compute composite score (0 to 6)
            let score = 0;
            if (hasLength) score++;
            if (hasUpper) score++;
            if (hasLower) score++;
            if (hasNumber) score++;
            if (hasSpecial) score++;
            if (isNameEmailClean && pwd.length > 0) score++;

            // Update strength bar visual representation
            if (!strengthBar || !strengthText) return;

            if (pwd.length === 0) {
                strengthBar.className = "strength-bar";
                strengthText.innerText = "Strength: Enter a password";
                strengthText.className = "small text-muted";
            } else if (score <= 3) {
                strengthBar.className = "strength-bar strength-weak";
                strengthText.innerText = "Strength: Weak (Add more character types)";
                strengthText.className = "small text-danger fw-semibold";
            } else if (score <= 5) {
                strengthBar.className = "strength-bar strength-medium";
                strengthText.innerText = "Strength: Medium (Almost there)";
                strengthText.className = "small text-warning fw-semibold";
            } else {
                strengthBar.className = "strength-bar strength-strong";
                strengthText.innerText = "Strength: Strong (All criteria met)";
                strengthText.className = "small text-success fw-bold";
            }

            // Check confirmation match if confirmInput has value
            if (confirmInput && confirmInput.value) {
                checkPasswordMatch();
            }
        });
    }

    // 3. Confirm Password Match Checker
    function checkPasswordMatch() {
        if (!passwordInput || !confirmInput || !matchStatus) return;
        if (confirmInput.value.length === 0) {
            matchStatus.innerText = "";
            return;
        }
        if (passwordInput.value === confirmInput.value) {
            matchStatus.innerHTML = '<span class="text-success"><i class="bi bi-check2-circle"></i> Passwords match</span>';
        } else {
            matchStatus.innerHTML = '<span class="text-danger"><i class="bi bi-x-circle"></i> Passwords do not match</span>';
        }
    }

    if (confirmInput) {
        confirmInput.addEventListener("input", checkPasswordMatch);
    }
});
