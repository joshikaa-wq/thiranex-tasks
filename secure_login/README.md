# 🔐 SecureLogin System

A secure web login application built with **Flask**, implementing all industry-standard security practices.

## Features

| Feature | Details |
|---|---|
| 🔑 Password Hashing | bcrypt (via flask-bcrypt) |
| 🛡️ SQL Injection Protection | Parameterized queries only |
| ✅ Input Validation | Regex-based server-side validation |
| 🍪 Session Management | Flask secure sessions with logout |
| 📱 Two-Factor Auth (2FA) | TOTP via pyotp + QR code setup |
| 🌑 Dark UI | Modern dark-themed responsive design |

## Setup & Run

```bash
pip install -r requirements.txt
python app.py
```

Visit: `http://localhost:5000`

## Project Structure

```
secure_login/
├── app.py                  # Main Flask application
├── requirements.txt
├── instance/
│   └── users.db            # SQLite DB (auto-created)
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── setup_2fa.html
│   └── verify_2fa.html
└── static/
    ├── css/style.css
    └── js/main.js
```

## Security Measures

1. **bcrypt hashing** — passwords never stored in plain text
2. **Parameterized SQL queries** — prevents SQL injection
3. **Server-side input validation** — username, email, password rules enforced
4. **Flask session** — server-side session, cleared on logout
5. **TOTP 2FA** — time-based one-time password using RFC 6238

## Tech Stack

- Python 3.x + Flask
- SQLite (via Python sqlite3)
- flask-bcrypt, pyotp, qrcode
- Bootstrap 5 + Font Awesome 6
