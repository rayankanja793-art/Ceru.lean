from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
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
        'balance': 1000,
        'bonus_unlocked': True,
        'is_admin': False
    }
}

# Placed bets now look like: {'email':..., 'round':..., 'selections': [{'home': 'Roma', 'away': 'Juventus', 'market': 'HOME', 'odds': 1.85}], 'stake': 100, 'total_odds': 1.85, 'status': 'PENDING'}
placed_bets = []

LEAGUE_TEAMS = [
    "Roma", "Juventus", "Milaan Reds", "Torino", "Fiorentina",
    "Bologna", "Sassuolo", "Lazio", "Verona", "Atlanta",
    "Monza", "Cremonese", "Leece", "Udinese", "Spenzia",
    "Empoli", "Napoli", "Samdoria", "Salernitana", "Milan Blues"
]

state = {
    'is_running': True,
    'start_time': time.time(),
    'paused_elapsed': 0,
    'company_balance': 500000.0  
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
    """Generates consistent pairs, virtual odds, and scores for any given round."""
    # Build unique seed specifically for odds generation
    random.seed(round_num + 999) 
    shuffled_teams = list(LEAGUE_TEAMS)
    random.shuffle(shuffled_teams)
    
    fixtures = []
    for i in range(0, len(shuffled_teams), 2):
        home = shuffled_teams[i]
        away = shuffled_teams[i+1]
        
        # Deterministic generation of realistic decimal odds
        home_odds = round(random.uniform(1.30, 4.50), 2)
        draw_odds = round(random.uniform(2.60, 3.80), 2)
        away_odds = round(random.uniform(1.40, 5.00), 2)
        
        fixtures.append({
            'id': f"fix_{round_num}_{i}",
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
            table[h]['mp'] += 1; table[a]['mp'] += 1
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
    users[email] = {'password': password, 'balance': 250, 'bonus_unlocked': False, 'is_admin': False}
    session['user'] = email
    return redirect(url_for('index'))

@app.route('/deposit', methods=['POST'])
def deposit():
    if 'user' not in session: return redirect(url_for('login'))
    phone = request.form.get('phone_number', '').strip()
    try: amount = int(float(request.form.get('amount', 0)))
    except ValueError: amount = 0
        
    if amount < 10:  
        flash("Minimum payment threshold is 10 KSH.")
        return redirect(url_for('index'))
        
    if phone.startswith('0'): phone = '254' + phone[1:]
    elif phone.startswith('+'): phone = phone[1:]

    access_token = get_mpesa_access_token()
    if not access_token or MPESA_CONSUMER_KEY == 'YOUR_ACTUAL_DARAJA_CONSUMER_KEY':
        users[session['user']]['balance'] += amount
        flash(f"[Simulation] STK push prompt of {amount} KSH sent to {phone}. Wallet updated!")
        return redirect(url_for('index'))

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
            flash(f"STK Push dispatched successfully! Complete verification prompt on phone {phone}.")
        else:
            users[session['user']]['balance'] += amount
            flash("Safaricom Gateway busy. Transaction completed locally instead.")
    except Exception:
        users[session['user']]['balance'] += amount
        flash("Connection timed out. Local simulation credit executed.")
    return redirect(url_for('index'))

@app.route('/place-multibet', methods=['POST'])
def place_multibet():
    """Processes a single or multi-leg structural bet ticket from the coupon frontend slip."""
    if 'user' not in session: return jsonify({'success': False, 'message': 'Session expired.'}), 401
    
    current_state = get_current_match_state()
    if current_state['phase'] != 'BETTING':
        return jsonify({'success': False, 'message': 'Market closed! Matches are already in play.'}), 400
        
    data = request.get_json() or {}
    selections = data.get('selections', []) # List of maps containing match details
    try: stake = float(data.get('stake', 0))
    except ValueError: stake = 0
    
    if stake < 10:
        return jsonify({'success': False, 'message': 'Minimum stake is 10 KSH.'}), 400
        
    user = users[session['user']]
    if user['balance'] < stake:
        return jsonify({'success': False, 'message': 'Insufficient account balance.'}), 400
        
    if not selections:
        return jsonify({'success': False, 'message': 'Your betslip coupon is completely empty.'}), 400

    # Cross-reference odds against server-side fixtures to completely stop client-side hacking
    current_fixtures = {f['id']: f for f in current_state['fixtures']}
    validated_selections = []
    accumulated_odds = 1.0
    
    for sel in selections:
        fix_id = sel.get('fixture_id')
        market = sel.get('market') # 'HOME', 'DRAW', 'AWAY'
        
        if fix_id not in current_fixtures:
            return jsonify({'success': False, 'message': 'Invalid match selection found.'}), 400
            
        fixture = current_fixtures[fix_id]
        if market not in ['HOME', 'DRAW', 'AWAY']:
            return jsonify({'success': False, 'message': 'Invalid market option choice.'}), 400
            
        market_odds = fixture['odds'][market]
        accum
