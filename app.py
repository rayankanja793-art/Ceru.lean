from flask import Flask, request, render_template_string, redirect, session, url_for
import math
import random
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super_secret_ligibigi_key_12345")

# ==========================================
# 1. ENHANCED DATABASE (Matches your image teams)
# ==========================================
USERS_DB = {}  
TEAMS = {
    'Milan Blues': {'att': 2.2, 'def': 0.8, 'odds_1': '2.15', 'odds_X': '3.27', 'odds_2': '3.56'},
    'Juventus': {'att': 1.8, 'def': 0.9},
    'Sampdoria': {'att': 1.2, 'def': 1.5, 'odds_1': '3.67', 'odds_X': '4.02', 'odds_2': '1.88'},
    'Bologna': {'att': 2.0, 'def': 1.0},
    'Lazio': {'att': 2.1, 'def': 1.1, 'odds_1': '1.97', 'odds_X': '3.45', 'odds_2': '3.93'},
    'Napoli': {'att': 1.9, 'def': 1.0},
    'Spezia': {'att': 1.5, 'def': 1.3, 'odds_1': '1.88', 'odds_X': '3.51', 'odds_2': '4.22'},
    'Salernitana': {'att': 1.4, 'def': 1.4}
}

# Explicit list of active matches shown in your image layout
MATCH_LIST = [
    ('Milan Blues', 'Juventus', '2.15', '3.27', '3.56'),
    ('Sampdoria', 'Bologna', '3.67', '4.02', '1.88'),
    ('Lazio', 'Napoli', '1.97', '3.45', '3.93'),
    ('Spezia', 'Salernitana', '1.88', '3.51', '4.22')
]

# ==========================================
# 2. LIGI BIGI MATH CORE ENGINE
# ==========================================
def simulate_match(home, away):
    exp_home = TEAMS[home]['att'] * TEAMS[away]['def']
    exp_away = TEAMS[away]['att'] * TEAMS[home]['att'] # Baseline defensive check
    
    def poisson(lam):
        L = math.exp(-lam)
        k, p = 0, 1.0
        while p > L: k += 1; p *= random.random()
        return k - 1
    
    return poisson(exp_home), poisson(exp_away)

# ==========================================
# 3. PREMIUM UI STYLING (Replica of your image)
# ==========================================
PREMIUM_CSS = """
<style>
    body { font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0b1118; color: #fff; margin: 0; padding: 0; }
    .top-header { background-color: #17212e; padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #233246; }
    .logo { font-size: 22px; font-weight: 900; italic; color: #fff; letter-spacing: -1px; }
    .logo span { background: #ffd700; color: #000; padding: 2px 6px; border-radius: 4px; margin-left: 2px; }
    .balance-badge { background-color: #1a3c22; border: 1px solid #00cc52; padding: 6px 14px; border-radius: 6px; color: #00ff66; font-weight: bold; font-size: 14px; }
    
    /* League Selector Tabs */
    .league-tabs { display: flex; background: #1c2a39; padding: 5px 10px; gap: 15px; overflow-x: auto; border-bottom: 2px solid #121d28; }
    .league-tab { text-align: center; color: #8fa0b5; font-size: 11px; padding: 5px 8px; cursor: pointer; text-decoration: none; min-width: 50px;}
    .league-tab.active { color: #fff; border-bottom: 3px solid #00ff66; font-weight: bold; }
    .league-tab img { display: block; margin: 0 auto 4px auto; width: 22px; height: 15px; border-radius: 2px; }

    /* Main Nav Tabs */
    .main-nav { display: flex; background: #17212e; border-bottom: 1px solid #233246; }
    .nav-item { flex: 1; text-align: center; padding: 12px 5px; color: #8fa0b5; font-size: 14px; font-weight: bold; text-decoration: none; border-bottom: 2px solid transparent; }
    .nav-item.active { color: #00ff66; border-bottom: 2px solid #00ff66; }

    /* Time Schedule Filters */
    .time-strip { display: flex; background: #0f1722; padding: 8px 10px; gap: 6px; overflow-x: auto; }
    .time-block { background: #17212e; padding: 5px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; color: #cfdbe8; }
    .time-block.active { background: #ff0033; color: white; }

    /* Market Rules Strip */
    .market-strip { display: flex; background: #121c27; padding: 8px 10px; gap: 6px; overflow-x: auto; border-bottom: 1px solid #1c2a39; }
    .market-btn { background: #202e3f; border: none; color: #bccee0; padding: 6px 12px; border-radius: 4px; font-size: 11px; font-weight: bold; cursor: pointer; }
    .market-btn.active { background: #00cc52; color: #000; }

    /* Main Sports Grid Matrix Layout */
    .match-row { display: flex; background: #17212e; border-bottom: 1px solid #0f1722; padding: 10px 8px; align-items: center; }
    .match-teams { flex: 1.2; font-size: 14px; font-weight: 600; color: #f5f8fa; line-height: 1.5; }
    .team-line { display: flex; align-items: center; gap: 8px; margin-bottom: 2px; }
    .team-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
    
    .odds-matrix { flex: 2; display: flex; gap: 5px; }
    .odds-box { flex: 1; background: #202e3f; border: none; border-radius: 4px; padding: 6px 4px; text-align: center; color: #fff; cursor: pointer; text-decoration: none;}
    .odds-box:hover { background: #2b3e55; }
    .odds-box .outcome-label { display: block; font-size: 10px; color: #76899f; margin-bottom: 2px; }
    .odds-box .odds-val { display: block; font-size: 13px; font-weight: bold; color: #00ff66; }

    /* Forms and Utilities */
    .bet-slip-panel { background: #17212e; margin: 15px; padding: 15px; border-radius: 8px; border: 1px solid #233246; }
    .input-field { background: #0b1118; border: 1px solid #233246; color: white; padding: 10px; width: 100%; box-sizing: border-box; border-radius: 6px; margin: 8px 0 15px 0; }
    .action-btn { background: #ffd700; color: #000; font-weight: bold; width: 100%; border: none; padding: 12px; border-radius: 6px; font-size: 15px; cursor: pointer; }
    .action-btn:hover { background: #e6c200; }
    .alert-banner { background: #ff3333; color: white; padding: 10px; text-align: center; border-radius: 6px; margin: 10px; font-size: 14px; }
    .success-banner { background: #00ff66; color: black; padding: 10px; text-align: center; border-radius: 6px; margin: 10px; font-weight: bold; font-size: 14px; }
</style>
"""

# ==========================================
# 4. VIEW RENDERING PAGES
# ==========================================
LOGIN_REG_BASE = PREMIUM_CSS + """
<div style="max-width:450px; margin: 50px auto; padding:20px; background:#17212e; border-radius:8px; border: 1px solid #233246;">
    <div class="logo" style="text-align:center; margin-bottom:20px;">LIGI<span>BIGI</span></div>
    {% if error %}<div class="alert-banner">{{ error }}</div>{% endif %}
    {% if msg %}<div class="success-banner">{{ msg }}</div>{% endif %}
    {{ content|safe }}
</div>
"""

DASHBOARD_PAGE = PREMIUM_CSS + """
<div style="max-width: 800px; margin: 0 auto; background: #0f1722; min-height: 100vh;">
    <div class="top-header">
        <div class="logo">LIGI<span>BIGI</span></div>
        <div style="display:flex; align-items:center; gap:10px;">
            <div class="balance-badge">KES {{ "%.2f"|format(balance) }}</div>
            <a href="/logout" style="color:#8fa0b5; text-decoration:none; font-size:12px;">Sign Out</a>
        </div>
    </div>

    <div class="league-tabs">
        <div class="league-tab"><span style="font-size:16px;">🇬🇧</span><br>English</div>
        <div class="league-tab"><span style="font-size:16px;">🇰🇪</span><br>Kenyan</div>
        <div class="league-tab"><span style="font-size:16px;">🇩🇪</span><br>German</div>
        <div class="league-tab"><span style="font-size:16px;">🇪🇸</span><br>Spanish</div>
        <div class="league-tab active"><span style="font-size:16px;">🇮🇹</span><br>Italian</div>
    </div>

    <div class="main-nav">
        <a href="#" class="nav-item active">Market⚽</a>
        <a href="#" class="nav-item">Results🕒</a>
        <a href="#" class="nav-item">Promos🎁</a>
        <a href="#" class="nav-item">My Bets📊</a>
    </div>

    <div class="time-strip">
        <div class="time-block active">00:46</div>
        <div class="time-block">17:52</div>
        <div class="time-block">17:54</div>
        <div class="time-block">17:56</div>
        <div class="time-block">17:58</div>
        <div class="time-block">18:00</div>
    </div>

    <div class="market-strip">
        <button class="market-btn active">1X2</button>
        <button class="market-btn">BTTS</button>
        <button class="market-btn">OV/UN 1.5</button>
        <button class="market-btn">OV/UN 2.5</button>
    </div>

    {% if msg %}<div class="success-banner">{{ msg }}</div>{% endif %}
    {% if error %}<div class="alert-banner">{{ error }}</div>{% endif %}

    <div style="margin-top: 2px;">
        {% for home, away, o1, oX, o2 in matches %}
        <div class="match-row">
            <div class="match-teams">
                <div class="team-line"><span class="team-dot" style="background:#0052cc;"></span>{{ home }}</div>
                <div class="team-line"><span class="team-dot" style="background:#cc0022;"></span>{{ away }}</div>
            </div>
            <div class="odds-matrix">
                <div class="odds-box" onclick="document.getElementById('match_select').value='{{ home }} vs {{ away }}'; document.getElementById('pred_select').value='1';">
                    <span class="outcome-label">1</span>
                    <span class="odds-val">{{ o1 }}</span>
                </div>
                <div class="odds-box" onclick="document.getElementById('match_select').value='{{ home }} vs {{ away }}'; document.getElementById('pred_select').value='X';">
                    <span class="outcome-label">X</span>
                    <span class="odds-val">{{ oX }}</span>
                </div>
                <div class="odds-box" onclick="document.getElementById('match_select').value='{{ home }} vs {{ away }}'; document.getElementById('pred_select').value='2';">
                    <span class="outcome-label">2</span>
                    <span class="odds-val">{{ o2 }}</span>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>

    <div class="bet-slip-panel">
        <h3 style="margin-top:0; color:#ffcc00; font-size:16px;">⚡ Quick Bet Slip Controller</h3>
        <form method="POST" action="/place-bet">
            <label style="font-size:12px; color:#8fa0b5;">Active Match Target</label>
            <select name="match" id="match_select" class="input-field">
                {% for home, away, o1, oX, o2 in matches %}
                <option value="{{ home }} vs {{ away }}">{{ home }} vs {{ away }}</option>
                {% endfor %}
            </select>

            <div style="display:flex; gap:10px;">
                <div style="flex:1;">
                    <label style="font-size:12px; color:#8fa0b5;">Market Prediction</label>
                    <select name="prediction" id="pred_select" class="input-field">
                        <option value="1">Home Win (1)</option>
                        <option value="X">Draw (X)</option>
                        <option value="2">Away Win (2)</option>
                    </select>
                </div>
                <div style="flex:1;">
                    <label style="font-size:12px; color:#8fa0b5;">Stake Value (KSh)</label>
                    <input type="number" name="stake" min="5" value="50" class="input-field" required>
                </div>
            </div>
            <button type="submit" class="action-btn">Place Virtual Stake & Simulate Match</button>
        </form>
    </div>

    <div class="bet-slip-panel" style="background:#131f2d;">
        <h4 style="margin:0 0 10px 0; color:#00ff66;">💸 Fast M-Pesa Wallet Deposit</h4>
        <form method="POST" action="/deposit" style="display:flex; gap:10px; align-items:center;">
            <input type="number" name="amount" min="10" placeholder="Amount (KSh)" class="input-field" style="margin:0;" required>
            <button type="submit" class="action-btn" style="width:150px; background:#00cc52; color:white;">Deposit</button>
        </form>
    </div>
</div>
"""

# ==========================================
# 5. ROUTING & CONTROLLER INTERCEPTORS
# ==========================================
@app.route('/')
def home():
    if 'email' in session:
        user = USERS_DB.get(session['email'])
        if user:
            return render_template_string(DASHBOARD_PAGE, balance=user['balance'], matches=MATCH_LIST, msg=request.args.get('msg'), error=request.args.get('error'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        if email in USERS_DB:
            return render_template_string(LOGIN_REG_BASE, error="Email already exists.", content="<a href='/login'>Go to Login</a>")
        USERS_DB[email] = {'phone': phone, 'password': password, 'balance': 0.05} # Starting credit matching image profile state
        session['email'] = email
        return redirect(url_for('home', msg="Welcome to Ligi Bigi! Account activated."))
    
    content = """
    <h2 style="margin-top:0;">Create Account</h2>
    <form method="POST">
        <label>Email Address</label><input type="email" name="email" class="input-field" required placeholder="name@domain.com">
        <label>M-Pesa Number</label><input type="text" name="phone" class="input-field" required placeholder="0712345678">
        <label>Password</label><input type="password" name="password" class="input-field" required placeholder="••••••••">
        <button type="submit" class="action-btn">Register</button>
    </form>
    <p style="text-align:center; font-size:13px; margin-top:15px;"><a href="/login" style="color:#00ff66; text-decoration:none;">Already have an account? Login</a></p>
    """
    return render_template_string(LOGIN_REG_BASE, content=content)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email in USERS_DB and USERS_DB[email]['password'] == password:
            session['email'] = email
            return redirect(url_for('home'))
        return render_template_string(LOGIN_REG_BASE, error="Invalid credentials.")
    
    content = """
    <h2 style="margin-top:0;">Account Login</h2>
    <form method="POST">
        <label>Email</label><input type="email" name="email" class="input-field" required>
        <label>Password</label><input type="password" name="password" class="input-field" required>
        <button type="submit" class="action-btn">Login</button>
    </form>
    <p style="text-align:center; font-size:13px; margin-top:15px;"><a href="/register" style="color:#00ff66; text-decoration:none;">New user? Register here</a></p>
    """
    return render_template_string(LOGIN_REG_BASE, content=content)

@app.route('/deposit', methods=['POST'])
def deposit():
    if 'email' not in session: return redirect(url_for('login'))
    amount = float(request.form['amount'])
    USERS_DB[session['email']]['balance'] += amount
    return redirect(url_for('home', msg=f"Deposit Confirmed! Credited KSh {amount} successfully."))

@app.route('/place-bet', methods=['POST'])
def place_bet():
    if 'email' not in session: return redirect(url_for('login'))
    user = USERS_DB[session['email']]
    match = request.form['match']
    prediction = request.form['prediction']
    stake = float(request.form['stake'])
    
    if user['balance'] < stake:
        return redirect(url_for('home', error="Insufficient balance for this stake!"))
    
    user['balance'] -= stake
    home_team, away_team = match.split(" vs ")
    h_g, a_g = simulate_match(home_team, away_team)
    
    actual_outcome = "X"
    if h_g > a_g: actual_outcome = "1"
    elif h_g < a_g: actual_outcome = "2"
    
    # Simple dynamic multiplier lookup matching odds scale factor
    odds_payout = 2.50
    for h, a, o1, oX, o2 in MATCH_LIST:
        if h == home_team:
            if prediction == "1": odds_payout = float(o1)
            elif prediction == "X": odds_payout = float(oX)
            elif prediction == "2": odds_payout = float(o2)

    if prediction == actual_outcome:
        winnings = stake * odds_payout
        user['balance'] += winnings
        result_msg = f"🎉 WINNER! Result: {home_team} {h_g} - {a_g} {away_team}. Won KSh {winnings:,.2f}!"
    else:
        result_msg = f"❌ Lost. Result: {home_team} {h_g} - {a_g} {away_team}. Better luck next ticket!"
        
    return redirect(url_for('home', msg=result_msg))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
