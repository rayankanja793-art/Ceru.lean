from flask import Flask, render_template, request, redirect, session, url_for, flash
import threading
import time
import random

app = Flask(__name__)
app.secret_key = 'swiftpitch_secret_2026'

# --- DATA STORAGE (Use SQL in production) ---
users = {'admin@swiftpitch.com': {'password': 'adminpassword', 'balance': 0, 'bonus_unlocked': True, 'is_admin': True}}
bets = [] 

# --- SIMULATION STATE ---
state = {
    'phase': 'BETTING',
    'time': 60,
    'is_running': False,
    'round': 1
}

def simulation_engine():
    while True:
        if state['is_running']:
            time.sleep(1)
            state['time'] -= 1
            if state['time'] <= 0:
                if state['phase'] == 'BETTING':
                    state['phase'] = 'PLAYING'
                    state['time'] = 55
                else:
                    state['phase'] = 'BETTING'
                    state['time'] = 60
                    state['round'] += 1
        else:
            time.sleep(1)

threading.Thread(target=simulation_engine, daemon=True).start()

# --- ROUTES ---
@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('index.html', state=state, user=users[session['user']])

@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    # Award 100 bonus
    users[email] = {'password': request.form['password'], 'balance': 100, 'bonus_unlocked': False, 'is_admin': False}
    session['user'] = email
    flash("Welcome! You received 100 KSH bonus. Deposit 50 KSH to unlock it.")
    return redirect(url_for('index'))

@app.route('/deposit', methods=['POST'])
def deposit():
    amount = float(request.form['amount'])
    user = users[session['user']]
    user['balance'] += amount
    if amount >= 50:
        user['bonus_unlocked'] = True
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not users.get(session.get('user'), {}).get('is_admin'): return "Access Denied", 403
    if request.method == 'POST':
        state['is_running'] = (request.form['action'] == 'start')
    return render_template('admin.html', state=state)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['user'] = request.form['email']
        return redirect(url_for('index'))
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
