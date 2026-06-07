from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import os
import time
import random

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'swiftpitch_clean_slate_2026')

# --- LEAGUE CONTEXT CONFIGURATIONS ---
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

# Global Application State Engine
state = {
    'house_balance': 750000.0,       # Restricted Admin balance tracking
    'simulation_running': True,     
    'last_update': time.time(),
    'current_round': 1,
    'season_fixtures_italian': {},
    'season_fixtures_english': {},
    'live_matches_italian': [],
    'live_matches_english': [],
    'pending_matches_italian': [],
    'pending_matches_english': [],
    'match_logs': [],
    'sports_bets': [],               # Stores active/settled football wagers
    'standings_italian': {},
    'standings_english': {},
    'aviator': {'phase': 'BETTING', 'start': time.time(), 'multiplier': 1.0, 'stakes': {}}
}

# Pre-seeded users database
users = {
    'admin@swiftpitch.com': {
        'password': 'adminpassword', 
        'phone': '0700000000', 
        'balance': 0.0, 
        'bonus': 0.0, 
        'bonus_locked': False, 
        'role': 'admin'
    },
    'player@swiftpitch.com': {
        'password': 'password123', 
        'phone': '0711223344', 
        'balance': 1000.0, 
        'bonus': 100.0, 
        'bonus_locked': True, 
        'role': 'user'
    }
}

def init_standings():
    state['standings_italian'] = {team: {'played': 0, 'won': 0, 'draw': 0, 'lost': 0, 'points': 0} for team in ITALIAN_TEAMS}
    state['standings_english'] = {team: {'played': 0, 'won': 0, 'draw': 0, 'lost': 0, 'points': 0} for team in ENGLISH_TEAMS}

# --- ROUND-ROBIN LEAGUE FIXTURE GENERATOR WITH DYNAMIC ODDS ---
def build_round_robin_schedule(teams, league_tag):
    rotation = list(teams)
    random.shuffle(rotation)
    n = len(rotation)
    schedule = {}
    match_id = 1 if league_tag == 'ITALIAN' else 5000
    
    for r in range(n - 1): 
        round_num = r + 1
        schedule[round_num] = []
        for i in range(n // 2):
            t1 = rotation[i]
            t2 = rotation[n - 1 - i]
            schedule[round_num].append({
                'id': match_id,
                'league': league_tag,
                'teams': f"{t1} vs {t2}",
                't1': t1,
                't2': t2,
                'score': '0-0',
                'status': 'PENDING',
                'minute': 0,
                # Injection of algorithmic 1X2 odds markers
                'odds_home': round(random.uniform(1.4, 3.2), 2),
                'odds_draw': round(random.uniform(2.8, 3.9), 2),
                'odds_away': round(random.uniform(2.1, 4.8), 2)
            })
            match_id += 1
        rotation = [rotation[0]] + [rotation[-1]] + rotation[1:-1]
    return schedule

def load_league_round_fixtures():
    r = state['current_round']
    if r > 19:
        state['current_round'] = 1
        r = 1
        init_standings()
        state['season_fixtures_italian'] = build_round_robin_schedule(ITALIAN_TEAMS, 'ITALIAN')
        state['season_fixtures_english'] = build_round_robin_schedule(ENGLISH_TEAMS, 'ENGLISH')

    state['live_matches_italian'] = state['season_fixtures_italian'][r]
    state['live_matches_english'] = state['season_fixtures_english'][r]
    
    for m in state['live_matches_italian'] + state['live_matches_english']:
        m['status'] = 'LIVE'
        m['minute'] = 0
        m['score'] = '0-0'

# Initialize systems
init_standings()
state['season_fixtures_italian'] = build_round_robin_schedule(ITALIAN_TEAMS, 'ITALIAN')
state['season_fixtures_english'] = build_round_robin_schedule(ENGLISH_TEAMS, 'ENGLISH')
load_league_round_fixtures()

# --- STATE SYNCHRONIZATION ENGINE ---
def dynamic_engine_loop():
    now = time.time()
    dt = now - state['last_update']
    state['last_update'] = now
    
    # Aviator Loop Cycle
    av_elapsed = now - state['aviator']['start']
    if state['aviator']['phase'] == 'BETTING' and av_elapsed > 10:
        state['aviator']['phase'] = 'FLYING'
        state['aviator']['start'] = now
        state['aviator']['multiplier'] = 1.0
    elif state['aviator']['phase'] == 'FLYING':
        state['aviator']['multiplier'] += round(dt * 0.5, 2)
        if state['aviator']['multiplier'] > random.uniform(1.3, 6.5):
            state['aviator']['phase'] = 'BETTING'
            state['aviator']['start'] = now
            state['aviator']['stakes'] = {} 

    if not state['simulation_running']:
        return

    # Process Active Match Minutes
    all_live = state['live_matches_italian'] + state['live_matches_english']
    for match in all_live:
        if match['status'] == 'LIVE':
            match['minute'] += int(dt * 8) 
            
            if random.random() < 0.03:
                s1, s2 = map(int, match['score'].split('-'))
                if random.choice([True, False]): s1 += 1
                else: s2 += 1
                match['score'] = f"{s1}-{s2}"
                
            if match['minute'] >= 90:
                match['status'] = 'FINISHED'
                finalize_match_statistics(match)
                
    if all(m['status'] == 'FINISHED' for m in all_live):
        state['current_round'] += 1
        load_league_round_fixtures()

def finalize_match_statistics(match):
    s1, s2 = map(int, match['score'].split('-'))
    t1, t2 = match['t1'], match['t2']
    standings = state['standings_italian'] if match['league'] == 'ITALIAN' else state['standings_english']
    
    standings[t1]['played'] += 1
    standings[t2]['played'] += 1
    
    if s1 > s2:
        standings[t1]['won'] += 1; standings[t1]['points'] += 3
        standings[t2]['lost'] += 1
        outcome = '1'
    elif s2 > s1:
        standings[t2]['won'] += 1; standings[t2]['points'] += 3
        standings[t1]['lost'] += 1
        outcome = '2'
    else:
        standings[t1]['draw'] += 1; standings[t1]['points'] += 1
        standings[t2]['draw'] += 1; standings[t2]['points'] += 1
        outcome = 'X'
        
    state['match_logs'].append(f"[{match['league']}] Rd {state['current_round']} | {match['teams']} ({match['score']})")

    # --- AUTOMATED SPORTS BET SETTLEMENT ENGINE ---
    for bet in state['sports_bets']:
        if bet['match_id'] == match['id'] and bet['status'] == 'PENDING':
            bet['score'] = match['score']
            if bet['prediction'] == outcome:
                bet['status'] = 'WON'
                payout = bet['stake'] * bet['odds']
                user_profile = users.get(bet['user'])
                if user_profile:
                    user_profile['balance'] += payout
                state['house_balance'] -= payout  # Vault payout deduction
            else:
                bet['status'] = 'LOST'

# --- VIEWS & API DISPATCH PIPELINES ---
@app.route('/')
def index():
    if 'user' not in session or session['user'] not in users:
        session.clear()
        return redirect(url_for('login'))
    return render_template('index.html', user=users[session['user']])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session: return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email in users and users[email]['password'] == password:
            session['user'] = email
            return redirect(url_for('index'))
        error = "Invalid credentials profile."
    return render_template('login.html', error=error)

@app.route('/deposit', methods=['POST'])
def deposit():
    user = users.get(session.get('user'))
    if user:
        amount = float(request.form.get('amount', 0))
        if amount >= 10.0:
            user['balance'] += amount
            state['house_balance'] += amount
            if user['bonus_locked'] and amount >= 50.0:
                user['balance'] += user['bonus']
                user['bonus'] = 0.0
                user['bonus_locked'] = False
    return redirect(url_for('index'))

@app.route('/withdraw', methods=['POST'])
def withdraw():
    user = users.get(session.get('user'))
    if user and float(request.form.get('amount', 0)) >= 100.0:
        amount = float(request.form.get('amount', 0))
        if user['balance'] >= amount:
            user['balance'] -= amount
            state['house_balance'] -= amount
    return redirect(url_for('index'))

# --- FOOTBALL WAGER PLACEMENT DISPATCH ---
@app.route('/api/sports/bet', methods=['POST'])
def place_sports_bet():
    user = users.get(session.get('user'))
    if not user: return jsonify({'success': False, 'message': 'Unauthorized Session Context'})
    
    data = request.get_json() or {}
    match_id = int(data.get('match_id', 0))
    prediction = data.get('prediction') # '1', 'X', or '2'
    stake = float(data.get('stake', 0))
    
    if stake < 10.0:
        return jsonify({'success': False, 'message': 'Minimum match stake is 10 KSH'})
    if user['balance'] < stake:
        return jsonify({'success': False, 'message': 'Insufficient account liquidity'})
        
    all_live = state['live_matches_italian'] + state['live_matches_english']
    target = next((m for m in all_live if m['id'] == match_id), None)
    
    if not target or target['status'] != 'LIVE' or target['minute'] > 75:
        return jsonify({'success': False, 'message': 'Match betting window closed'})
        
    if prediction == '1': odds = target['odds_home']
    elif prediction == 'X': odds = target['odds_draw']
    elif prediction == '2': odds = target['odds_away']
    else: return jsonify({'success': False, 'message': 'Invalid selection profile'})
    
    # Execute transaction
    user['balance'] -= stake
    state['house_balance'] += stake
    
    state['sports_bets'].append({
        'user': session['user'],
        'match_id': match_id,
        'teams': target['teams'],
        'league': target['league'],
        'prediction': prediction,
        'odds': odds,
        'stake': stake,
        'status': 'PENDING',
        'score': target['score']
    })
    return jsonify({'success': True})

# --- AVIATOR INTERACTIVE ENDPOINTS ---
@app.route('/api/aviator/bet', methods=['POST'])
def aviator_bet():
    user = users.get(session.get('user'))
    if not user or state['aviator']['phase'] != 'BETTING': return jsonify({'success': False})
    data = request.get_json() or {}
    stake = float(data.get('stake', 0))
    if user['balance'] >= stake and stake >= 10.0:
        user['balance'] -= stake
        state['house_balance'] += stake
        state['aviator']['stakes'][session['user']] = stake
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/aviator/cashout', methods=['POST'])
def aviator_cashout():
    user = users.get(session.get('user'))
    if not user or state['aviator']['phase'] != 'FLYING': return jsonify({'success': False})
    stake = state['aviator']['stakes'].pop(session['user'], None)
    if stake:
        winnings = stake * state['aviator']['multiplier']
        user['balance'] += winnings
        state['house_balance'] -= winnings
        return jsonify({'success': True, 'winnings': winnings})
    return jsonify({'success': False})

@app.route('/api/state')
def get_state():
    dynamic_engine_loop()
    curr_user = users.get(session.get('user'), {'role': 'user', 'balance': 0.0})
    is_admin = curr_user.get('role') == 'admin'
    
    user_bets = [
        {k: v for k, v in b.items() if k != 'user'} 
        for b in state['sports_bets'] if b['user'] == session.get('user')
    ]
    
    return jsonify({
        'house_balance': state['house_balance'] if is_admin else None, 
        'simulation_running': state['simulation_running'],
        'current_round': state['current_round'],
        'live_matches': state['live_matches_italian'] + state['live_matches_english'],
        'match_logs': state['match_logs'][-12:],
        'standings_italian': state['standings_italian'],
        'standings_english': state['standings_english'],
        'aviator': {
            'phase': state['aviator']['phase'],
            'multiplier': state['aviator']['multiplier']
        },
        'user_balance': curr_user['balance'],
        'user_bonus': curr_user.get('bonus', 0),
        'user_bonus_locked': curr_user.get('bonus_locked', False),
        'user_role': curr_user['role'],
        'my_sports_bets': user_bets[-6:]
    })

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
def admin_dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    curr_user = users.get(session['user'])
    if not curr_user or curr_user.get('role') != 'admin': return "Unauthorized", 403
    return render_template('admin.html', user=curr_user)

@app.route('/admin/toggle', methods=['POST'])
def toggle_sim():
    user = users.get(session.get('user'), {})
    if user.get('role') != 'admin': return "Unauthorized", 403
    data = request.get_json() or {}
    state['simulation_running'] = data.get('run', True)
    return jsonify({'success': True})

@app.route('/api/admin/users')
def admin_get_users():
    if 'user' not in session or users.get(session['user'], {}).get('role') != 'admin': return jsonify({'error': 'Unauthorized'}), 403
    safe_users = {k: {v_k: v_v for v_k, v_v in v.items() if v_k != 'password'} for k, v in users.items()}
    return jsonify(safe_users)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
