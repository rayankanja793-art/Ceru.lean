from flask import Flask, render_template, request, redirect, session, url_for, flash
import time

app = Flask(__name__)

# Explicit configuration for secure cookie handling on Render
app.config.update(
    SECRET_KEY='swiftpitch_super_secret_key_2026',
    SESSION_COOKIE_SECURE=False,  
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

# --- SIMULATION STATE (TIMESTAMP BASED) ---
state = {
    'is_running': True, # Changed to True by default so you don't even need to click start!
    'start_time': time.time()
}

def get_current_match_state():
    """Calculates the exact match time dynamically using the system clock.
    This guarantees it never freezes on cloud servers like Render."""
    if not state['is_running']:
        return {'phase': 'BETTING', 'time': 60, 'round': 1}
        
    elapsed = int(time.time() - state['start_time'])
    total_loop_time = 115 # 60s betting + 55s playing
    
    current_round = (elapsed // total_loop_time) + 1
    time_into_current_loop = elapsed % total_loop_time
    
    if time_into_current_loop < 60:
        phase = 'BETTING'
        time_left = 60 - time_into_current_loop
    else:
        phase = 'PLAYING'
        time_left = 115 - time_into_current_loop
        
    return {
        'phase': phase,
        'time': time_left,
        'round': current_round
    }

# --- ROUTES ---

@app.route('/')
def index():
    if 'user' not in session or session['user'] not in users:
        return redirect(url_for('login'))
    
    current_user_data = users[session['user']]
    current_state = get_current_match_state()
    return render_template('index.html', state=current_state, user=current_user_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if email in users and users[email]['password'] == password:
            session['user'] = email
            return redirect(url_for('index'))
        else:
            flash("Invalid email or password.")
            return redirect(url_for('login'))
            
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
            state['start_time'] = time.time()
        elif action == 'stop':
            state['is_running'] = False
            
    current_state = get_current_match_state()
    # Add status compatibility for the admin template layout toggle
    current_state['is_running'] = state['is_running']
    return render_template('admin.html', state=current_state)

@app.route('/api/state')
def get_state():
    current_state = get_current_match_state()
    
    if current_state['phase'] == 'PLAYING':
        if current_state['time'] > 45:
            commentary = ["[05'] Match kicked off! Both teams looking sharp.", "[12'] Juventus dictating the tempo early on."]
        elif current_state['time'] > 20:
            commentary = ["[24'] ⚽ GOAL! Juventus takes the lead! 1-0", "[38'] Inter Milan hitting the post on a counter-attack!"]
        else:
            commentary = ["[44'] AC Milan pressing hard before the whistle.", "[45+1'] Halftime whistle blows! Players heading down the tunnel."]
    else:
        commentary = [f"[System] Round #{current_state['round']} match clearing. Next kickoff in {current_state['time']}s.", "[System] Market pools open. Acceptable placement limits active."]

    return {
        'phase': current_state['phase'],
        'time': current_state['time'],
        'round': current_state['round'],
        'logs': commentary
    }

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
