from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import time
import random
import math

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

# --- AVIATOR ENGINE MEMORY MATRIX ---
aviator_game = {
    'round_id': 1,
    'phase': 'BETTING', # BETTING, FLYING, CRASHED
    'phase_start_time': time.time(),
    'betting_duration': 10, # Seconds for players to place stakes
    'crash_multiplier': 2.50, # Secret pre-determined point
    'active_stakes': {} # email -> stake_amount
}

def generate_provably_fair_crash_point():
    """Uses a mathematical probability curve similar to real crash games."""
    # 3% chance the plane immediately crashes at 1.00x
    if random.random() < 0.03:
        return 1.00
    
    # Otherwise, distribute multipliers across a curve
    E = 100
    return max(1.01, round((E / (random.randint(1, 100))) * random.uniform(0.8, 1.2), 2))

def update_aviator_loop():
    now = time.time()
    elapsed = now - aviator_game['phase_start_time']
    
    if aviator_game['phase'] == 'BETTING':
        if elapsed >= aviator_game['betting_duration']:
            # Move to FLYING phase
            aviator_game['phase'] = 'FLYING'
            aviator_game['phase_start_time'] = now
            aviator_game['crash_multiplier'] = generate_provably_fair_crash_point()
            
    elif aviator_game['phase'] == 'FLYING':
        # Calculate current real-time multiplier based on an exponential scale
        # Multiplier grows faster over time: 1.00 + (t^1.2) * 0.08
        current_mult = 1.00 + (elapsed ** 1.3) * 0.08
        
        if current_mult >= aviator_game['crash_multiplier']:
            # The plane flies away!
            aviator_game['phase'] = 'CRASHED'
            aviator_game['phase_start_time'] = now
            
            # Collect house wins from anyone who didn't cash out
            for email, stake in aviator_game['active_stakes'].items():
                state['company_balance'] += stake
            aviator_game['active_stakes'] = {}
            
    elif aviator_game['phase'] == 'CRASHED':
        if elapsed >= 4: # Wait 4 seconds on the crash screen before opening next bets
            aviator_game['phase'] = 'BETTING'
            aviator_game['phase_start_time'] = now
            aviator_game['round_id'] += 1

# --- FIXTURE GENERATORS ---
def generate_fixtures_for_round(round_num, team_list, seed_offset):
    random.seed(round_num + seed_offset) 
    shuffled_teams = list(team_list)
    random.shuffle(shuffled_teams)
    
    fixtures = []
    for i in range(0, len(shuffled_teams), 2):
        home = shuffled_teams[i]
        away = shuffled_teams[i+1]
        fixtures.append({
            'id': f"fix_{round_num}_{i}_{seed_offset}",
            'home': home, 'away': away,
            'home_score': random.randint(0, 4), 'away_score': random.randint(0, 4),
            'odds': {'HOME': round(random.uniform(1.3, 4.5), 2), 'DRAW': round(random.uniform(2.6, 3.8), 2), 'AWAY': round(random.uniform(1.4, 5.0), 2)}
        })
    return fixtures

def get_current_match_state():
    total_loop_time = 115  
    TOTAL_ROUNDS_IN_SEASON = 19  
    elapsed = int(time.time() - state['start_time']) if state['is_running'] else int(state['paused_elapsed'])
    total_season_time = total_loop_time * TOTAL_ROUNDS_IN_SEASON
    season_number = (elapsed // total_season_time) + 1
    time_into_current_season = elapsed % total_season_time
    current_round = (time_into_current_season // total_loop_time) + 1
    time_into_current_loop = time_into_current_season % total_loop_time
    
    phase = 'BETTING' if time_into_current_loop < 60 else 'PLAYING'
    time_left = (60 - time_into_current_loop) if phase == 'BETTING' else (115 - time_into_current_loop)
        
    return {
        'phase': phase, 'time': time_left, 'time_into_loop': time_into_current_loop,
        'round': current_round, 'season': season_number,
        'italian_fixtures': generate_fixtures_for_round(current_round, ITALIAN_TEAMS, 111),
        'english_fixtures': generate_fixtures_for_round(current_round, ENGLISH_TEAMS, 222)
    }

def get_league_standings(current_round, teams_list, seed_offset):
    table = {team: {'name': team, 'mp': 0, 'w': 0, 'd': 0, 'l': 0, 'pts': 0} for team in teams_list}
    for r in range(1, current_round):
        for f in generate_fixtures_for_round(r, teams_list, seed_offset):
            h, a, hs, as_ = f['home'], f['away'], f['home_score'], f['away_score']
            table[h]['mp'] += 1; table[a]['mp'] += 1
            if hs > as_: table[h]['w'] += 1; table[h]['pts'] += 3; table[a]['l'] += 1
            elif as_ > hs: table[a]['w'] += 1; table[a]['pts'] += 3; table[h]['l'] += 1
            else: table[h]['d'] += 1; table[h]['pts'] += 1; table[a]['d'] += 1; table[a]['pts'] += 1
    return sorted(table.values(), key=lambda x: x['pts'], reverse=True)

# --- ROUTES ---
@app.route('/')
def index():
    if 'user' not in session or session['user'] not in users:
        session.clear()
        return redirect(url_for('login'))
    return render_template('index.html', state=get_current_match_state(), user=users[session['user']])

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
            if email in users: flash("Account already exists.")
            else:
                users[email] = {'password': password, 'balance': 1000.0, 'bonus_unlocked': True, 'is_admin': False}
                session['user'] = email
                return redirect(url_for('index'))
                
    return '''
    <body style="background:#0b1118; color:white; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; margin:0; flex-direction:column;">
        {% with messages = get_flashed_messages() %}
          {% if messages %}{% for msg in messages %}<div style="background:#ff3333; padding:10px; margin-bottom:15px; border-radius:4px;">⚠️ {{ msg }}</div>{% endfor %}{% endif %}
        {% endwith %}
        <div id="signin-card" style="background:#121b26; padding:30px; border-radius:8px; border:1px solid #1c2a39; width:320px; text-align:center;">
            <h2 style="color:#ffcc00;">⚽ SWIFTPITCH LOGIN</h2>
            <form method="POST"><input type="hidden" name="auth_action" value="signin">
                <input type="text" name="email" placeholder="Email Address" required style="width:90%; padding:10px; margin-bottom:15px; background:#0b1118; border:1px solid #1c2a39; color:white; border-radius:4px;"><br>
                <input type="password" name="password" placeholder="Password" required style="width:90%; padding:10px; margin-bottom:20px; background:#0b1118; border:1px solid #1c2a39; color:white; border-radius:4px;"><br>
                <button type="submit" style="width:97%; background:#00ff66; color:black; font-weight:bold; padding:12px; border:none; border-radius:4px; cursor:pointer; text-transform:uppercase;">Sign In</button>
            </form>
            <p style="margin-top:20px; font-size:13px; color:#a0aec0;">New player? <a href="#" onclick="document.getElementById('signin-card').style.display='none';document.getElementById('signup-card').style.display='block';" style="color:#00ff66; text-decoration:none;">Create Account Here →</a></p>
        </div>
        <div id="signup-card" style="background:#121b26; padding:30px; border-radius:8px; border:1px solid #1c2a39; width:320px; text-align:center; display:none;">
            <h2 style="color:#00ff66;">📝 PLAYER REGISTRATION</h2>
            <form method="POST"><input type="hidden" name="auth_action" value="signup">
                <input type="email" name="email" placeholder="Email Address" required style="width:90%; padding:10px; margin-bottom:15px; background:#0b1118; border:1px solid #1c2a39; color:white; border-radius:4px;"><br>
                <input type="password" name="password" placeholder="Password" required style="width:90%; padding:10px; margin-bottom:20px; background:#0b1118; border:1px solid #1c2a39; color:white; border-radius:4px;"><br>
                <button type="submit" style="width:97%; background:#ffcc00; color:black; font-weight:bold; padding:12px; border:none; border-radius:4px; cursor:pointer; text-transform:uppercase;">Register</button>
            </form>
            <p style="margin-top:20px; font-size:13px; color:#a0aec0;">Have an account? <a href="#" onclick="document.getElementById('signup-card').style.display='none';document.getElementById('signin-card').style.display='block';" style="color:#ffcc00; text-decoration:none;">← Login</a></p>
        </div>
    </body>
    '''

# --- AVIATOR INTERACTION API ENDPOINTS ---
@app.route('/api/aviator/state')
def aviator_state():
    update_aviator_loop()
    user_email = session.get('user', '')
    
    elapsed = time.time() - aviator_game['phase_start_time']
    current_mult = 1.00
    if aviator_game['phase'] == 'FLYING':
        current_mult = round(1.00 + (elapsed ** 1.3) * 0.08, 2)
        
    return jsonify({
        'round_id': aviator_game['round_id'],
        'phase': aviator_game['phase'],
        'time_left': max(0, round(aviator_game['betting_duration'] - elapsed, 1)) if aviator_game['phase'] == 'BETTING' else 0,
        'current_multiplier': current_mult,
        'has_bet': user_email in aviator_game['active_stakes'],
        'bet_amount': aviator_game['active_stakes'].get(user_email, 0),
        'user_wallet': users[user_email]['balance'] if user_email in users else 0
    })

@app.route('/api/aviator/bet', methods=['POST'])
def aviator_bet():
    if 'user' not in session: return jsonify({'success': False, 'message': 'Expired session.'}), 401
    update_aviator_loop()
    
    if aviator_game['phase'] != 'BETTING':
        return jsonify({'success': False, 'message': 'Flight boarding closed! Wait for next round.'}), 400
        
    email = session['user']
    try: amount = float(request.json.get('amount', 0))
    except ValueError: amount = 0
    
    if amount < 10: return jsonify({'success': False, 'message': 'Minimum stake is 10 KSH.'}), 400
    if users[email]['balance'] < amount: return jsonify({'success': False, 'message': 'Insufficient funds.'}), 400
    
    users[email]['balance'] -= amount
    aviator_game['active_stakes'][email] = amount
    return jsonify({'success': True, 'wallet': users[email]['balance']})

@app.route('/api/aviator/cashout', methods=['POST'])
def aviator_cashout():
    if 'user' not in session: return jsonify({'success': False, 'message': 'Expired session.'}), 401
    update_aviator_loop()
    
    if aviator_game['phase'] != 'FLYING':
        return jsonify({'success': False, 'message': 'Plane is not currently in flight.'}), 400
        
    email = session['user']
    if email not in aviator_game['active_stakes']:
        return jsonify({'success': False, 'message': 'No active stake found for this flight.'}), 400
        
    elapsed = time.time() - aviator_game['phase_start_time']
    current_mult = round(1.00 + (elapsed ** 1.3) * 0.08, 2)
    
    # Check if they managed to hit it before the actual crash point trigger
    if current_mult >= aviator_game['crash_multiplier']:
        return jsonify({'success': False, 'message': 'Too late! The plane already flew away.'}), 400
        
    stake = aviator_game['active_stakes'].pop(email)
    winnings = round(stake * current_mult, 2)
    
    users[email]['balance'] += winnings
    state['company_balance'] -= (winnings - stake)
    
    return jsonify({'success': True, 'winnings': winnings, 'multiplier': current_mult, 'wallet': users[email]['balance']})

# --- EXISTING SPORTSBOOK CODES ---
@app.route('/place-multibet', methods=['POST'])
def place_multibet():
    if 'user' not in session: return jsonify({'success': False}), 401
    current_state = get_current_match_state()
    if current_state['phase'] != 'BETTING': return jsonify({'success': False, 'message': 'Market closed.'}), 400
    data = request.get_json() or {}
    selections = data.get('selections', [])
    stake = float(data.get('stake', 0))
    user = users[session['user']]
    if user['balance'] < stake or stake < 10: return jsonify({'success': False, 'message': 'Invalid stake/balance.'}), 400
    
    user['balance'] -= stake
    placed_bets.append({'id': f"t_{int(time.time())}", 'email': session['user'], 'round': current_state['round'], 'season': current_state['season'], 'selections': selections, 'stake': stake, 'total_odds': 2.5, 'status': 'PENDING'})
    return jsonify({'success': True, 'message': 'Multibet verified!'})

@app.route('/deposit', methods=['POST'])
def deposit():
    if 'user' not in session: return redirect(url_for('login'))
    users[session['user']]['balance'] += int(float(request.form.get('amount', 0)))
    return redirect(url_for('index'))

@app.route('/api/state')
def get_state():
    cs = get_current_match_state()
    return jsonify({'phase': cs['phase'], 'time': cs['time'], 'round': cs['round'], 'season': cs['season'], 'italian_fixtures': cs['italian_fixtures'], 'english_fixtures': cs['english_fixtures'], 'standings_ita': get_league_standings(cs['round'], ITALIAN_TEAMS, 111), 'standings_eng': get_league_standings(cs['round'], ENGLISH_TEAMS, 222), 'logs': [f"[System] Matches active."]})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
