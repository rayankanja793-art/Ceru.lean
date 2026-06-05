from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import time
import random

app = Flask(__name__)
app.config.update(SECRET_KEY='swiftpitch_secret_2026')

# --- DATA: TEAMS & CONFIG ---
ITALIAN_TEAMS = ["Roma", "Juventus", "Milaan Reds", "Torino", "Fiorentina", "Bologna", "Sassuolo", "Lazio", "Verona", "Atlanta", "Monza", "Cremonese", "Leece", "Udinese", "Spenzia", "Empoli", "Napoli", "Samdoria", "Salernitana", "Milan Blues"]
ENGLISH_TEAMS = ["Manchester blue", "spurs", "A.Villa", "London blues", "Manchester red", "New castle", "Everton", "Bournemouth", "N. forrest", "Brighton", "London reds", "Brentford", "Wolves", "west Ham", "Southampton", "Fulham", "Liverpool", "C.Palace", "Leicester", "Leeds"]

users = {
    'admin@swiftpitch.com': {'password': 'adminpassword', 'balance': 0.0, 'is_admin': True}
}

# --- AVIATOR ENGINE ---
aviator_game = {
    'phase': 'BETTING',
    'phase_start_time': time.time(),
    'crash_multiplier': 2.50
}

def update_aviator_loop():
    elapsed = time.time() - aviator_game['phase_start_time']
    if aviator_game['phase'] == 'BETTING' and elapsed >= 10:
        aviator_game['phase'] = 'FLYING'
        aviator_game['phase_start_time'] = time.time()
        aviator_game['crash_multiplier'] = round(random.uniform(1.0, 5.0), 2)
    elif aviator_game['phase'] == 'FLYING' and elapsed >= 5:
        aviator_game['phase'] = 'BETTING'
        aviator_game['phase_start_time'] = time.time()

# --- ROUTES ---
@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('index.html', user=users[session['user']])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        if email in users:
            session['user'] = email
            return redirect(url_for('index'))
    return '<form method="POST">Email: <input type="text" name="email"><button>Login</button></form>'

@app.route('/api/aviator/state')
def aviator_state():
    update_aviator_loop()
    return jsonify({
        'phase': aviator_game['phase'],
        'multiplier': aviator_game['crash_multiplier'] if aviator_game['phase'] == 'FLYING' else 1.0
    })

@app.route('/api/state')
def get_state():
    return jsonify({
        'italian_teams': ITALIAN_TEAMS,
        'english_teams': ENGLISH_TEAMS
    })

if __name__ == '__main__':
    app.run(debug=True)
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
