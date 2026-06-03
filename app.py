from flask import Flask, render_template, request, redirect, session, url_for, flash
import threading
import time
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure random string

# --- DATABASE MOCKS ---
# In a production app, replace these with a real database (e.g., PostgreSQL)
users = {}
bets = []

# --- SIMULATION ENGINE STATE ---
engine_state = {
    'phase': 'BETTING',      # 'BETTING' or 'PLAYING'
    'time_remaining': 60,    # Starts at 60s
    'is_running': False,     # Controlled by Admin
    'round': 1
}

def simulation_loop():
    while True:
        if engine_state['is_running']:
            time.sleep(1)
            engine_state['time_remaining'] -= 1
            
            if engine_state['time_remaining'] <= 0:
                if engine_state['phase'] == 'BETTING':
                    engine_state['phase'] = 'PLAYING'
                    engine_state['time_remaining'] = 55 # Match duration
                else:
                    engine_state['phase'] = 'BETTING'
                    engine_state['time_remaining'] = 60
                    engine_state['round'] += 1
                    # Logic to settle bets and update standings goes here
        else:
            time.sleep(1) # Wait if paused

# Start the simulation in a background thread
threading.Thread(target=simulation_loop, daemon=True).start()

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html', state=engine_state)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('is_admin'):
        return "Unauthorized", 403
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'start': engine_state['is_running'] = True
        if action == 'stop': engine_state['is_running'] = False
    
    return render_template('admin.html', state=engine_state)

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Logic for 100 KSH bonus + 50 KSH deposit requirement
    return "Registration Page"

if __name__ == '__main__':
    app.run(debug=True)
