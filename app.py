from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import time
import random

app = Flask(__name__)
app.secret_key = 'swiftpitch_secure_key_2026'

# --- 1. DATA & STATE ---
# House Balance starts at 500,000
house = {'balance': 500000.0}
users = {} # {email: {'password': password, 'balance': balance}}

# Team Lists
ITALIAN_TEAMS = ["Roma", "Juventus", "Lazio", "Napoli", "Fiorentina", "Bologna", "Sassuolo", "Verona", "Atalanta", "Monza"]
ENGLISH_TEAMS = ["Arsenal", "Man City", "Liverpool", "Chelsea", "Man Utd", "Spurs", "Newcastle", "Everton", "Bournemouth", "Brighton"]

# Game Engines
aviator = {'phase': 'BETTING', 'start': time.time(), 'multiplier': 1.0, 'stakes': {}}
match_state = {'start_time': time.time()}

# --- 2. GAME LOGIC ---
def process_game_logic():
    # Aviator Loop
    elapsed = time.time() - aviator['start']
    if aviator['phase'] == 'BETTING' and elapsed > 10:
        aviator['phase'] = 'FLYING'
        aviator['start'] = time.time()
        aviator['multiplier'] = 1.0
    elif aviator['phase'] == 'FLYING':
        aviator['multiplier'] += 0.1
        if aviator['multiplier'] > random.uniform(1.5, 10.0): # Crash
            aviator['phase'] = 'BETTING'
            aviator['start'] = time.time()
            aviator['stakes'] = {} 

# --- 3. ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email not in users:
            users[email] = {'password': password, 'balance': 1000.0} # New user bonus
        session['user'] = email
        return redirect(url_for('index'))
    return '''
    <body style="background:#0b1118; color:white; font-family:sans-serif; text-align:center; padding-top:50px;">
        <h2>SWIFTPITCH LOGIN</h2>
        <form method="POST">
            Email: <input name="email" required><br><br>
            Pass: <input name="password" type="password" required><br><br>
            <button>Login / Create Account</button>
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

@app.route('/deposit', methods=['POST'])
def deposit():
    if 'user' in session:
        amount = float(request.form.get('amount', 0))
        users[session['user']]['balance'] += amount
    return redirect(url_for('index'))

# --- 4. API ENDPOINTS ---
@app.route('/api/state')
def get_state():
    process_game_logic()
    return jsonify({
        'aviator': aviator,
        'house_balance': house['balance'],
        'user_balance': users.get(session.get('user'), {}).get('balance', 0),
        'italian': ITALIAN_TEAMS,
        'english': ENGLISH_TEAMS
    })

@app.route('/api/aviator/bet', methods=['POST'])
def aviator_bet():
    user = session['user']
    stake = float(request.json.get('stake', 0))
    if users[user]['balance'] >= stake:
        users[user]['balance'] -= stake
        house['balance'] += stake
        aviator['stakes'][user] = stake
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/aviator/cashout', methods=['POST'])
def aviator_cashout():
    user = session['user']
    if user in aviator['stakes']:
        stake = aviator['stakes'].pop(user)
        winnings = stake * aviator['multiplier']
        # Rule: Max Payout 300,000
        winnings = min(winnings, 300000)
        users[user]['balance'] += winnings
        house['balance'] -= winnings
        return jsonify({'success': True, 'winnings': winnings})
    return jsonify({'success': False})

if __name__ == '__main__':
    app.run(debug=True)
