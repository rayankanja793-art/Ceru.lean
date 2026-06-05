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

# --- DATABASE LOGIC ---
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

placed_bets = []

# --- LEAGUE SQUADS DATA ---
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

# --- ENGINE CALCULATION MATRICES ---

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
        
    # Generate both lanes concurrently using separate seed indexes
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

def generate_live_commentary(fixtures_ita, fixtures_eng, time_into_loop, round_num):
    random.seed(time_into_loop + round_num)
    
    # Merge both match coupons to allow the AI commentator to watch both lanes
    all_fixtures = fixtures_ita + fixtures_eng
    focus_match = random.choice(all_fixtures)
    
    home = focus_match['home']
    away = focus_match['away']
    h_score = focus_match['home_score']
    a_score = focus_match['away_score']
    
    playing_second = time_into_loop - 60
    match_minute = int((playing_second / 55.0) * 90)
    if match_minute < 1: match_minute = 1
    if match_minute > 90: match_minute = 90

    goal_commentary = [
        f"🎙️ GOOOAAAL! Incredible scenes here! {home} breaks through the defensive wall!",
        f"🎙️ BALL IN THE NET! A masterclass finish from the {away} forward line!",
        f"🎙️ GOAL! The keeper had absolutely no chance with that powerful strike!",
        f"🎙️ UNBELIEVABLE GOAL! The stadium erupts as {home} clinical volley finds the top corner!"
    ]
    
    midfield_commentary = [
        f"🎙️ [{match_minute}'] Tactical battle ongoing in midfield between {home} and {away}.",
        f"🎙️ [{match_minute}'] {home} is maintaining possession nicely, looking for a crossing opportunity.",
        f"🎙️ [{match_minute}'] Crucial sliding tackle intercept from the {away} central defensive midfielder!",
        f"🎙️ [{match_minute}'] High intensity pressure here as {away} presses deep up the wings.",
        f"🎙️ [{match_minute}'] {home} earns a corner kick after a deflected cross over the back line.",
        f"🎙️ [{match_minute}'] Yellow card! Defending player penalized for an aggressive tackle.",
        f"🎙️ [{match_minute}'] SPECTACULAR SAVE! The goalkeeper dives wide to deny {away} a clean opener!"
    ]
    
    if (h_score > 0 or a_score > 0) and random.random() > 0.65:
        return f"[{match_minute}'] " + random.choice(goal_commentary) + f" ({home} {h_score} - {a_score} {away})"
    
    return random.choice(midfield_commentary)

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

# --- CONTROLLER ROUTING ---

@app.route('/')
def index():
    if 'user' not in session or session['user'] not in users:
        session.clear()
        return redirect(url_for('login'))
        
    try:
        current_state = get_current_match_state()
        standings_ita = get_league_standings(current_state['round'], ITALIAN_TEAMS, 111)
        my_bets = [b for b in placed_bets if b['email'] == session['user']]
        return render_template('index.html', state=current_state, user=users[session['user']], standings=standings_ita, bets=my_bets)
    except Exception as e:
        session.clear()
        return redirect(url_for('login'))

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
        flash("Email already registered.")
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
    return redirect
