from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import time
import random

app = Flask(__name__)
app.secret_key = 'swiftpitch_high_roller_2026'

# --- 1. SEPARATED LEAGUE DATA BOARDS ---
ITALIAN_TEAMS = ["Roma", "Juventus", "Milaan Reds", "Torino", "Fiorentina", "Bologna", "Sassuolo", "Lazio", "Verona", "Atlanta", "Monza", "Cremonese", "Leece", "Udinese", "Spenzia", "Empoli", "Napoli", "Samdoria", "Salernitana", "Milan Blues"]
ENGLISH_TEAMS = ["Manchester blue", "spurs", "A.Villa", "London blues", "Manchester red", "New castle", "Everton", "Bournemouth", "N. forrest", "Brighton", "London reds", "Brentford", "Wolves", "west Ham", "Southampton", "Fulham", "Liverpool", "C.Palace", "Leicester", "Leeds"]

state = {
    'house_balance': 500000.0,      
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
    'standings_italian': {},
    'standings_english': {},
    'aviator': {'phase': 'BETTING', 'start': time.time(), 'multiplier': 1.0, 'stakes': {}}
}

users = {
    'admin@swiftpitch.com': {'password': 'adminpassword', 'phone': '0700000000', 'balance': 0.0, 'bonus': 0.0, 'bonus_locked': False, 'role': 'admin', 'bets': []}
}

def init_standings():
    for team in ITALIAN_TEAMS:
        state['standings_italian'][team] = {'played': 0, 'won': 0, 'draw': 0, 'lost': 0, 'points': 0}
    for team in ENGLISH_TEAMS:
        state['standings_english'][team] = {'played': 0, 'won': 0, 'draw': 0, 'lost': 0, 'points': 0}

init_standings()

# --- 2. ROUND-ROBIN LEAGUE FIXTURE GENERATOR ---
def build_round_robin_schedule(teams, league_tag):
    """Generates a mathematically perfect round-robin league season schedule"""
    rotation = list(teams)
    random.shuffle(rotation)
    n = len(rotation)
    schedule = {}
    
    match_id = 1 if league_tag == 'ITALIAN' else 2000
    
    for r in range(n - 1): # 19 Rounds total for 20 teams
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
                'minute': 0
            })
            match_id += 1
            
        # Rotate list using standard Circle Scheduling Algorithm
        rotation = [rotation[0]] + [rotation[-1]] + rotation[1:-1]
        
    return schedule

# Generate full season itineraries on startup
state['season_fixtures_italian'] = build_round_robin_schedule(ITALIAN_TEAMS, 'ITALIAN')
state['season_fixtures_english'] = build_round_robin_schedule(ENGLISH_TEAMS, 'ENGLISH')

def load_league_round_fixtures():
    r = state['current_round']
    
    # If the season completes (19 rounds are done), reset to a new season
    if r > 19:
        state['current_round'] = 1
        r = 1
        init_standings()
        state['season_fixtures_italian'] = build_round_robin_schedule(ITALIAN_TEAMS, 'ITALIAN')
        state['season_fixtures_english'] = build_round_robin_schedule(ENGLISH_TEAMS, 'ENGLISH')

    # Load all 10 fixtures for the current round into live rotation arrays
    state['live_matches_italian'] = state['season_fixtures_italian'][r]
    state['live_matches_english'] = state['season_fixtures_english'][r]
    
    for m in state['live_matches_italian'] + state['live_matches_english']:
        m['status'] = 'LIVE'
        m['minute'] = 0
        m['score'] = '0-0'
        
    # Queue up the next upcoming round fixtures as a dashboard preview
    next_r = r + 1
    if next_r <= 19:
        state['pending_matches_italian'] = state['season_fixtures_italian'][next_r]
        state['pending_matches_english'] = state['season_fixtures_english'][next_r]
    else:
        state['pending_matches_italian'] = []
        state['pending_matches_english'] = []

# Load initial Round 1 games
load_league_round_fixtures()

# --- 3. DYNAMIC TIME THREAD ENGINE ---
def dynamic_engine_loop():
    now = time.time()
    dt = now - state['last_update']
    state['last_update'] = now
    
    # Aviator Core Cycles
    av_elapsed = now - state['aviator']['start']
    if state['aviator']['phase'] == 'BETTING' and av_elapsed > 10:
        state['aviator']['phase'] = 'FLYING'
        state['aviator']['start'] = now
        state['aviator']['multiplier'] = 1.0
    elif state['aviator']['phase'] == 'FLYING':
        state['aviator']['multiplier'] += round(dt * 0.4, 2)
        if state['aviator']['multiplier'] > random.uniform(1.5, 7.0):
            state['aviator']['phase'] = 'BETTING'
            state['aviator']['start'] = now
            state['aviator']['stakes'] = {} 

    if not state['simulation_running']:
        return

    # Process all active matches within the running round
    all_live = state['live_matches_italian'] + state['live_matches_english']
    for match in all_live:
        if match['status'] == 'LIVE':
            match['minute'] += int(dt * 6) # Simulated match duration tick controller
            
            # Realistic probability weightings for scoring parameters
            if random.random() < 0.025: 
                s1, s2 = map(int, match['score'].split('-'))
                if random.choice([True, False]): s1 += 1
                else: s2 += 1
                match['score'] = f"{s1}-{s2}"
            
            if match['minute'] >= 90:
                match['status'] = 'FINISHED'
                finalize_match_statistics(match)
                
    # Proceed to the next matchday round ONLY when all 20 games hit full time
    if all(m['status'] == 'FINISHED' for m in all_live):
        state['current_round'] += 1
        load_league_round_fixtures()

def finalize_match_statistics(match):
    s1, s2 = map(int, match['score'].split('-'))
    t1, t2 = match['t1'], match['t2']
    league = match['league']
    
    standings = state['standings_italian'] if league == 'ITALIAN' else state['standings_english']
    
    standings[t1]['played'] += 1
    standings[t2]['played'] += 1
    
    if s1 > s2:
        standings[t1]['won'] += 1; standings[t1]['points'] += 3
        standings[t2]['lost'] += 1
    elif s2 > s1:
        standings[t2]['won'] += 1; standings[t2]['points'] += 3
        standings[t1]['lost'] += 1
    else:
        standings[t1]['draw'] += 1; standings[t1]['points'] += 1
        standings[t2]['draw'] += 1; standings[t2]['points'] += 1
        
    log_entry = f"[{league}] Rd {state['current_round']} | {match['teams']} ({match['score']})"
    state['match_logs'].append(log_entry)

# --- 4. SECURE API ROUTING PIPELINES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session and session['user'] in users: return redirect(url_for('index'))
    msg = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        
        if email not in users:
            if phone: 
                users[email] = {'password': password, 'phone': phone, 'balance': 0.0, 'bonus': 100.0, 'bonus_locked': True, 'role': 'user', 'bets': []}
                msg = "Welcome! You received 100 KSH bonus. Deposit 50 KSH to unlock it."
                return render_template('login.html', message=msg)
            return render_template('login.html', error="Account missing details.")
        
        if users[email]['password'] == password:
            session['user'] = email
            return redirect(url_for('index'))
    return render_template('login.html')

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

@app.route('/api/aviator/bet', methods=['POST'])
def aviator_bet():
    user = users.get(session.get('user'))
    if not user or state['aviator']['phase'] != 'BETTING':
        return jsonify({'success': False})
    data = request.get_json() or {}
    stake = float(data.get('stake', 0))
    if user['balance'] >= stake and stake >= 10:
        user['balance'] -= stake
        state['house_balance'] += stake
        state['aviator']['stakes'][session['user']] = stake
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/aviator/cashout', methods=['POST'])
def aviator_cashout():
    user = users.get(session.get('user'))
    if not user or state['aviator']['phase'] != 'FLYING':
        return jsonify({'success': False})
    stake = state['aviator']['stakes'].pop(session['user'], None)
    if stake:
        winnings = min(stake * state['aviator']['multiplier'], 300000.0)
        user['balance'] += winnings
        state['house_balance'] -= winnings
        return jsonify({'success': True, 'winnings': winnings})
    return jsonify({'success': False})

@app.route('/admin/toggle', methods=['POST'])
def toggle_simulation():
    user = users.get(session.get('user'), {})
    if user.get('role') != 'admin': return "Forbidden", 403
    data = request.get_json() or {}
    state['simulation_running'] = data.get('run', True)
    return jsonify({'success': True, 'running': state['simulation_running']
