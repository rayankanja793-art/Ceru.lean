from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import time
import random

app = Flask(__name__)
app.config.update(SECRET_KEY='swiftpitch_secret_2026')

# --- DATA ---
ITALIAN_TEAMS = ["Roma", "Juventus", "Lazio", "Napoli", "Fiorentina", "Bologna", "Sassuolo", "Verona", "Atalanta", "Monza"]
ENGLISH_TEAMS = ["Arsenal", "Man City", "Liverpool", "Chelsea", "Man Utd", "Spurs", "Newcastle", "Everton", "Bournemouth", "Brighton"]

users = {'admin@swiftpitch.com': {'password': 'adminpassword', 'is_admin': True, 'balance': 1000.0}}
state = {'company_balance': 250000.0, 'start_time': time.time()}

# --- AVIATOR ENGINE ---
aviator_game = {'phase': 'BETTING', 'start_time': time.time(), 'multiplier': 1.0}

def update_game_engines():
    # Aviator Logic
    elapsed = time.time() - aviator_game['start_time']
    if aviator_game['phase'] == 'BETTING' and elapsed > 10:
        aviator_game['phase'] = 'FLYING'
        aviator_game['start_time'] = time.time()
        aviator_game['multiplier'] = 1.0
    elif aviator_game['phase'] == 'FLYING':
        aviator_game['multiplier'] += 0.1
        if aviator_game['multiplier'] > random.uniform(2.0, 10.0):
            aviator_game['phase'] = 'BETTING'
            aviator_game['start_time'] = time.time()

# --- ROUTES ---
@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('index.html', user=users[session['user']])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['user'] = request.form.get('email')
        return redirect(url_for('index'))
    return '<form method="POST">Email: <input type="text" name="email"><button>Login</button></form>'

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/state')
def get_state():
    update_game_engines() # Keep games moving
    return jsonify({
        'aviator': aviator_game,
        'italian_teams': ITALIAN_TEAMS,
        'english_teams': ENGLISH_TEAMS
    })

if __name__ == '__main__':
    app.run(debug=True)
