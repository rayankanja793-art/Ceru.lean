from flask import Flask, render_template, request, redirect, session, url_for, flash
import time
import random

app = Flask(__name__)

# Secure cookie configuration for handling sessions on cloud deployment platforms
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

# --- YOUR 20 CUSTOM LEAGUE TEAMS ---
LEAGUE_TEAMS = [
    "Roma", "Juventus", "Milaan Reds", "Torino", "Fiorentina",
    "Bologna", "Sassuolo", "Lazio", "Verona", "Atlanta",
    "Monza", "Cremonese", "Leece", "Udinese", "Spenzia",
    "Empoli", "Napoli", "Samdoria", "Salernitana", "Milan Blues"
]

# --- LIVE ENGINE STATE (TIMESTAMP DRIVEN) ---
state = {
    'is_running': True,      # Engine runs by default on deployment startup
    'start_time': time.time()
}

def generate_fixtures_for_round(round_num):
    """Generates a consistent set of matching pairs and scores based on the active round sequence."""
    random.seed(round_num + 999) # Ensures the scores match for all users on the same round
    shuffled_teams = list(LEAGUE_TEAMS)
    random.shuffle(shuffled_teams)
    
    fixtures = []
    for i in range(0, len(shuffled_teams), 2):
        home = shuffled_teams[i]
        away = shuffled_teams[i+1]
        fixtures.append({
            'home': home,
            'away': away,
            'home_score': random.randint(0, 4),
            'away_score': random.randint(0, 4)
        })
    return fixtures

def get_current_match_state():
    """Calculates phase, remaining time, and fixture matchups mathematically using system time."""
    if not state['is_running']:
        return {'phase': 'BETTING', 'time': 60, 'round': 1, 'fixtures': generate_fixtures_for_round(1)}
        
    elapsed = int(time.time() - state['start_time'])
    total_loop_time = 115 # 60 seconds betting window + 55 seconds live play duration
    
    current_round = (elapsed // total_loop_time) + 1
    time_into_current_loop = elapsed % total_loop_time
    
    if time_into_current_loop < 60:
        phase = 'BETTING'
        time_left = 60 - time_into_current_loop
    else:
        phase = 'PLAYING'
        time_left = 115 - time_into_current_loop
        
    fixtures = generate_fixtures_for_round(current_round)
        
    return {
        'phase': phase,
        'time': time_left,
        'round': current_round,
        'fixtures': fixtures
    }

# --- APPLICATION ROUTING SYSTEM ---

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
        flash("Email and password fields are required.")
        return redirect(url_for('login'))
        
    if email in users:
        flash("Email address already registered. Please login instead.")
        return redirect(url_for('login'))
        
    # Standard profile generation with your 100 KSH welcome bonus parameters
    users[email] = {
        'password': password, 
        'balance': 100, 
        'bonus_unlocked': False, 
        'is_admin': False
    }
    
    session['user'] = email
    flash("Welcome! You received a 100 KSH bonus. Deposit 50 KSH or more to unlock it.")
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
    
    # Check if this deposit satisfies the welcome bonus unlocking terms
    if amount >= 50 and not user['bonus_unlocked']:
        user['bonus_unlocked'] = True
        flash("Deposit successful! Your 100 KSH sign-up bonus has been unlocked.")
    else:
        flash(f"Successfully deposited {amount} KSH to account balance.")
        
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    user_profile = users.get(session['user'], {})
    if not user_profile.get('is_admin', False):
        return "Access Denied: Admins Only.", 403
        
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'start':
            state['is_running'] = True
            state['start_time'] = time.time()
        elif action == 'stop':
            state['is_running'] = False
            
    current_state = get_current_match_state()
    current_state['is_running'] = state['is_running']
    return render_template('admin.html', state=current_state)

@app.route('/api/state')
def get_state():
    """Quietly updates real-time screen parameters and active tickers every second via AJAX fetch."""
    current_state = get_current_match_state()
    
    if current_state['phase'] == 'PLAYING':
        if current_state['time'] > 45:
            commentary = ["[05'] Matches kicked off! Pitch conditions look pristine across all venues.", "[14'] Milan Blues pressing deep in enemy territory."]
        elif current_state['time'] > 20:
            commentary = ["[28'] ⚽ GOAL action reported! Front lines breaking through headers.", "[35'] Napoli and Roma locked in intense defensive battles."]
        else:
            commentary = ["[44'] Final minutes of the half. Teams conserving structural formations.", "[45+2'] Halftime whistle blows! Scores locked."]
    else:
        commentary = [f"[System] Round #{current_state['round']} matches archived. Shuffling dynamic boards.", f"[System] Next market window lock sequence incoming in {current_state['time']}s."]

    return {
        'phase': current_state['phase'],
        'time': current_state['time'],
        'round': current_state['round'],
        'fixtures': current_state['fixtures'],
        'logs': commentary
    }

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
