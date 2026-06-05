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

# --- VIRTUAL SIMULATION STATE ENGINE ---
state = {
    'is_running': True,
    'start_time': time.time(),
    'paused_elapsed': 0,
    'company_balance': 500000.0,
    'manual_italian_results': None,  # Used by admin to override simulations
    'manual_english_results': None
}

# --- LUCKY AVIATOR CRASH ENGINE CONFIGURATION ---
aviator_game = {
    'round_id': 1,
    'phase': 'BETTING',      
    'phase_start_time': time.time(),
    'betting_duration': 10,   
    'crash_multiplier': 2.50, 
    'active_stakes': {}       
}

# --- AVIATOR ENGINE ALGORITHMS ---
def generate_provably_fair_crash_point():
    if random.random() < 0.03:
        return 1.00  
    scale_factor = 100
    random_weight = random.randint(1, 100)
    return max(1.01, round((scale_factor / random_weight) * random.uniform(0.85, 1.15), 2))

def update_aviator_loop():
    now = time.time()
    elapsed = now - aviator_game['phase_start_time']
    
    if aviator_game['phase'] == 'BETTING':
        if elapsed >= aviator_game['betting_duration']:
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
            
    elif aviator_game['phase'] == 'CRASHED':
        if elapsed >= 4:  
            aviator_game['phase'] = 'BETTING'
            aviator_game['phase_start_time'] = now
            aviator_game['round_id'] += 1

# --- VIRTUAL FOOTBALL MATCH MATRICES ---
def generate_fixtures_for_round(round_num, team_list, seed_offset, override_scores=None):
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
        
        # Use administrative override if provided by admin panel
        if override_scores and home in override_scores:
            h_score = override_scores[home]
            a_score = override_scores.get(away, random.randint(0, 4))
        else:
            h_score = random.randint(0, 4)
            a_score = random.randint(0, 4)
        
        fixtures.append({
            'id': f"fix_{round_num}_{i}_{seed_offset}",
            'home': home,
            'away': away,
            'home_score': h_score,
            'away_score': a_score,
            'odds': {'HOME': home_odds, 'DRAW': draw_odds, 'AWAY': away_odds}
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
        
    italian_fixtures = generate_fixtures_for_round(current_round, ITALIAN_TEAMS, 111, state['manual_italian_results'])
    english_fixtures = generate_fixtures_for_round(current_round, ENGLISH_TEAMS, 222, state['manual_english_results'])
        
    return {
        'phase': phase, 'time': time_left, 'time_into_loop': time_into_current_loop,
        'round': current_round, 'season': season_number,
        'italian_fixtures': italian_fixtures, 'english_fixtures': english_fixtures
    }

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

# --- ROUTING ENDPOINTS ---
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
                flash("Please enter valid credentials.")
            else:
                users[email] = {'password': password, 'balance': 1000.0, 'bonus_unlocked': True, 'is_admin': False}
                session['user'] = email
                return redirect(url_for('index'))
                
    return '''
    <!DOCTYPE html>
    <html>
    <body style="background:#0b1118; color:white; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; margin:0; flex-direction:column;">
        <div style="background:#121b26; padding:30px; border-radius:8px; border:1px solid #1c2a39; width:320px; text-align:center;">
            <h2 style="color:#ffcc00; margin-bottom:20px;">⚽ SWIFTPITCH LOGIN</h2>
            <form method="POST">
                <input type="hidden" name="auth_action" value="signin">
                <input type="text" name="email" placeholder="Email Address" required style="width:90%; padding:11px; margin-bottom:15px; background:#0b1118; border:1px solid #1c2a39; color:white; border-radius:4px;"><br>
                <input type="password" name="password" placeholder="Password" required style="width:90%; padding:11px; margin-bottom:20px; background:#0b1118; border:1px solid #1c2a39; color:white; border-radius:4px;"><br>
                <button type="submit" style="width:97%; background:#00ff66; color:black; font-weight:bold; padding:12px; border:none; border-radius:4px; cursor:pointer;">Sign In</button>
            </form>
        </div>
    </body>
    </html>
    '''

# --- ADMINSTRATIVE CONTROL PANEL ROUTINGS ---
@app.route('/admin/control', methods=['POST'])
def admin_control():
    if 'user' not in session or not users[session['user']].get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    data = request.get_json() or {}
    action = data.get('action')
    
    if action == 'force_result':
        league = data.get('league')
        home_team = data.get('home_team')
        home_score = int(data.get('home_score', 0))
        away_score = int(data.get('away_score', 0))
        
        target_override = 'manual_italian_results' if league == 'ITALIAN' else 'manual_english_results'
        if state[target_override] is None:
            state[target_override] = {}
        state[target_override][home_team] = home_score
        return jsonify({'success': True, 'message': f'Forced result recorded for {home_team}.'})
        
    elif action == 'clear_overrides':
        state['manual_italian_results'] = None
        state['manual_english_results'] = None
        return jsonify({'success': True, 'message': 'All manual simulation overrides cleared.'})
        
    return jsonify({'success': False, 'message': 'Unknown administrative command.'})

# --- DYNAMIC REFRESH API ENDPOINTS ---
@app.route('/api/aviator/state')
def aviator_state():
    update_aviator_loop()
    user_email = session.get('user', '')
    elapsed = time.time() - aviator_game['phase_start_time']
    current_mult = round(1.00 + (elapsed ** 1.3) * 0.08, 2) if aviator_game['phase'] == 'FLYING' else 1.00
        
    return jsonify({
        'round_id': aviator_game['round_id'],
        'phase': aviator_game['phase'],
        'time_left': max(0, round(aviator_game['betting_duration'] - elapsed, 1)) if aviator_game['phase'] == 'BETTING' else 0,
        'current_multiplier': current_mult,
        'has_bet': user_email in aviator_game['active_stakes'],
        'bet_amount': aviator_game['active_stakes'].get(user_email, 0),
        'user_wallet': users[user_email]['balance'] if user_email in users else 0.0
    })

@app.route('/api/aviator/bet', methods=['POST'])
def aviator_bet():
    if 'user' not in session: return jsonify({'success': False}), 401
    update_aviator_loop()
    if aviator_game['phase'] != 'BETTING': return jsonify({'success': False, 'message': 'Boarding closed!'}), 400
    
    email = session['user']
    amount = float(request.json.get('amount', 0))
    if users[email]['balance'] < amount or amount < 10: return jsonify({'success': False, 'message': 'Invalid transaction parameters.'}), 400
    
    users[email]['balance'] -= amount
    aviator_game['active_stakes'][email] = amount
    return jsonify({'success': True, 'wallet': users[email]['balance']})

@app.route('/api/aviator/cashout', methods=['POST'])
def aviator_cashout():
    if 'user' not in session: return jsonify({'success': False}), 401
    update_aviator_loop()
    
    if aviator_game['phase'] != 'FLYING': return jsonify({'success': False, 'message': 'Too late!'}), 400
    email = session['user']
    if email not in aviator_game['active_stakes']: return jsonify({'success': False, 'message': 'No stake active.'}), 400
    
    elapsed = time.time() - aviator_game['phase_start_time']
    current_mult = round(1.00 + (elapsed ** 1.3) * 0.08, 2)
    
    stake = aviator_game['active_stakes'].pop(email)
    winnings = round(stake * current_mult, 2)
    users[email]['balance'] += winnings
    return jsonify({'success': True, 'winnings': winnings, 'multiplier': current_mult, 'wallet': users[email]['balance']})

@app.route('/api/state')
def get_state():
    cs = get_current_match_state()
    return jsonify({
        'phase': cs['phase'], 'time': cs['time'], 'round': cs['round'], 'season': cs['season'],
        'italian_fixtures': cs['italian_fixtures'], 'english_fixtures': cs['english_fixtures'],
        'standings_ita': get_league_standings(cs['round'], ITALIAN_TEAMS, 111, state['manual_italian_results']),
        'standings_eng': get_league_standings(cs['round'], ENGLISH_TEAMS, 222, state['manual_english_results'])
    })

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
