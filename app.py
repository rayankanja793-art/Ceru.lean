from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import time
import random
import requests
from requests.auth import HTTPBasicAuth

app = Flask(__name__)

# --- SECURE CONFIGURATION SYSTEM ---
app.config.update(
    SECRET_KEY='swiftpitch_super_secret_key_2026',
    SESSION_COOKIE_SECURE=False,  # Set to True if using HTTPS production ssl
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# --- IN-MEMORY DATABASE STORAGE ---
users = {
    'admin@swiftpitch.com': {
        'password': 'adminpassword', 
        'balance': 0.0, 
        'bonus_unlocked': True, 
        'is_admin': True
    },
    'player@test.com': {
        'password': 'password123',
        'balance': 1000.0,
        'bonus_unlocked': True,
        'is_admin': False
    }
}

placed_bets = []

# --- SPORTSBOOK COMPETITIONS SQUADS DATA ---
ITALIAN_TEAMS = [
    "Roma", "Juventus", "Milaan Reds", "Torino", "Fiorentina",
    "Bologna", "Sassuolo", "Lazio", "Verona", "Atlanta",
    "Monza", "Cremonese", "Leece", "Udinese", "Spenzia",
    "Empoli", "Napoli", "Samdoria", "Salernitana", "Milan Blues"
]

ENGLISH_TEAMS = [
    "Manchester blue", "spurs", "A.Villa", "London blues", "Manchester red",
    "New castle", "Everton", "Bournemouth", "N. forrest", "Brighton",
    "London reds", "Brentford", "Wolves", "west Ham", "Southampton",
    "Fulham", "Liverpool", "C.Palace", "Leicester", "Leeds"
]

state = {
    'is_running': True,
    'start_time': time.time(),
    'paused_elapsed': 0,
    'company_balance': 500000.0  
}

# --- LUCKY AVIATOR CRASH ENGINE CONFIGURATION ---
aviator_game = {
    'round_id': 1,
    'phase': 'BETTING',      # Phasing states: BETTING, FLYING, CRASHED
    'phase_start_time': time.time(),
    'betting_duration': 10,   # Seconds allowed for players to mount stakes
    'crash_multiplier': 2.50, # Pre-calculated mathematical hard crash limit
    'active_stakes': {}       # Holds running stakes: account_email -> float_stake
}

# --- REAL-MONEY PAYMENTS GATEWAY INITIALIZATION PARAMETERS ---
MPESA_CONSUMER_KEY = 'YOUR_ACTUAL_DARAJA_CONSUMER_KEY'
MPESA_CONSUMER_SECRET = 'YOUR_ACTUAL_DARAJA_CONSUMER_SECRET'
MPESA_SHORTCODE = '174379'  
MPESA_PASSKEY = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'

def get_mpesa_access_token():
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    try:
        response = requests.get(api_url, auth=HTTPBasicAuth(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET), timeout=10)
        if response.status_code == 200:
            return response.json().get('access_token')
    except Exception:
        pass
    return None

# --- AVIATOR ENGINE ALGORITHMS ---

def generate_provably_fair_crash_point():
    """Generates a bounded multiplier curve using a 3% instant-house loss threshold."""
    if random.random() < 0.03:
        return 1.00  # Instant crash upon takeoff
    
    scale_factor = 100
    random_weight = random.randint(1, 100)
    generated_point = max(1.01, round((scale_factor / random_weight) * random.uniform(0.85, 1.15), 2))
    return generated_point

def update_aviator_loop():
    """Core state machine updater driving the real-time background parameters."""
    now = time.time()
    elapsed = now - aviator_game['phase_start_time']
    
    if aviator_game['phase'] == 'BETTING':
        if elapsed >= aviator_game['betting_duration']:
            aviator_game['phase'] = 'FLYING'
            aviator_game['phase_start_time'] = now
            aviator_game['crash_multiplier'] = generate_provably_fair_crash_point()
            
    elif aviator_game['phase'] == 'FLYING':
        # Exponential curve growth: 1.00 + (t^1.3) * 0.08
        current_mult = 1.00 + (elapsed ** 1.3) * 0.08
        
        if current_mult >= aviator_game['crash_multiplier']:
            aviator_game['phase'] = 'CRASHED'
            aviator_game['phase_start_time'] = now
            
            # House retains stakes of players who failed to cash out in time
            for email, stake in aviator_game['active_stakes'].items():
                state['company_balance'] += stake
            aviator_game['active_stakes'] = {}
            
    elif aviator_game['phase'] == 'CRASHED':
        if elapsed >= 4:  # Provide a 4-second downtime before launching next round
            aviator_game['phase'] = 'BETTING'
            aviator_game['phase_start_time'] = now
            aviator_game['round_id'] += 1

# --- VIRTUAL FOOTBALL SCHEDULING & LOGIC MATRICES ---

def generate_fixtures_for_round(round_num, team_list, seed_offset):
    random.seed(round_num + seed_offset) 
    shuffled_teams = list(team_list)
    random.shuffle(shuffled_teams)
    
    fixtures = []
    for i in range(0, len(shuffled_teams), 2):
        home = shuffled_teams[i]
        away = shuffled_teams[i+1]
        
        home_odds = round(random.uniform(1.30, 4.50), 2)
        draw_odds = round(random.uniform(2.60, 3.80), 2)
        away_odds = round(random.uniform(1.40, 5.00), 2)
        
        fixtures.append({
            'id': f"fix_{round_num}_{i}_{seed_offset}",
            'home': home,
            'away': away,
            'home_score': random.randint(0, 4),
            'away_score': random.randint(0, 4),
            'odds': {
                'HOME': home_odds,
                'DRAW': draw_odds,
                'AWAY': away_odds
            }
        })
    return fixtures

def get_current_match_state():
    total_loop_time = 115  
    TOTAL_ROUNDS_IN_SEASON = 19  
    
    if not state['is_running']:
        elapsed = int(state['paused_elapsed'])
    else:
        elapsed = int(time.time() - state['start_time'])
        
    total_season_time = total_loop_time * TOTAL_ROUNDS_IN_SEASON
    season_number = (elapsed // total_season_time) + 1
    time_into_current_season = elapsed % total_season_time
    
    current_round = (time_into_current_season // total_loop_time) + 1
    time_into_current_loop = time_into_current_season % total_loop_time
    
    if time_into_current_loop < 60:
        phase = 'BETTING'
        time_left = 60 - time_into_current_loop
    else:
        phase = 'PLAYING'
        time_left = 115 - time_into_current_loop
        
    italian_fixtures = generate_fixtures_for_round(current_round, ITALIAN_TEAMS, 111)
    english_fixtures = generate_fixtures_for_round(current_round, ENGLISH_TEAMS, 222)
        
    return {
        'phase': phase,
        'time': time_left,
        'time_into_loop': time_into_current_loop,
        'round': current_round,
        'season': season_number,
        'italian_fixtures': italian_fixtures,
        'english_fixtures': english_fixtures
    }

def get_league_standings(current_round, teams_list, seed_offset):
    table = {team: {'name': team, 'mp': 0, 'w': 0, 'd': 0, 'l': 0, 'pts': 0} for team in teams_list}
    for r in range(1, current_round):
        fixtures = generate_fixtures_for_round(r, teams_list, seed_offset)
        for f in fixtures:
            h, a = f['home'], f['away']
            hs, as_ = f['home_score'], f['away_score']
            table[h]['mp'] += 1; table[a]['mp'] += 1
            if hs > as_:
                table[h]['w'] += 1; table[h]['pts'] += 3; table[a]['l'] += 1
            elif as_ > hs:
                table[a]['w'] += 1; table[a]['pts'] += 3; table[h]['l'] += 1
            else:
                table[h]['d'] += 1; table[h]['pts'] += 1; table[a]['d'] += 1; table[a]['pts'] += 1
                
    return sorted(table.values(), key=lambda x: x['pts'], reverse=True)

# --- CONTROLLER ROUTING HANDLERS ---

@app.route('/')
def index():
    if 'user' not in session or session['user'] not in users:
        session.clear()
        return redirect(url_for('login'))
        
    try:
        current_state = get_current_match_state()
        return render_template('index.html', state=current_state, user=users[session['user']])
    except Exception:
        session.clear()
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        action = request.form.get('auth_action')
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if action == 'signin':
            if email in users and users[email]['password'] == password:
                session['user'] = email
                return redirect(url_for('index'))
            flash("Invalid email or password.")
            
        elif action == 'signup':
            if email in users:
                flash("An account with that email already exists.")
            elif len(email) < 5 or len(password) < 4:
                flash("Please enter a valid email and password (min 4 characters).")
            else:
                # Add new player with 1,000 KSH registration starting bonus
                users[email] = {
                    'password': password,
                    'balance': 1000.0,
                    'bonus_unlocked': True,
                    'is_admin': False
                }
                session['user'] = email
                return redirect(url_for('index'))
                
    return render_template('login.html') if False else '''
    <body style="background:#0b1118; color:white; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; margin:0; flex-direction:column;">
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            {% for msg in messages %}
              <div style="background:#ff3333; color:white; padding:10px 20px; border-radius:4px; margin-bottom:15px; font-weight:bold;">
                 ⚠️ {{ msg }}
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <div id="signin-card" style="background:#121b26; padding:30px; border-radius:8px; border:1px solid #1c2a39; width:
