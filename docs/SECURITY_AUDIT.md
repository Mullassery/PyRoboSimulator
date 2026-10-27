# Security Vulnerability Audit - pyrobosimulator

**Audit Date:** 2026-10-27
**Repository:** /Users/georgimullassery/Desktop/Projects/pyrobosimulator
**Total Findings:** 22

## Summary
- **Critical:** 17
- **Medium:** 5

## Findings

### 1. [Critical] Command Injection
- **File:** backend/htmlcov/coverage_html_cb_15cffcd0.js:236
- **Description:** exec()
- **Evidence (Line):** `const match = /\.([0-9]+)/.exec(cell.textContent);`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 2. [Critical] Command Injection
- **File:** backend/htmlcov/coverage_html_cb_54cfdca1.js:274
- **Description:** exec()
- **Evidence (Line):** `const match = /\.([0-9]+)/.exec(cell.textContent);`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 3. [Critical] Command Injection
- **File:** backend/htmlcov/coverage_html_cb_6fb7b396.js:234
- **Description:** exec()
- **Evidence (Line):** `const match = /\.([0-9]+)/.exec(cell.textContent);`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 4. [Critical] Command Injection
- **File:** backend/htmlcov/coverage_html_cb_dd2e7eb5.js:236
- **Description:** exec()
- **Evidence (Line):** `const match = /\.([0-9]+)/.exec(cell.textContent);`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 5. [Critical] Hardcoded Secret
- **File:** backend/k8s/deployment.yaml:37
- **Description:** Secret Key Assignment detected
- **Evidence (Line):** `SECRET_KEY: "your-super-secret-key-change-in-production"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 6. [Critical] Hardcoded Secret
- **File:** backend/k8s/postgres.yaml:115
- **Description:** Password Assignment detected
- **Evidence (Line):** `#     --from-literal=password="$(openssl rand -base64 32)"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 7. [Critical] Hardcoded Secret
- **File:** backend/tests/test_api_integration.py:34
- **Description:** Password Assignment detected
- **Evidence (Line):** `password = "SecurePassword123456"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 8. [Critical] Hardcoded Secret
- **File:** backend/tests/test_api_integration.py:54
- **Description:** Password Assignment detected
- **Evidence (Line):** `password = "SecurePassword123456"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 9. [Critical] Hardcoded Secret
- **File:** backend/tests/test_api_integration.py:77
- **Description:** Password Assignment detected
- **Evidence (Line):** `password = "SecurePassword123456"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 10. [Critical] Hardcoded Secret
- **File:** backend/tests/test_auth.py:11
- **Description:** Password Assignment detected
- **Evidence (Line):** `password = "test_password_123"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 11. [Critical] Hardcoded Secret
- **File:** backend/tests/test_auth.py:19
- **Description:** Password Assignment detected
- **Evidence (Line):** `password = "test_password_123"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 12. [Critical] Hardcoded Secret
- **File:** backend/tests/test_auth.py:26
- **Description:** Password Assignment detected
- **Evidence (Line):** `password = "correct_password"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 13. [Critical] Hardcoded Secret
- **File:** backend/tests/test_auth.py:27
- **Description:** Password Assignment detected
- **Evidence (Line):** `wrong_password = "wrong_password"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 14. [Critical] Hardcoded Secret
- **File:** backend/tests/test_auth.py:72
- **Description:** Password Assignment detected
- **Evidence (Line):** `password = "test_password"`
- **Exploit Scenario:** Attacker could extract credentials and gain unauthorized access
- **Fix Recommendation:** Move secrets to environment variables or secret manager, rotate compromised credentials
- **Confidence:** High

### 15. [Critical] Command Injection
- **File:** backend/tests/test_simulation_engine.py:276
- **Description:** eval()
- **Evidence (Line):** `def test_agent_state_retrieval(self) -> None:`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 16. [Critical] Command Injection
- **File:** backend/tests/test_trajectories.py:340
- **Description:** eval()
- **Evidence (Line):** `def test_large_trajectory_retrieval(self):`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 17. [Critical] Command Injection
- **File:** htmlcov/coverage_html_cb_dd2e7eb5.js:236
- **Description:** exec()
- **Evidence (Line):** `const match = /\.([0-9]+)/.exec(cell.textContent);`
- **Exploit Scenario:** Attacker could execute arbitrary system commands
- **Fix Recommendation:** Avoid shell execution, use subprocess with shell=False and list args
- **Confidence:** High

### 18. [Medium] Weak Cryptography
- **File:** backend/.mypy_cache/3.10/anthropic/_base_client.data.json:1
- **Description:** non-crypto random for tokens
- **Evidence (Line):** `{".class":"MypyFile","_fullname":"anthropic._base_client","future_import_flags":["annotations"],"is_`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 19. [Medium] Weak Cryptography
- **File:** backend/.mypy_cache/3.10/hashlib.data.json:1
- **Description:** Weak hash algorithm
- **Evidence (Line):** `{".class":"MypyFile","_fullname":"hashlib","future_import_flags":[],"is_partial_stub_package":false,`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 20. [Medium] Weak Cryptography
- **File:** backend/.mypy_cache/3.10/hashlib.data.json:1
- **Description:** Weak hash algorithm
- **Evidence (Line):** `{".class":"MypyFile","_fullname":"hashlib","future_import_flags":[],"is_partial_stub_package":false,`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 21. [Medium] Weak Cryptography
- **File:** docs/archive/PERFORMANCE_OPTIMIZATION_PLAYBOOK.md:301
- **Description:** MD5 usage
- **Evidence (Line):** `return hashlib.md5(key_str.encode()).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High

### 22. [Medium] Weak Cryptography
- **File:** docs/archive/PERFORMANCE_OPTIMIZATION_PLAYBOOK.md:301
- **Description:** Weak hash algorithm
- **Evidence (Line):** `return hashlib.md5(key_str.encode()).hexdigest()`
- **Exploit Scenario:** Weak algorithms vulnerable to collision/brute force attacks
- **Fix Recommendation:** Use modern algorithms (SHA-256+, bcrypt/argon2 for passwords, secrets module for tokens)
- **Confidence:** High
