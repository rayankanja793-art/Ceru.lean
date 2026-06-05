from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import time
import random

app = Flask(__name__)
app.secret_key = 'swiftpitch_high_roller_2026'

# --- 1. SYSTEM DATA BOARDS ---
ITALIAN_TEAMS = ["Roma", "Juventus", "Milaan Reds", "Torino", "Fiorentina", "Bologna", "Sassuolo", "Lazio", "Verona", "Atlanta", "Monza", "Cremonese", "Leece", "Udinese", "Spenzia", "Empoli", "Napoli", "Samdoria", "Salernitana", "Milan Blues"]
ENGLISH_TEAMS = ["Manchester blue", "spurs", "A.Villa", "London blues", "Manchester red", "New castle", "Everton", "Bournemouth", "N. forrest", "Brighton", "London reds", "Brentford", "Wolves", "west Ham", "Southampton", "Fulham", "Liverpool", "C.Palace", "Leicester", "Leeds"]

# Shared Platform State Engine
state = {
    'house_balance': 500000.0,      # Rule 2: 500,000 KSH Initial House Bank
    'simulation_running': True,     # Rule 6: Admin switch control
    'last_update': time.time(),
    'current_round': 1,
    'live_matches': [],
    'pending_matches': [],
    'match_logs': [],
    'standings': {},
    'aviator': {'phase': 'BETTING', 'start': time.time(), 'multiplier': 1.0, 'stakes': {}}
}

# In-Memory Database
users = {
    'admin@swiftpitch.com': {'password': 'adminpassword', 'phone': '0700000000', 'balance': 0.0, 'bonus': 0.0, 'bonus_locked': False, 'role': 'admin', 'bets': []}
}

# Initialize league scoreboard standings
for team in ITALIAN_TEAMS + ENGLISH_TEAMS:
    state['standings'][team] = {'played': 0, 'won': 0, 'draw': 0, 'lost': 0, 'points': 0}

# --- 2. CORE SIMULATION SIMULATOR ---
def generate_fixtures():
    """Generates live pairings and sets up the subsequent round."""
    all_teams = ITALIAN_TEAMS + ENGLISH_TEAMS
    random.shuffle(all_teams)
    
    # Take first 4 teams for live match simulations, next 4 for pending queue
    state['live_matches'] = [
        {'id': 1, 'teams': f"{all_teams[0]} vs {all_teams[1]}", 't1': all_teams[0], 't2': all_teams[1], 'score': '0-0', 'status': 'LIVE', 'minute': 0},
        {'id': 2, 'teams': f"{all_teams[2]} vs {all_teams[3]}", 't1': all_teams[2], 't2': all_teams[3], 'score': '0-0', 'status': 'LIVE', 'minute': 0}
    ]
    state['pending_matches'] = [
        {'teams': f"{all_teams[4]} vs {all_teams[5]}"},
        {'teams': f"{all_teams[6]} vs {all_teams[7]}"}
    ]

generate_fixtures()

def dynamic_engine_loop():
    """Processes real-time increments for soccer simulations & aviator phases."""
    now = time.time()
    dt = now - state['last_update']
    state['last_update'] = now
    
    # Aviator Live Thread Simulation
    av_elapsed = now - state['aviator']['start']
    if state['aviator']['phase'] == 'BETTING' and av_elapsed > 10:
        state['aviator']['phase'] = 'FLYING'
        state['aviator']['start'] = now
        state['aviator']['multiplier'] = 1.0
    elif state['aviator']['phase'] == 'FLYING':
        state['aviator']['multiplier'] += round(dt * 0.3, 2)
        if state['aviator']['multiplier'] > random.uniform(1.5, 8.0):
            state['aviator']['phase'] = 'BETTING'
            state['aviator']['start'] = now
            state['aviator']['stakes'] = {} # House clears uncashed configurations

    # Soccer Match Progression Engine
    if not state['simulation_running']:
        return

    for match in state['live_matches']:
        if match['status'] == 'LIVE':
            match['minute'] += int(dt * 4) # Accelerated simulation time frames
            if random.random() < 0.05: # Chance of scoring a goal
                s1, s2 = map(int, match['score'].split('-'))
                if random.choice([True, False]): s1 += 1
                else s2 += 1
                match['score'] = f"{s1}-{s2}"
            
            if match['minute'] >= 90:
                match['status'] = 'FINISHED'
                finalize_match_statistics(match)
                
    # If all current live matches are finished, cycle to next round
    if all(m['status'] == 'FINISHED' for m in state['live_matches']):
        state['current_round'] += 1
        generate_fixtures()

def finalize_match_statistics(match):
    s1, s2 = map(int, match['score'].split('-'))
    t1, t2 = match['t1'], match['t2']
    
    state['standings'][t1]['played'] += 1
    state['standings'][t2]['played'] += 1
    
    if s1 > s2:
        state['standings'][t1]['won'] += 1; state['standings'][t1]['points'] += 3
        state['standings'][t2]['lost'] += 1
        winner = t1
    elif s2 > s1:
        state['standings'][t2]['won'] += 1; state['standings'][t2]['points'] += 3
        state['standings'][t1]['lost'] += 1
        winner = t2
    else:
        state['standings'][t1]['draw'] += 1; state['standings'][t1]['points'] += 1
        state['standings'][t2]['draw'] += 1; state['standings'][t2]['points'] += 1
        winner = 'DRAW'
        
    log_entry = f"Round {state['current_round']} | {match['teams']} ended ({match['score']})"
    state['match_logs'].append(log_entry)
    evaluate_user_bets(match, winner)

def evaluate_user_bets(match, winner):
    """Processes active bet tickets to settle open, won, or lost status loops."""
    for email, user in users.items():
        for bet in user.get('bets', []):
            if bet['status'] == 'OPEN' and bet['match_id'] == match['id']:
                if bet['predicted_winner'] == winner:
                    bet['status'] = 'WON'
                    user['balance'] += bet['payout']
                    state['house_balance'] -= bet['payout'] # Auto-deduct house bank
                else:
                    bet['status'] = 'LOST'

# --- 3. SECURE AUTH & REGISTRATION ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session: return redirect(url_for('index'))
    msg = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        
        # Rule 7: Dynamic Registration/Login routing switch
        if email not in users:
            if phone: # Registration payload context
                users[email] = {
                    'password': password, 'phone': phone, 'balance': 0.0,
                    'bonus': 100.0, 'bonus_locked': True, 'role': 'user', 'bets': []
                }
                msg = "Welcome to SwiftPitch! You have received 100 KSH bonus. You are supposed to deposit 50 KSH to unlock your bonus."
                return render_template('login.html', message=msg)
            else:
                return render_template('login.html', error="Account does not exist. Fill out registration fields.")
        
        if users[email]['password'] == password:
            session['user'] = email
            return redirect(url_for('index'))
    return render_template('login.html')

# --- 4. SYSTEM TRANSACTION CONTROLLERS ---
@app.route('/deposit', methods=['POST'])
def deposit():
    user = users.get(session.get('user'))
    if user:
        amount = float(request.form.get('amount', 0))
        if amount >= 10.0: # Rule 3: 10 Bob Minimum Deposit validation check
            user['balance'] += amount
            state['house_balance'] += amount # Auto-add house bank
            if user['bonus_locked'] and amount >= 50.0: # Unlock Bonus Requirement Trigger
                user['balance'] += user['bonus']
                user['bonus'] = 0.0
                user['bonus_locked'] = False
        else:
            return "Minimum deposit limit is 10 KSH.", 400
    return redirect(url_for('index'))

@app.route('/withdraw', methods=['POST'])
def withdraw():
    user = users.get(session.get('user'))
    if user:
        amount = float(request.form.get('amount', 0))
        if amount >= 100.0: # Rule 3: 100 KSH Minimum Withdrawal condition check
            if user['balance'] >= amount:
                user['balance'] -= amount
                state['house_balance'] -= amount
            else:
                return "Insufficient funds.", 400
        else:
            return "Minimum withdrawal limit is 100 KSH.", 400
    return redirect(url_for('index'))

# --- 5. ADMINISTRATION CONTROL PANEL ---
@app.route('/admin/toggle', methods=['POST'])
def toggle_simulation():
    """Rule 6: Allows administrative privileges to control system clocks."""
    user = users.get(session.get('user'), {})
    if user.get('role') != 'admin': return "Forbidden", 403
    
    data = request.get_json() or {}
    state['simulation_running'] = data.get('run', True)
    return jsonify({'success': True, 'running': state['simulation_running']})

# --- 6. ASYNC STATE INTERFACE REFRESHERS ---
@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('index.html', user=users[session['user']])

@app.route('/api/state')
def get_state():
    dynamic_engine_loop()
    current_user = users.get(session.get('user'), {'balance': 0.0, 'bonus': 0.0, 'bonus_locked': False, 'role': 'user', 'bets': []})
    return jsonify({
        'house_balance': state['house_balance'],
        'simulation_running': state['simulation_running'],
        'live_matches': state['live_matches'],
        'pending_matches': state['pending_matches'],
        'match_logs': state['match_logs'],
        'standings': state['standings'],
        'aviator': state['aviator'],
        'user_balance': current_user['balance'],
        'user_bonus': current_user['bonus'],
        'user_bonus_locked': current_user['bonus_locked'],
        'user_role': current_user['role'],
        'user_bets': current_user.get('bets', [])
    })

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
