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

# Precise Cycle Constants (Seconds)
BETTING_WINDOW = 72.0
MATCH_WINDOW = 55.0

# Global Application State Engine
state = {
    'house_balance': 750000.0,
    'simulation_running': True,     
    'last_update': time.time(),
    'current_round': 1,
    'league_phase': 'BETTING',       # 'BETTING' or 'LIVE'
    'phase_start_time': time.time(),
    'season_fixtures_italian': {},
    'season_fixtures_english': {},
    'live_matches_italian': [],
    'live_matches_english': [],
    'match_logs': [],
    'sports_bets': [],               # Universal Ledger for Singles and Multi-bets
    'standings_italian': {},
    'standings_english': {},
    'aviator': {'phase': 'BETTING', 'start': time.time(), 'multiplier': 1.0, 'stakes': {}}
}

users = {
    'admin@swiftpitch.com': {'password': 'adminpassword', 'phone': '0700000000', 'balance': 0.0, 'bonus': 0.0, 'bonus_locked': False, 'role': 'admin'},
    'player@swiftpitch.com': {'password': 'password123', 'phone': '0711223344', 'balance': 5000.0, 'bonus': 100.0, 'bonus_locked': True, 'role': 'user'}
}

def init_standings():
    state['standings_italian'] = {team: {'played': 0, 'won': 0, 'draw': 0, 'lost': 0, 'points': 0} for team in ITALIAN_TEAMS}
    state['standings_english'] = {team: {'played': 0, 'won': 0, 'draw': 0, 'lost': 0, 'points': 0} for team in ENGLISH_TEAMS}

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
                'odds_home': round(random.uniform(1.4, 3.2), 2),
                'odds_draw': round(random.uniform(2.6, 3.6), 2),
                'odds_away': round(random.uniform(2.1, 4.5), 2),
                'timeline': []  # Pre-generated timeline arrays
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
    
    # Initialize as pending for the betting countdown window
    for m in state['live_matches_italian'] + state['live_matches_english']:
        m['status'] = 'BETTING'
        m['minute'] = 0
        m['score'] = '0-0'
        m['timeline'] = []

def precalculate_match_events():
    """Generates goals and timelines evenly spread across the 55s simulation window"""
    for m in state['live_matches_italian'] + state['live_matches_english']:
        m['status'] = 'LIVE'
        gh = random.choices([0, 1, 2, 3], weights=[40, 35, 18, 7])[0]
        ga = random.choices([0, 1, 2, 3], weights=[45, 35, 15, 5])[0]
        
        timeline = []
        for _ in range(gh): timeline.append({'min': random.randint(1, 89), 'side': 'H'})
        for _ in range(ga): timeline.append({'min': random.randint(1, 89), 'side': 'A'})
        m['timeline'] = sorted(timeline, key=lambda x: x['min'])

# Initialize leagues
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
        if state['aviator']['multiplier'] > random.uniform(1.2, 5.0):
            state['aviator']['phase'] = 'BETTING'
            state['aviator']['start'] = now
            state['aviator']['stakes'] = {}

    if not state['simulation_running']:
        return

    # Unified Match Phase Scheduler
    elapsed_phase = now - state['phase_start_time']
    
    if state['league_phase'] == 'BETTING':
        if elapsed_phase >= BETTING_WINDOW:
            # Transit from 72s Betting Window into 55s Live Action
            state['league_phase'] = 'LIVE'
            state['phase_start_time'] = now
            precalculate_match_events()
            
    elif state['league_phase'] == 'LIVE':
        if elapsed_phase >= MATCH_WINDOW:
            # End of 55s Live Match Phase
            finalize_and_settle_round()
            state['current_round'] += 1
            state['league_phase'] = 'BETTING'
            state['phase_start_time'] = now
            load_league_round_fixtures()
        else:
            # Map elapsed seconds to full 90 minutes
            ratio = elapsed_phase / MATCH_WINDOW
            current_game_minute = int(ratio * 90)
            
            all_live = state['live_matches_italian'] + state['live_matches_english']
            for m in all_live:
                m['minute'] = current_game_minute
                # Evaluate real-time live scores from pre-calculated event timeline
                home_goals = sum(1 for g in m['timeline'] if g['min'] <= current_game_minute and g['side'] == 'H')
                away_goals = sum(1 for g in m['timeline'] if g['min'] <= current_game_minute and g['side'] == 'A')
                m['score'] = f"{home_goals}-{away_goals}"

def finalize_and_settle_round():
    all_live = state['live_matches_italian'] + state['live_matches_english']
    match_map = {m['id']: m for m in all_live}
    
    for m in all_live:
        m['status'] = 'FINISHED'
        m['minute'] = 90
        s1, s2 = map(int, m['score'].split('-'))
        t1, t2 = m['t1'], m['t2']
        standings = state['standings_italian'] if m['league'] == 'ITALIAN' else state['standings_english']
        
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
            
        state['match_logs'].append(f"[{m['league']}] Rd {state['current_round']} | {m['teams']} ({m['score']})")

    # --- MULTI-BET ACCUMULATOR SETTLEMENT ENGINE ---
    for bet in state['sports_bets']:
        if bet['status'] != 'PENDING':
            continue
            
        all_selections_resolved = True
        any_selection_lost = False
        
        for sel in bet['selections']:
            m = match_map.get(sel['match_id'])
            if m:
                s1, s2 = map(int, m['score'].split('-'))
                actual_outcome = '1' if s1 > s2 else ('2' if s2 > s1 else 'X')
                if actual_outcome == sel['prediction']:
                    sel['status'] = 'WON'
                else:
                    sel['status'] = 'LOST'
                    any_selection_lost = True
            else:
                all_selections_resolved = False
                
        if any_selection_lost:
            bet['status'] = 'LOST'
        elif all_selections_resolved and all(s['status'] == 'WON' for s in bet['selections']):
            bet['status'] = 'WON'
            payout = bet['stake'] * bet['total_odds']
            user_profile = users.get(bet['user'])
            if user_profile:
                user_profile['balance'] += payout
            state['house_balance'] -= payout

# --- MULTI-BET PLACEMENT ENDPOINT ---
@app.route('/api/sports/bet', methods=['POST'])
def place_sports_bet():
    user = users.get(session.get('user'))
    if not user: return jsonify({'success': False, 'message': 'Unauthorized context'})
    if state['league_phase'] != 'BETTING':
        return jsonify({'success': False, 'message': 'Betslip locked! Matches are already in progress.'})
        
    data = request.get_json() or {}
    selections = data.get('selections', []) # Format: [{'match_id':X, 'prediction':Y}]
    stake = float(data.get('stake', 0))
    
    if len(selections) == 0: return jsonify({'success': False, 'message': 'Betslip is empty'})
    if stake < 10.0: return jsonify({'success': False, 'message': 'Minimum selection wager is 10 KSH'})
    if user['balance'] < stake: return jsonify({'success': False, 'message': 'Insufficient account balance'})
    
    all_live = state['live_matches_italian'] + state['live_matches_english']
    match_map = {m['id']: m for m in all_live}
    
    processed_selections = []
    accumulated_odds = 1.0
    seen_matches = set()
    
    for sel in selections:
        mid = int(sel['match_id'])
        pred = sel['prediction']
        
        if mid in seen_matches:
            return jsonify({'success': False, 'message': 'Combining outcomes from the same match is invalid'})
        seen_matches.add(mid)
        
        m = match_map.get(mid)
        if not m: return jsonify({'success': False, 'message': 'Match scope expired'})
        
        if pred == '1': o = m['odds_home']
        elif pred == 'X': o = m['odds_draw']
        elif pred == '2': o = m['odds_away']
        else: return jsonify({'success': False, 'message': 'Invalid selection profile'})
        
        accumulated_odds *= o
        processed_selections.append({
            'match_id': mid,
            'teams': m['teams'],
            'prediction': pred,
            'odds': o,
            'status': 'PENDING'
        })
        
    accumulated_odds = round(accumulated_odds, 2)
    user['balance'] -= stake
    state['house_balance'] += stake
    
    state['sports_bets'].append({
        'user': session['user'],
        'type': 'SINGLE' if len(processed_selections) == 1 else 'MULTI-BET',
        'stake': stake,
        'total_odds': accumulated_odds,
        'status': 'PENDING',
        'selections': processed_selections
    })
    return jsonify({'success': True, 'message': 'Betslip booked successfully!'})

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
    
    now = time.time()
    elapsed = now - state['phase_start_time']
    rem = (BETTING_WINDOW if state['league_phase'] == 'BETTING' else MATCH_WINDOW) - elapsed
    
    user_slips = []
    for b in state['sports_bets']:
        if b['user'] == session.get('user'):
            user_slips.append({
                'type': b['type'],
                'stake': b['stake'],
                'total_odds': b['total_odds'],
                'status': b['status'],
                'desc': ", ".join([f"{s['teams']} ({s['prediction']})" for s in b['selections']])
            })
            
    return jsonify({
        'house_balance': state['house_balance'] if is_admin else None, 
        'current_round': state['current_round'],
        'league_phase': state['league_phase'],
        'time_remaining': max(0, int(rem)),
        'live_matches': state['live_matches_italian'] + state['live_matches_english'],
        'match_logs': state['match_logs'][-8:],
        'standings_italian': state['standings_italian'],
        'standings_english': state['standings_english'],
        'aviator': {'phase': state['aviator']['phase'], 'multiplier': state['aviator']['multiplier']},
        'user_balance': curr_user['balance'],
        'user_bonus': curr_user.get('bonus', 0),
        'user_bonus_locked': curr_user.get('bonus_locked', False),
        'user_role': curr_user['role'],
        'my_slips': user_slips[-5:]
    })

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
        error = "Invalid profile."
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/deposit', methods=['POST'])
def deposit():
    user = users.get(session.get('user'))
    if user:
        amount = float(request.form.get('amount', 0))
        if amount >= 10.0:
            user['balance'] += amount
            state['house_balance'] += amount
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
