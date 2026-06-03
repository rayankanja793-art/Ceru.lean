from flask import Flask, render_template, request, redirect, session, url_for, flash
import threading
import time

app = Flask(__name__)

# CRITICAL FIX: Explicitly configuration for secure cookie handling on Render
app.config.update(
    SECRET_KEY='swiftpitch_super_secret_key_2026',
    SESSION_COOKIE_SECURE=False,  # Set to True in production with HTTPS if needed
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# --- DATA STORAGE (Mock Database) ---
users = {
    'admin@swiftpitch.com': {
        'password': 'adminpassword', 
        'balance': 0, 
        'bonus_unlocked': True, 
        'is_admin': True
    }
}
bets = [] 

# --- SIMULATION STATE ---
state = {
    'phase': 'BETTING',
    'time': 60,
    'is_running': False,
    'round': 1
}

def simulation_engine():
    while True:
        if state['is_running']:
            time.sleep(1)
            state['time'] -= 1
            if state['time'] <= 0:
                if state['phase'] == 'BETTING':
                    state['phase'] = 'PLAYING'
                    state['time'] = 55
                else:
                    state['phase'] = 'BETTING'
                    state['time'] = 60
                    state['round'] += 1
        else:
            time.sleep(1)

# Start background thread
threading.Thread(target=simulation_engine, daemon=True).start()

# --- ROUTES ---

@app.route('/')
def index():
    # If user session is empty or missing, bounce them cleanly to login page
    if 'user' not in session or session['user'] not in users:
        return redirect(url_for('login'))
    
    current_user_data = users[session['user']]
    return render_template('index.html', state=state, user=current_user_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        # Simple authentication check
        if email in users and users[email]['password'] == password:
            session['user'] = email
            return redirect(url_for('index'))
        else:
            flash("Invalid email or password.")
            return redirect(url_for('login'))
            
    # GET request renders the page cleanly now
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    
    if not email or not password:
        flash("Email and password are required.")
        return redirect(url_for('login'))
        
    if email in users:
        flash("Email already registered. Please login.")
        return redirect(url_for('login'))
        
    # Create new account with 100 KSH locked bonus
    users[email] = {
        'password': password, 
        'balance': 100, 
        'bonus_unlocked': False, 
        'is_admin': False
    }
    
    session['user'] = email
    flash("Welcome! You received 100 KSH bonus. Deposit 50 KSH to unlock it.")
    return redirect(url_for('index'))

@app.route('/deposit', methods=['POST'])
def deposit():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    try:
        amount = float(request.form.get('amount', 0))
    except ValueError:
        amount = 0
        
    if amount < 10:
        flash("Minimum deposit is 10 Bob.")
        return redirect(url_for('index'))
        
    user = users[session['user']]
    user['balance'] += amount
    
    if amount >= 50 and not user['bonus_unlocked']:
        user['bonus_unlocked'] = True
        flash("Deposit successful! Your 100 KSH bonus has been unlocked.")
    else:
        flash(f"Successfully deposited {amount} KSH.")
        
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    user_profile = users.get(session['user'], {})
    if not user_profile.get('is_admin', False):
        return "Access Denied: Admins Only", 403
        
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'start':
            state['is_running'] = True
        elif action == 'stop':
            state['is_running'] = False
            
    return render_template('admin.html', state=state)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
