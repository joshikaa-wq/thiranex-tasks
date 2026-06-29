from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
import sqlite3, os, pyotp, qrcode, io, base64, re

app = Flask(__name__)
app.secret_key = os.urandom(24)
bcrypt = Bcrypt(app)

DB = os.path.join(os.path.dirname(__file__), 'instance', 'users.db')

# ── DB SETUP ──────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    UNIQUE NOT NULL,
            email    TEXT    UNIQUE NOT NULL,
            password TEXT    NOT NULL,
            otp_secret TEXT  DEFAULT NULL,
            tfa_enabled INTEGER DEFAULT 0
        )''')
        db.commit()

init_db()

# ── HELPERS ───────────────────────────────────────────────────────────────────
def validate_input(username, email, password):
    errors = []
    if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
        errors.append("Username must be 3-20 chars (letters, numbers, underscore only)")
    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        errors.append("Invalid email address")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")
    if not re.search(r'[A-Z]', password):
        errors.append("Password needs at least one uppercase letter")
    if not re.search(r'[0-9]', password):
        errors.append("Password needs at least one number")
    return errors

def generate_qr(secret, username):
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name="SecureLogin")
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode()

def logged_in():
    return 'user_id' in session

# ── ROUTES ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    if logged_in():
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if logged_in():
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        errors = validate_input(username, email, password)
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('register.html')

        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        try:
            with get_db() as db:
                db.execute('INSERT INTO users (username, email, password) VALUES (?,?,?)',
                           (username, email, hashed))
                db.commit()
            flash('Account created! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if logged_in():
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Basic sanitization — no raw SQL with user input
        if not username or not password:
            flash('All fields required.', 'danger')
            return render_template('login.html')

        with get_db() as db:
            user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user and bcrypt.check_password_hash(user['password'], password):
            if user['tfa_enabled']:
                session['pre_2fa_user'] = user['id']
                return redirect(url_for('verify_2fa'))
            session['user_id']  = user['id']
            session['username'] = user['username']
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    if 'pre_2fa_user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        otp = request.form.get('otp', '').strip()
        with get_db() as db:
            user = db.execute('SELECT * FROM users WHERE id = ?', (session['pre_2fa_user'],)).fetchone()
        totp = pyotp.TOTP(user['otp_secret'])
        if totp.verify(otp):
            session.pop('pre_2fa_user')
            session['user_id']  = user['id']
            session['username'] = user['username']
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid OTP. Try again.', 'danger')
    return render_template('verify_2fa.html')

@app.route('/dashboard')
def dashboard():
    if not logged_in():
        flash('Please login first.', 'warning')
        return redirect(url_for('login'))
    with get_db() as db:
        user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    return render_template('dashboard.html', user=user)

@app.route('/setup-2fa', methods=['GET', 'POST'])
def setup_2fa():
    if not logged_in():
        return redirect(url_for('login'))
    with get_db() as db:
        user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    if request.method == 'POST':
        otp   = request.form.get('otp', '').strip()
        secret = request.form.get('secret', '').strip()
        totp  = pyotp.TOTP(secret)
        if totp.verify(otp):
            with get_db() as db:
                db.execute('UPDATE users SET otp_secret=?, tfa_enabled=1 WHERE id=?',
                           (secret, session['user_id']))
                db.commit()
            flash('2FA enabled successfully! 🎉', 'success')
            return redirect(url_for('dashboard'))
        flash('OTP verification failed. Try again.', 'danger')
        return redirect(url_for('setup_2fa'))

    secret = pyotp.random_base32()
    qr     = generate_qr(secret, user['username'])
    return render_template('setup_2fa.html', secret=secret, qr=qr)

@app.route('/disable-2fa', methods=['POST'])
def disable_2fa():
    if not logged_in():
        return redirect(url_for('login'))
    with get_db() as db:
        db.execute('UPDATE users SET otp_secret=NULL, tfa_enabled=0 WHERE id=?', (session['user_id'],))
        db.commit()
    flash('2FA has been disabled.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
