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
    'company_balance': 250000.0,  # Displays on Admin Panel and updates automatically
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
                state['company_balance'] += stake # Lost bet goes to company bank
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
        
        # Consistent Odds based on team seeding positions
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
    total_loop_time = 90  # 45s betting window, 45s match rendering window
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
    
    # Automated Ticket Verification Settlements
    settle_sportsbook_bets(current_round, time_into_current_loop, italian_fixtures + english_fixtures)
        
    return {
        'phase': phase, 'time': time_left, 'round': current_round,
        'italian_fixtures': italian_fixtures, 'english_fixtures': english_fixtures
    }

def settle_sportsbook_bets(current_round, time_into_loop, current_fixtures):
    # Settle bets once at the end of the playing loop window
    if time_into_loop >= 88 and state['last_settled_round'] < current_round:
        fixture_map = {f['id']: f for f in current_fixtures}
        
        for bet in user_bets:
            if bet['round'] == current_round and bet['status'] == 'OPEN':
                fix = fixture_map.get(bet['fixture_id'])
                if fix:
                    # Resolve outcome
                    outcome = 'X'
                    if fix['home_score'] > fix['away_score']: outcome = '1'
                    elif fix['away_score'] > fix['home_score']: outcome = '2'
                    
                    bet['score_feed'] = f"{fix['home_score']}-{fix['away_score']}"
                    if bet['prediction'] == outcome:
                        bet['status'] = 'WON'
                        payout = round(bet['stake'] * bet['odds'], 2)
                        users[bet['email']]['balance'] += payout
                        state['company_balance'] -= (payout - bet['stake']) # Deducts from admin account balance
                    else:
                        bet['status'] = 'LOST'
                        state['company_balance'] += bet['stake'] # Adds directly to company revenue
                        
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

# --- CORE ROUTINGS ---
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
            if email in users: flash("Account already exists.")
            else:
                users[email] = {'password': password, 'phone': phone, 'balance': 500.0, 'is_admin': False}
                session['user'] = email
                return redirect(url_for('index'))
    return redirect(url_for('index')) # Backup routing directly to templates landing fallback

# --- SPORTS BET SELECTION POSTING ENGINE ---
@app.route('/api/sportsbook/bet', methods=['POST'])
def place_sportsbook_bet():
    if 'user' not in session: return jsonify({'success': False, 'message': 'Auth Error'}), 401
    
    data = request.get_json() or {}
    email = session['user']
    stake = float(data.get('stake', 0))
    
    cs = get_current_match_state()
    if cs['phase'] != 'BETTING':
        return jsonify({'success': False, 'message': 'Window locked! Round matches already playing.'}), 400
        
    if users[email]['balance'] < stake or stake < 10:
        return jsonify({'success': False, 'message': 'Check wallet balance limits (Min: 10 Bob)'}), 400
        
    users[email]['balance'] -= stake
    
    new_bet = {
        'id': f"ticket_{int(time.time())}_{random.randint(10,99)}",
        'email': email,
        'round': cs['round'],
        'fixture_id': data.get('fixture_id'),
        'teams': data.get('teams'),
        'prediction': data.get('prediction'),
        'odds': float(data.get('odds', 1.0)),
        'stake': stake,
        'score_feed': 'Vb',
        'status': 'OPEN'
    }
    user_bets.append(new_bet)
    return jsonify({'success': True, 'wallet': users[email]['balance']})

@app.route('/api/sportsbook/mybets')
def get_my_bets():
    if 'user' not in session: return jsonify([])
    # Return user specific slips filtered backwards chronologically
    user_slips = [b for b in user_bets if b['email'] == session['user']]
    return jsonify(user_slips[::-1])

# --- CASH FLOW MANAGEMENT OPERATIONS ---
@app.route('/deposit', methods=['POST'])
def deposit():
    if 'user' not in session: return redirect(url_for('login'))
    amount = float(request.form.get('amount', 0))
    if amount >= MIN_DEPOSIT:
        users[session['user']]['balance'] += amount
    return redirect(url_for('index'))

@app.route('/withdraw', methods=['POST'])
def withdraw():
    if 'user' not in session: return redirect(url_for('login'))
    amount = float(request.form.get('amount', 0))
    if amount >= MIN_WITHDRAWAL and users[session['user']]['balance'] >= amount:
        users[session['user']]['balance'] -= amount
    return redirect(url_for('index'))

# --- ADMIN AUTOMATED AUDITING MODULE ---
@app.route('/admin/control', methods=['POST'])
def admin_control():
    if 'user' not in session or not users[session['user']].get('is_admin'): return jsonify({'success': False}), 403
    data = request.get_json() or {}
    action = data.get('action')
    
    if action == 'force_result':
        league = data.get('league')
        home = data.get('home_team')
        if state['manual_italian_results'] is None: state['manual_italian_results'] = {}
        if state['manual_english_results'] is None: state['manual_english_results'] = {}
        
        target = state['manual_italian_results'] if league == 'ITALIAN' else state['manual_english_results']
        target[home] = int(data.get('home_score', 0))
        return jsonify({'success': True, 'message': 'Overridden result loaded successfully.'})
    elif action == 'clear_overrides':
        state['manual_italian_results'] = None
        state['manual_english_results'] = None
        return jsonify({'success': True, 'message': 'System resets finished.'})
    return jsonify({'success': False})

@app.route('/api/aviator/state')
def aviator_state():
    update_aviator_loop()
    user_email = session.get('user', '')
    elapsed = time.time() - aviator_game['phase_start_time']
    current_mult = round(1.00 + (elapsed ** 1.3) * 0.08, 2) if aviator_game['phase'] == 'FLYING' else 1.00
    return jsonify({
        'round_id': aviator_game['round_id'], 'phase': aviator_game['phase'],
        'time_left': max(0, round(aviator_game['betting_duration'] - elapsed, 1)) if aviator_game['phase'] == 'BETTING' else 0,
        'current_multiplier': current_mult, 'has_bet': user_email in aviator_game['active_stakes'],
        'bet_amount': aviator_game['active_stakes'].get(user_email, 0),
        'user_wallet': users[user_email]['balance'] if user_email in users else 0.0
    })

@app.route('/api/aviator/bet', methods=['POST'])
def aviator_bet():
    if 'user' not in session: return jsonify({'success': False}), 401
    update_aviator_loop()
    email = session['user']
    amount = float(request.json.get('amount', 0))
    if users[email]['balance'] >= amount and aviator_game['phase'] == 'BETTING':
        users[email]['balance'] -= amount
        aviator_game['active_stakes'][email] = amount
        return jsonify({'success': True, 'wallet': users[email]['balance']})
    return jsonify({'success': False, 'message': 'Check entry parameters.'}), 400

@app.route('/api/aviator/cashout', methods=['POST'])
def aviator_cashout():
    if 'user' not in session or session['user'] not in aviator_game['active_stakes']: return jsonify({'success': False}), 400
    elapsed = time.time() - aviator_game['phase_start_time']
    current_mult = round(1.00 + (elapsed ** 1.3) * 0.08, 2)
    email = session['user']
    stake = aviator_game['active_stakes'].pop(email)
    winnings = round(stake * current_mult, 2)
    users[email]['balance'] += winnings
    state['company_balance'] -= (winnings - stake) # Automatic adjustment tracking on win payouts
    return jsonify({'success': True, 'winnings': winnings, 'multiplier': current_mult})

@app.route('/api/state')
def get_state():
    cs = get_current_match_state()
    return jsonify({
        'phase': cs['phase'], 'time': cs['time'], 'round': cs['round'],
        'company_balance': state['company_balance'], # Sends live automated bank balance to frontend view
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
