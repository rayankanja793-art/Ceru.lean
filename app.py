from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import time
import random

app = Flask(__name__)
app.secret_key = 'swiftpitch_secure_key_2026'

# --- 1. STATE & BALANCES ---
# 2. House Balance starts exactly at 500,000 KSH
house = {'balance': 500000.0}
users = {} 

ITALIAN_TEAMS = ["Roma", "Juventus", "Lazio", "Napoli", "Fiorentina"]
ENGLISH_TEAMS = ["Arsenal", "Man City", "Liverpool", "Chelsea", "Man Utd"]

# 1. Continuous Game Engines
aviator = {'phase': 'BETTING', 'start': time.time(), 'multiplier': 1.0, 'stakes': {}}
live_matches = []
match_timer = time.time()

def generate_matches():
    global live_matches
    live_matches = []
    teams = ITALIAN_TEAMS + ENGLISH_TEAMS
    for i in range(3):
        t1, t2 = random.sample(teams, 2)
        live_matches.append({'match': f"{t1} vs {t2}", 'score': f"{random.randint(0,3)} - {random.randint(0,3)}", 'minute': random.randint(10, 89)})

generate_matches()

def process_game_logic():
    global match_timer
    
    # Aviator Loop
    elapsed = time.time() - aviator['start']
    if aviator['phase'] == 'BETTING' and elapsed > 10:
        aviator['phase'] = 'FLYING'
        aviator['start'] = time.time()
        aviator['multiplier'] = 1.0
    elif aviator['phase'] == 'FLYING':
        aviator['multiplier'] += 0.1
        if aviator['multiplier'] > random.uniform(1.5, 10.0):
            aviator['phase'] = 'BETTING'
            aviator['start'] = time.time()
            aviator['stakes'] = {} # 5. House automatically keeps lost bets
            
    # Continuous Matches Loop (Updates scores every 10 seconds)
    if time.time() - match_timer > 10:
        generate_matches()
        match_timer = time.time()

# --- 2. USER ROUTES ---
# 7. Create Accounts and Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email not in users:
            users[email] = {'password': password, 'balance': 1000.0}
        session['user'] = email
        return redirect(url_for('index'))
    return '''
    <body style="background:#0b1118; color:white; font-family:sans-serif; text-align:center; padding-top:50px;">
        <h2>SWIFTPITCH</h2>
        <form method="POST">
            Email: <input name="email" required><br><br>
            Pass: <input name="password" type="password" required><br><br>
            <button style="padding:10px; background:#00ff66;">Login / Register</button>
        </form>
    </body>'''

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('index.html', user=users[session['user']])

# --- 3. BANKING ROUTES ---
# 4. Places to Deposit and Withdraw
@app.route('/banking', methods=['POST'])
def banking():
    if 'user' in session:
        action = request.form.get('action')
        amount = float(request.form.get('amount', 0))
        if action == 'deposit':
            users[session['user']]['balance'] += amount
        elif action == 'withdraw' and users[session['user']]['balance'] >= amount:
            users[session['user']]['balance'] -= amount
    return redirect(url_for('index'))

# --- 4. API ROUTES ---
@app.route('/api/state')
def get_state():
    process_game_logic()
    return jsonify({
        'aviator': aviator,
        'live_matches': live_matches,
        'house_balance': house['balance'],
        'user_balance': users.get(session.get('user'), {}).get('balance', 0)
    })

@app.route('/api/aviator/bet', methods=['POST'])
def aviator_bet():
    user = session['user']
    stake = float(request.json.get('stake', 0))
    if users[user]['balance'] >= stake:
        users[user]['balance'] -= stake
        house['balance'] += stake # 5. Company balance adds automatically
        aviator['stakes'][user] = stake
        return jsonify({'success': True})
    return jsonify({'success': False})

# 6. Aviator Cashout
@app.route('/api/aviator/cashout', methods=['POST'])
def aviator_cashout():
    user = session['user']
    if user in aviator['stakes']:
        stake = aviator['stakes'].pop(user)
        winnings = stake * aviator['multiplier']
        
        # 3. Winning rate capped at 300,000 KSH
        winnings = min(winnings, 300000)
        
        users[user]['balance'] += winnings
        house['balance'] -= winnings # 5. Company balance deducts automatically
        return jsonify({'success': True, 'winnings': winnings})
    return jsonify({'success': False})

if __name__ == '__main__':
    app.run(debug=True)
