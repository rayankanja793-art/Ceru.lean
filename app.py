from flask import Flask, request, render_template_string, redirect, session, url_for
import math
import random
import os

app = Flask(__name__)
# This line ensures your website security key adapts automatically to cloud platforms like Render
app.secret_key = os.environ.get("SECRET_KEY", "super_secret_ligibigi_key_12345")

# ==========================================
# 1. DATABASE (Stored in server memory)
# ==========================================
USERS_DB = {}  
TEAMS = {
    'Inter': {'att': 2.4, 'def': 0.6}, 'Juventus': {'att': 1.7, 'def': 0.5},
    'Milan': {'att': 2.0, 'def': 1.1}, 'Napoli': {'att': 1.9, 'def': 0.9}
}

# ==========================================
# 2. LIGI BIGI MATH CORE ENGINE
# ==========================================
def simulate_match(home, away):
    exp_home = TEAMS[home]['att'] * TEAMS[away]['def']
    exp_away = TEAMS[away]['att'] * TEAMS[home]['def']
    
    def poisson(lam):
        L = math.exp(-lam)
        k, p = 0, 1.0
        while p > L: k += 1; p *= random.random()
        return k - 1
    
    return poisson(exp_home), poisson(exp_away)

# ==========================================
# 3. FRONTEND UI DESIGN (HTML & CSS)
# ==========================================
BASE_CSS = """
<style>
    body { font-family: 'Segoe UI', Arial, sans-serif; background-color: #1a1a1a; color: #fff; margin: 0; padding: 20px; }
    .container { max-width: 600px; margin: 0 auto; background: #2d2d2d; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
    h2 { color: #00ff66; border-bottom: 2px solid #333; padding-bottom: 10px; }
    input[type="text"], input[type="email"], input[type="password"], input[type="number"], select { 
        width: 100%; padding: 12px; margin: 10px 0 20px 0; border: 1px solid #444; border-radius: 6px; background: #1a1a1a; color: white; box-sizing: border-box;
    }
    .btn { background: #00ff66; color: #1a1a1a; font-weight: bold; padding: 12px 20px; border: none; border-radius: 6px; cursor: pointer; width: 100%; font-size: 16px; }
    .btn:hover { background: #00cc52; }
    .balance-card { background: #1f3a24; border: 1px solid #00ff66; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; }
    .alert { background: #ff3333; padding: 10px; border-radius: 6px; margin-bottom: 15px; text-align: center; color: white; }
    .success { background: #00ff66; color: #1a1a1a; padding: 10px; border-radius: 6px; margin-bottom: 15px; text-align: center; font-weight: bold; }
    .logout-link { display: block; text-align: center; margin-top: 15px; color: #aaa; text-decoration: none; }
</style>
"""

REGISTRATION_PAGE = BASE_CSS + """
<div class="container">
    <h2>Ligi Bigi - Create Account 🇰🇪</h2>
    {% if error %}<div class="alert">{{ error }}</div>{% endif %}
    <form method="POST" action="/register">
        <label>Email Address</label>
        <input type="email" name="email" required placeholder="example@gmail.com">
        <label>M-Pesa Phone Number</label>
        <input type="text" name="phone" required placeholder="0712345678">
        <label>Password</label>
        <input type="password" name="password" required placeholder="••••••••">
        <button type="submit" class="btn">Register & Get Started</button>
    </form>
    <a href="/login" class="logout-link">Already have an account? Login here</a>
</div>
"""

LOGIN_PAGE = BASE_CSS + """
<div class="container">
    <h2>Ligi Bigi - User Login</h2>
    {% if error %}<div class="alert">{{ error }}</div>{% endif %}
    <form method="POST" action="/login">
        <label>Email</label>
        <input type="email" name="email" required>
        <label>Password</label>
        <input type="password" name="password" required>
        <button type="submit" class="btn">Login</button>
    </form>
    <a href="/register" class="logout-link">New user? Register here</a>
</div>
"""

DASHBOARD_PAGE = BASE_CSS + """
<div class="container">
    <h2>Ligi Bigi Dashboard</h2>
    <p>Welcome back, <strong>{{ email }}</strong> ({{ phone }})</p>
    <div class="balance-card">
        <h3>Wallet Balance</h3>
        <h1 style="margin: 5px 0; color: #00ff66;">KSh {{ "%.2f"|format(balance) }}</h1>
    </div>
    {% if msg %}<div class="success">{{ msg }}</div>{% endif %}
    {% if error %}<div class="alert">{{ error }}</div>{% endif %}
    <details style="background: #3a3a3a; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
        <summary style="cursor: pointer; font-weight: bold;">💸 Deposit Funds via M-Pesa STK Push</summary>
        <form method="POST" action="/deposit" style="margin-top: 15px;">
            <label>Amount (KSh)</label>
            <input type="number" name="amount" min="10" required placeholder="e.g., 100">
            <button type="submit" class="btn">Trigger STK Push</button>
        </form>
    </details>
    <h3>Place a Virtual Bet</h3>
    <form method="POST" action="/place-bet">
        <label>Select Match</label>
        <select name="match">
            <option value="Inter vs Juventus">Inter vs Juventus</option>
            <option value="Milan vs Napoli">Milan vs Napoli</option>
        </select>
        <label>Your Prediction</label>
        <select name="prediction">
            <option value="1">Home Win (1)</option>
            <option value="X">Draw (X)</option>
            <option value="2">Away Win (2)</option>
        </select>
        <label>Stake Amount (KSh)</label>
        <input type="number" name="stake" min="5" required placeholder="Minimum KSh 5">
        <button type="submit" class="btn" style="background: #ffcc00; color: #1a1a1a;">Place Bet & Run Simulation</button>
    </form>
    <a href="/logout" class="logout-link">Sign Out</a>
</div>
"""

# ==========================================
# 4. BACKEND ROUTING LOGIC
# ==========================================
@app.route('/')
def home():
    if 'email' in session:
        user = USERS_DB.get(session['email'])
        if user:
            return render_template_string(DASHBOARD_PAGE, email=session['email'], phone=user['phone'], balance=user['balance'], msg=request.args.get('msg'), error=request.args.get('error'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        if email in USERS_DB:
            return render_template_string(REGISTRATION_PAGE, error="Email already registered!")
        USERS_DB[email] = {'phone': phone, 'password': password, 'balance': 0.0}
        session['email'] = email
        return redirect(url_for('home', msg="Registration successful!"))
    return render_template_string(REGISTRATION_PAGE)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email in USERS_DB and USERS_DB[email]['password'] == password:
            session['email'] = email
            return redirect(url_for('home'))
        return render_template_string(LOGIN_PAGE, error="Invalid Email or Password.")
    return render_template_string(LOGIN_PAGE)

@app.route('/deposit', methods=['POST'])
def deposit():
    if 'email' not in session: return redirect(url_for('login'))
    amount = float(request.form['amount'])
    USERS_DB[session['email']]['balance'] += amount
    return redirect(url_for('home', msg=f"STK Push simulated! Credited KSh {amount}."))

@app.route('/place-bet', methods=['POST'])
def place_bet():
    if 'email' not in session: return redirect(url_for('login'))
    user = USERS_DB[session['email']]
    match = request.form['match']
    prediction = request.form['prediction']
    stake = float(request.form['stake'])
    
    if user['balance'] < stake:
        return redirect(url_for('home', error="Insufficient funds!"))
    
    user['balance'] -= stake
    home_team, away_team = match.split(" vs ")
    h_g, a_g = simulate_match(home_team, away_team)
    
    actual_outcome = "X"
    if h_g > a_g: actual_outcome = "1"
    elif h_g < a_g: actual_outcome = "2"
    
    if prediction == actual_outcome:
        winnings = stake * 2.5
        user['balance'] += winnings
        result_msg = f"🎉 WINNER! Result: {h_g}-{a_g}. Credited KSh {winnings}."
    else:
        result_msg = f"❌ LOST. Result was {h_g}-{a_g}."
        
    return redirect(url_for('home', msg=result_msg))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Configures the application to use the custom dynamic port provided by Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
