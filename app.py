from flask import Flask, render_template, request, redirect, session, url_for, flash
import time
import random

app = Flask(__name__)

app.config.update(
    SECRET_KEY='swiftpitch_super_secret_key_2026',
    SESSION_COOKIE_SECURE=False,  
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# --- DATA STORAGE ---
users = {
    'admin@swiftpitch.com': {
        'password': 'adminpassword', 
        'balance': 0, 
        'bonus_unlocked': True, 
        'is_admin': True
    }
}

LEAGUE_TEAMS = [
    "Roma", "Juventus", "Milaan Reds", "Torino", "Fiorentina",
    "Bologna", "Sassuolo", "Lazio", "Verona", "Atlanta",
    "Monza", "Cremonese", "Leece", "Udinese", "Spenzia",
    "Empoli", "Napoli", "Samdoria", "Salernitana", "Milan Blues"
]

state = {
    'is_running': True,
    'start_time': time.time()
}

def generate_fixtures_for_round(round_num):
    random.seed(round_num + 999) 
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
    if not state['is_running']:
        return {'phase': 'BETTING', 'time': 60, 'round': 1, 'fixtures': generate_fixtures_for_round(1)}
        
    elapsed = int(time.time() - state['start_time'])
    total_loop_time = 115 
    
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

def get_league_standings(current_round, phase):
    """Calculates Wins, Draws, Losses, and Points accumulatively for all teams."""
    # Initialize table dictionary structures
    table = {team: {'name': team, 'mp': 0, 'w': 0, 'd': 0, 'l': 0, 'pts': 0} for team in LEAGUE_TEAMS}
    
    # Check history up to the current running sequence
    # If we are in PLAYING phase, we don't add current round scores until the match finishes (BETTING phase)
    max_completed_round = current_round if phase == 'BETTING' else current_round
    
    for r in range(1, max_completed_round):
        fixtures = generate_fixtures_for_round(r)
        for f in fixtures:
            h, a = f['home'], f['away']
            hs, as_ = f['home_score'], f['away_score']
            
            table[h]['mp'] += 1
            table[a]['mp'] += 1
            
            if hs > as_:
                table[h]['w'] += 1
                table[h]['pts'] += 3
                table[a]['l'] += 1
            elif as_ > hs:
                table[a]['w'] += 1
                table[a]['pts'] += 3
                table[h]['l'] += 1
            else:
                table[h]['d'] += 1
                table[h]['pts'] += 1
                table[a]['d'] += 1
                table[a]['pts'] += 1
                
    # Sort teams by total points highest to lowest
    sorted_table = sorted(table.values(), key=lambda x: x['pts'], reverse=True)
    return sorted_table

# --- ROUTES ---

@app.route('/')
def index():
    if 'user' not in session or session['user'] not in users:
        return redirect(url_for('login'))
    current_user_data = users[session['user']]
    current_state = get_current_match_state()
    standings = get_league_standings(current_state['round'], current_state['phase'])
    return render_template('index.html', state=current_state, user=current_user_data, standings=standings)

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
        flash("Fields required.")
        return redirect(url_for('login'))
    if email in users:
        flash("Email registered.")
        return redirect(url_for('login'))
    users[email] = {'password': password, 'balance': 100, 'bonus_unlocked': False, 'is_admin': False}
    session['user'] = email
    return redirect(url_for('index'))

@app.route('/deposit', methods=['POST'])
def deposit():
    if 'user' not in session: return redirect(url_for('login'))
    try: amount = float(request.form.get('amount', 0))
    except ValueError: amount = 0
    if amount < 10: return redirect(url_for('index'))
    user = users[session['user']]
    user['balance'] += amount
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user' not in session: return redirect(url_for('login'))
    user_profile = users.get(session['user'], {})
    if not user_profile.get('is_admin', False): return "Forbidden", 403
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'start': state['is_running'] = True; state['start_time'] = time.time()
        elif action == 'stop': state['is_running'] = False
    current_state = get_current_match_state()
    current_state['is_running'] = state['is_running']
    return render_template('admin.html', state=current_state)

@app.route('/api/state')
def get_state():
    current_state = get_current_match_state()
    standings = get_league_standings(current_state['round'], current_state['phase'])
    
    if current_state['phase'] == 'PLAYING':
        commentary = ["[05'] Kickoff completed! Live parameters synchronized.", "[30'] Dynamic action underway across the grounds."]
    else:
        commentary = [f"[System] Round #{current_state['round']} data processed.", "[System] Market pools open for placements."]

    return {
        'phase': current_state['phase'],
        'time': current_state['time'],
        'round': current_state['round'],
        'fixtures': current_state['fixtures'],
        'logs': commentary,
        'standings': standings
    }

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
