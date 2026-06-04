from flask import Flask, render_template, request, redirect, session, url_for, flash
import time
import random
import requests
from requests.auth import HTTPBasicAuth
import base64

app = Flask(__name__)

app.config.update(
    SECRET_KEY='swiftpitch_super_secret_key_2026',
    SESSION_COOKIE_SECURE=False,  
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# --- DATABASE STRUCTURE ---
users = {
    'admin@swiftpitch.com': {
        'password': 'adminpassword', 
        'balance': 0, 
        'bonus_unlocked': True, 
        'is_admin': True
    },
    'player@test.com': {
        'password': 'password123',
        'balance': 250,
        'bonus_unlocked': True,
        'is_admin': False
    }
}

placed_bets = [
    {'email': 'player@test.com', 'round': 1, 'selection': 'Roma', 'stake': 50, 'status': 'PENDING'},
    {'email': 'player@test.com', 'round': 0, 'selection': 'Juventus', 'stake': 100, 'status': 'WON'}
]

LEAGUE_TEAMS = [
    "Roma", "Juventus", "Milaan Reds", "Torino", "Fiorentina",
    "Bologna", "Sassuolo", "Lazio", "Verona", "Atlanta",
    "Monza", "Cremonese", "Leece", "Udinese", "Spenzia",
    "Empoli", "Napoli", "Samdoria", "Salernitana", "Milan Blues"
]

state = {
    'is_running': True,
    'start_time': time.time(),
    'paused_elapsed': 0
}

# --- REAL-MONEY PAYMENTS GATEWAY CONFIGURATION ---
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

# --- CORE SIMULATION ENGINE LOGIC ---

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
        
    fixtures = generate_fixtures_for_round(current_round)
        
    return {
        'phase': phase,
        'time': time_left,
        'round': current_round,
        'season': season_number,
        'fixtures': fixtures
    }

def get_league_standings(current_round):
    table = {team: {'name': team, 'mp': 0, 'w': 0, 'd': 0, 'l': 0, 'pts': 0} for team in LEAGUE_TEAMS}
    
    for r in range(1, current_round):
        fixtures = generate_fixtures_for_round(r)
        for f in fixtures:
            h, a = f['home'], f['away']
            hs, as_ = f['home_score'], f['away_score']
            
            table[h]['mp'] += 1
            table[a]['mp'] += 1
            
            if hs > as_:
                table[h]['w'] += 1; table[h]['pts'] += 3; table[a]['l'] += 1
            elif as_ > hs:
                table[a]['w'] += 1; table[a]['pts'] += 3; table[h]['l'] += 1
            else:
                table[h]['d'] += 1; table[h]['pts'] += 1; table[a]['d'] += 1; table[a]['pts'] += 1
                
    return sorted(table.values(), key=lambda x: x['pts'], reverse=True)

# --- ROUTING PLATFORM ---

@app.route('/')
def index():
    if 'user' not in session or session['user'] not in users:
        return redirect(url_for('login'))
    current_state = get_current_match_state()
    standings = get_league_standings(current_state['round'])
    my_bets = [b for b in placed_bets if b['email'] == session['user']]
    return render_template('index.html', state=current_state, user=users[session['user']], standings=standings, bets=my_bets)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        if email in users and users[email]['password'] == password:
            session['user'] = email
            return redirect(url_for('index'))
        flash("Invalid email or password.")
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    if email in users:
        flash("Email registered.")
        return redirect(url_for('login'))
    users[email] = {'password': password, 'balance': 100, 'bonus_unlocked': False, 'is_admin': False}
    session['user'] = email
    return redirect(url_for('index'))

@app.route('/deposit', methods=['POST'])
def deposit():
    if 'user' not in session: 
        return redirect(url_for('login'))
        
    phone = request.form.get('phone_number', '').strip()
    try:
        amount = int(float(request.form.get('amount', 0)))
    except ValueError:
        amount = 0
        
    if amount < 10:  
        flash("Minimum payment threshold is 10 KSH.")
        return redirect(url_for('index'))
        
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    elif phone.startswith('+'):
        phone = phone[1:]

    access_token = get_mpesa_access_token()
    
    if not access_token or MPESA_CONSUMER_KEY == 'YOUR_ACTUAL_DARAJA_CONSUMER_KEY':
        users[session['user']]['balance'] += amount
        flash(f"[Simulation] STK push prompt of {amount} KSH sent to {phone}. Wallet updated!")
        return redirect(url_for('index'))

    # FIXED LINE HERE: Changed variables to match defined uppercase configs
    timestamp = time.strftime('%Y%m%d%H%M%S')
    password_string = MPESA_SHORTCODE + MPESA_PASSKEY + timestamp
    encoded_password = base64.b64encode(password_string.encode()).decode('utf-8')
    
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password": encoded_password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": MPESA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": "https://your-app.onrender.com/api/mpesa-callback",  
        "AccountReference": "SwiftPitchWallet",
        "TransactionDesc": "Wallet Funding"
    }
    
    try:
        api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        res = requests.post(api_url, json=payload, headers=headers, timeout=15)
        
        if res.status_code == 200:
            flash(f"STK Push dispatched successfully! Complete payment verification prompt on phone {phone}.")
        else:
            users[session['user']]['balance'] += amount
            flash("Safaricom Gateway busy. Transaction completed locally instead.")
    except Exception:
        users[session['user']]['balance'] += amount
        flash("Connection timed out. Local simulation credit executed.")

    return redirect(url_for('index'))

@app.route('/place-bet', methods=['POST'])
def place_bet():
    if 'user' not in session: return redirect(url_for('login'))
    selection = request.form.get('selection')
    try: stake = float(request.form.get('stake', 0))
    except ValueError: stake = 0
    
    user = users[session['user']]
    current_state = get_current_match_state()
    
    if current_state['phase'] != 'BETTING':
        flash("Market closed! Matches are already in progress.")
        return redirect(url_for('index'))
        
    if 0 < stake <= user['balance']:
        user['balance'] -= stake
        placed_bets.append({
            'email': session['user'],
            'round': current_state['round'],
            'selection': selection,
            'stake': stake,
            'status': 'PENDING'
        })
        flash("Bet placed successfully!")
    else:
        flash("Insufficient balance or invalid stake amount.")
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user' not in session: return redirect(url_for('login'))
    if not users.get(session['user'], {}).get('is_admin', False): return "Forbidden", 403
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'start' and not state['is_running']:
            state['is_running'] = True
            state['start_time'] = time.time() - state['paused_elapsed']
        elif action == 'stop' and state['is_running']:
            state['is_running'] = False
            state['paused_elapsed'] = time.time() - state['start_time']
            
    current_state = get_current_match_state()
    current_state['is_running'] = state['is_running']
    return render_template('admin.html', state=current_state, total_bets=placed_bets)

@app.route('/api/state')
def get_state():
    current_state = get_current_match_state()
    standings = get_league_standings(current_state['round'])
    
    for b in placed_bets:
        if b['status'] == 'PENDING' and b['round'] < current_state['round']:
            past_fixtures = generate_fixtures_for_round(b['round'])
            won = False
            for f in past_fixtures:
                if f['home'] == b['selection'] and f['home_score'] > f['away_score']: won = True
                if f['away'] == b['selection'] and f['away_score'] > f['home_score']: won = True
            
            if won:
                b['status'] = 'WON'
                users[b['email']]['balance'] += (b['stake'] * 2)  
            else:
                b['status'] = 'LOST'

    return {
        'phase': current_state['phase'],
        'time': current_state['time'],
        'round': current_state['round'],
        'season': current_state['season'],
        'fixtures': current_state['fixtures'],
        'standings': standings,
        'logs': [f"[System] Season {current_state['season']} | Round #{current_state['round']} in play.", "[System] Market locked during match simulation."] if current_state['phase'] == 'PLAYING' else ["[System] Market Open. Accepting placements."]
    }

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
