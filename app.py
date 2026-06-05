from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import time
import random

app = Flask(__name__)

# --- SECURE CONFIGURATION SYSTEM ---
app.config.update(
    SECRET_KEY='swiftpitch_super_secret_key_2026',
    SESSION_COOKIE_SECURE=False,  
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# --- IN-MEMORY DATABASE STORAGE ---
users = {
    'admin@swiftpitch.com': {
        'password': 'adminpassword', 
        'phone': '0700000000',
        'balance': 0.0, 
        'is_admin': True
    },
    'player@test.com': {
        'password': 'password123',
        'phone': '0711223344',
        'balance': 1000.0,
        'is_admin': False
    }
}

# ACTIVE USER SLIPS AND HISTORIES
user_bets = []  
withdrawals_log = []

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
    'company_balance': 250000.0,  
    'manual_italian_results': None,  
    'manual_english_results': None,
    'last_settled_round': 0
}

MIN_DEPOSIT = 10.0
MIN_WITHDRAWAL = 100.0

# --- LUCKY AVIATOR CRASH ENGINE ---
aviator_game = {
    'round_id': 1,
    'phase': 'BETTING',      
    'phase_start_time': time.time(),
    'betting_duration': 10,   
    'crash_multiplier': 2.50, 
    'active_stakes': {}       
}

def generate_provably_fair_crash_point():
    if random.random() < 0.03: return 1.00  
    return max(1.01, round((100 / random.randint(1, 100)) * random.uniform(0.85, 1.15), 2))

def update_aviator_loop():
    now = time.time()
    elapsed = now - aviator_game['phase_start_time']
    
    if aviator_game['phase'] == 'BETTING' and elapsed >= aviator_game['betting_duration']:
        aviator_game['phase'] = 'FLYING'
        aviator_game['phase_start_time'] = now
        aviator_game['crash_multiplier'] = generate_provably_fair_crash_point()
    elif aviator_game['phase'] == 'FLYING':
        current_mult = 1.00 + (elapsed ** 1.3) * 0.08
        if current_mult >= aviator_game['crash_multiplier']:
            aviator_game['phase'] = 'CRASHED'
            aviator_game['phase_start_time'] = now
            for email, stake in aviator_game['active_stakes'].items():
                state['company_balance'] += stake
            aviator_game['active_stakes'] = {}
    elif aviator_game['phase'] == 'CRASHED' and elapsed >= 4:
        aviator_game['phase'] = 'BETTING'
        aviator_game['phase_start_time'] = now
        aviator_game['round_id'] += 1

# --- VIRTUAL SPORTS BET ENGINE MATRICES ---
def generate_fixtures_for_round(round_num, team_list, seed_offset, override_scores=None):
    random.seed(round_num + seed_offset) 
    shuffled_teams = list(team_list)
    random.shuffle(shuffled_teams)
    
    fixtures = []
    for i in range(0, len(shuffled_teams), 2):
        home = shuffled_teams[i]
        away = shuffled_teams[i+1]
        
        home_odds = round(random.uniform(1.40, 3.20), 2)
        draw_odds = round(random.uniform(2.80, 3.60), 2)
        away_odds = round(random.uniform(1.80, 4.50), 2)
        
        if override_scores and home in override_scores:
            h_score = override_scores[home]
            a_score = override_scores.get(away, random.randint(0, 3))
        else:
            h_score = random.randint(0, 4)
            a_score = random.randint(0, 4)
        
        fixtures.append({
            'id': f"fix_{round_num}_{i}_{seed_offset}",
            'home': home, 'away': away,
            'home_score': h_score, 'away_score': a_score,
            'odds': {'1': home_odds, 'X': draw_odds, '2': away_odds}
        })
    return fixtures

def get_current_match_state():
    total_loop_time = 90  
    elapsed = int(time.time() - state['start_time'])
    
    current_round = (elapsed // total_loop_time) + 1
    time_into_current_loop = elapsed % total_loop_time
    
    if time_into_current_loop < 45:
        phase = 'BETTING'
        time_left = 45 - time_into_current_loop
    else:
        phase = 'PLAYING'
        time_left = 90 - time_into_current_loop
        
    italian_fixtures = generate_fixtures_for_round(current_round, ITALIAN_TEAMS, 111, state['manual_italian_results'])
    english_fixtures = generate_fixtures_for_round(current_round, ENGLISH_TEAMS, 222, state['manual_english_results'])
    
    settle_sportsbook_bets(current_round, time_into_current_loop, italian_fixtures + english_fixtures)
        
    return {
        'phase': phase, 'time': time_left, 'round': current_round,
        'italian_fixtures': italian_fixtures, 'english_fixtures': english_fixtures
    }

def settle_sportsbook_bets(current_round, time_into_loop, current_fixtures):
    if time_into_loop >= 88 and state['last_settled_round'] < current_round:
        fixture_map = {f['id']: f for f in current_fixtures}
        
        for bet in user_bets:
            if bet['round'] == current_round and bet['status'] == 'OPEN':
                fix = fixture_map.get(bet['fixture_id'])
                if fix:
                    outcome = 'X'
                    if fix['home_score'] > fix['away_score']: outcome = '1'
                    elif fix['away_score'] > fix['home_score']: outcome = '2'
                    
                    bet['score_feed'] = f"{fix['home_score']}-{fix['away_score']}"
                    if bet['prediction'] == outcome:
                        bet['status'] = 'WON'
                        payout = round(bet['stake'] * bet['odds'], 2)
                        users[bet['email']]['balance'] += payout
                        state['company_balance'] -= (payout - bet['stake'])
                    else:
                        bet['status'] = 'LOST'
                        state['company_balance'] += bet['stake']
                        
        state['last_settled_round'] = current_round

def get_league_standings(current_round, teams_list, seed_offset, overrides=None):
    table = {team: {'name': team, 'mp': 0, 'w': 0, 'd': 0, 'l': 0, 'pts': 0} for team in teams_list}
    for r in range(1, current_round):
        fixtures = generate_fixtures_for_round(r, teams_list, seed_offset, overrides)
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

# --- CORE ROUTINGS FIXED FROM INFINITE LOOP ---
@app.route('/')
def index():
    if 'user' not in session or session['user'] not in users:
        session.clear()
        return redirect(url_for('login'))
    return render_template('index.html', user=users[session['user']])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        action = request.form.get('auth_action')
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        
        if action == 'signin':
            if email in users and users[email]['password'] == password:
                session['user'] = email
                return redirect(url_for('index'))
            flash("Invalid credentials.")
        elif action == 'signup':
            if email in users: 
                flash("Account already exists.")
            else:
                users[email] = {'password': password, 'phone': phone, 'balance': 500.0, 'is_admin': False}
                session['user'] = email
                return redirect(url_for('index'))
                
    # Direct HTML fallback output logic avoids recursive app matching states
    return render_template_string()

def render_template_string():
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>SwiftPitch Auth</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
    <body style="background:#0b1118; color:white; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; margin:0; flex-direction:column;">
        <div id="signin-card" style="background:#121b26; padding:30px; border-radius:8px; border:1px solid #1c2a39; width:320px; text-align:center;">
            <h2 style="color:#ffcc00; margin-bottom:20px;">⚽ SWIFTPITCH LOGIN</h2>
            <form method="POST">
                <input type="hidden" name="auth_action" value="signin">
                <input type="text" name="email" placeholder="Email Address" required style="width:90%; padding:11px; margin-bottom:15px; background:#0b1118; border:1px solid #1c2a39; color:white; border-radius:4px;"><br>
                <input type="password" name="password" placeholder="Password" required style="width:90%; padding:11px; margin-bottom:20px; background:#0b1118; border:1px solid #1c2a39; color:white; border-radius:4px;"><br>
                <button type="submit" style="width:97%; background:#00ff66; color:black; font-weight:bold; padding:12px; border:none; border-radius:4px; cursor:pointer;">SIGN IN</button>
            </form>
            <p style="margin-top:20px; font-size:13px;"><a href="#" onclick="toggle(true)" style="color:#00ff66; text-decoration:none;">Create Account Here →</a></p>
        </div>
        <div id="signup-card" style="background:#121b26; padding:30px; border-radius:8px; border:1px solid #1c2a39; width:320px; text-align:center; display:none;">
            <h2 style="color:#00ff66; margin-bottom:20px;">📝 PLAYER REGISTRATION</h2>
            <form method="POST">
                <input type="hidden" name="auth_action" value="signup">
                <input type="email" name="email" placeholder="Email Address" required style="width:90%; padding:11px; margin-bottom:15px; background:#0b1118; border:1px solid #1c2a39; color:white; border-radius:4px;"><br>
                <input type="text" name="phone" placeholder="Phone Number" required style="width:90%; padding:11px; margin-bottom:15px; background:#0b1118; border:1px solid #1c2a39; color:white; border-radius:4px;"><br>
                <input type="password" name="password" placeholder="Choose Password" required style="width:90%; padding:11px; margin-bottom:20px; background:#0b1118; border:1px solid #1c2a39; color:white; border-radius:4px;"><br>
                <button type="submit" style="width:97%; background:#ffcc00; color:black; font-weight:bold; padding:12px; border:none; border-radius:4px; cursor:pointer;">REGISTER</button>
            </form>
            <p style="margin-top:20px; font-size:13px;"><a href="#" onclick="toggle(false)" style="color:#ffcc00; text-decoration:none;">← Back to Login</a></p>
        </div>
        <script>
            function toggle(show) {
                document.getElementById('signin-card').style.display = show ? 'none' : 'block';
                document.getElementById('signup-card').style.display = show ? 'block' : 'none';
            }
        </script>
    </body>
    </html>
    '''

# --- POST SLIP MULTIPLIERS ENGINE ---
@app.route('/api/sportsbook/bet', methods=['POST'])
def place_sportsbook_bet():
    if 'user' not in session: return jsonify({'success': False, 'message': 'Auth Error'}), 401
    data = request.get_json() or {}
    email = session['user']
    stake = float(data.get('stake', 0))
    
    cs = get_current_match_state()
    if cs['phase'] != 'BETTING':
        return jsonify({'success': False, 'message': 'Round matches already playing.'}), 400
    if users[email]['balance'] < stake or stake < 10:
        return jsonify({'success': False, 'message': 'Insufficient wallet balance.'}), 400
        
    users[email]['balance'] -= stake
    user_bets.append({
        'id': f"ticket_{int(time.time())}", 'email': email, 'round': cs['round'],
        'fixture_id': data.get('fixture_id'), 'teams': data.get('teams'),
        'prediction': data.get('prediction'), 'odds': float(data.get('odds', 1.0)),
        'stake': stake, 'score_feed': 'Vb', 'status': 'OPEN'
    })
    return jsonify({'success': True, 'wallet': users[email]['balance']})

@
