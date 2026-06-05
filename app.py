from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import time
import random

app = Flask(__name__)
app.secret_key = 'swiftpitch_secret_2026'

# --- INITIAL STATE & DATA ---
# Goal: House balance at 500k, user registration & wallet support
users = {} # {email: {'password': p, 'balance': b, 'phone': ph}}
house = {'balance': 500000.0}

ITALIAN_TEAMS = ["Roma", "Juventus", "Lazio", "Napoli", "Fiorentina", "Bologna", "Sassuolo", "Verona", "Atalanta", "Monza"]
ENGLISH_TEAMS = ["Arsenal", "Man City", "Liverpool", "Chelsea", "Man Utd", "Spurs", "Newcastle", "Everton", "Bournemouth", "Brighton"]

# --- GAME ENGINES ---
aviator = {'phase': 'BETTING', 'start': time.time(), 'multiplier': 1.0, 'stakes': {}}

def process_game_logic():
    # 1. Aviator Continuous Loop
    elapsed = time.time() - aviator['start']
    if aviator['phase'] == 'BETTING' and elapsed > 10:
        aviator['phase'] = 'FLYING'
        aviator['start'] = time.time()
        aviator['multiplier'] = 1.0
    elif aviator['phase'] == 'FLYING':
        aviator['multiplier'] += 0.1
        # Random crash point
        if aviator['multiplier'] > random.uniform(1.5, 10.0):
            aviator['phase'] = 'BETTING'
            aviator['start'] = time.time()
            aviator['stakes'] = {} # House collects all remaining bets

# --- ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email not in users: # Simple Sign Up
            users[email] = {'password': password, 'balance': 1000.0, 'phone': '000'}
        session['user'] = email
        return redirect(url_for('index'))
    return '''<form method="POST">Email: <input name="email"> Pass: <input name="password" type="password"> <button>Login/Register</button></form>'''

@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('index.html', user=users[session['user']])

@app.route('/api/aviator/bet', methods=['POST'])
def aviator_bet():
    data = request.json
    user = session['user']
    stake = float(data['stake'])
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
        # Limit max payout to 300,000 KSH
        winnings = min(winnings, 300000)
        users[user]['balance'] += winnings
        house['balance'] -= winnings
        return jsonify({'success': True, 'amount': winnings})
    return jsonify({'success': False})

@app.route('/api/state')
def get_state():
    process_game_logic()
    return jsonify({
        'aviator': aviator,
        'house_balance': house['balance'],
        'user_balance': users.get(session.get('user'), {}).get('balance', 0)
    })

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
