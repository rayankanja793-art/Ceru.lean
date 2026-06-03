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
from flask import Flask, request, render_template_string, redirect, session, url_for
import math
import random
import os
import threading
import time

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ultra_secure_ligi_bigi_matrix_9988")

# ==========================================
# 1. CORE DATA REGISTRIES & STATE SYSTEM
# ==========================================
USERS_DB = {
    'admin@ligibigi.com': {'phone': '00000000', 'password': 'adminpassword', 'balance': 9999999.0, 'is_admin': True}
}
BETS_REGISTRY = [] # Stores placed tickets
COMPLETED_ROUNDS_HISTORY = []

ALL_TEAMS = [
    'Roma', 'Juventus', 'Milan Reds', 'Torino', 'Fiorentina',
    'Bologna', 'Sassuolo', 'Lazio', 'Verona', 'Atalanta',
    'Monza', 'Cremonese', 'Lecce', 'Udinese', 'Spezia',
    'Empoli', 'Napoli', 'Sampdoria', 'Salernitana', 'Milan Blues'
]

# Thread-safe Engine State Dictionary
ENGINE_STATE = {
    'round_number': 1,
    'phase': 'BETTING',       # 'BETTING' or 'PLAYING'
    'time_remaining': 60,     # Countdown tracker
    'active_matches': [],     # List of current 10 matches
    'forced_results': {}      # Admin overrides registry: {match_index: '1' or 'X' or '2'}
}

lock = threading.Lock()

# ==========================================
# 2. MATCH & ODDS MATRIX SIMULATION ENGINE
# ==========================================
def generate_new_round_fixtures():
    """Shuffles all 20 teams and assigns realistic random decimal 1X2 odds weights"""
    random.shuffle(ALL_TEAMS)
    fixtures = []
    for i in range(0, len(ALL_TEAMS), 2):
        home = ALL_TEAMS[i]
        away = ALL_TEAMS[i+1]
        
        # Calculate random relative strengths for realistic dynamic odds grid
        h_weight = random.uniform(1.3, 4.5)
        a_weight = random.uniform(1.3, 4.5)
        d_weight = random.uniform(2.8, 3.9)
        
        # Precompute target goal profiles for the eventual 37-sec live engine
        final_home_goals = min(5, int(random.gammavariate(2, 0.6)))
        final_away_goals = min(5, int(random.gammavariate(2, 0.5)))
        
        # Pre-assign execution timestamps for goal distribution across 37 playing seconds
        goal_events = []
        for _ in range(final_home_goals):
            goal_events.append({'team': 'home', 'sec': random.randint(1, 36)})
        for _ in range(final_away_goals):
            goal_events.append({'team': 'away', 'sec': random.randint(1, 36)})
            
        fixtures.append({
            'home': home,
            'away': away,
            'odds_1': f"{h_weight:.2f}",
            'odds_X': f"{d_weight:.2f}",
            'odds_2': f"{a_weight:.2f}",
            'final_h_g': final_home_goals,
            'final_a_g': final_away_goals,
            'goals_timeline': goal_events
        })
    return fixtures

# Seed initial system round conditions
ENGINE_STATE['active_matches'] = generate_new_round_fixtures()

# ==========================================
# 3. BACKGROUND CONTINUOUS TIMING LOOP
# ==========================================
def continuous_loop_daemon():
    """Background loop that ticks every second without stalling user navigation"""
    global ENGINE_STATE, BETS_REGISTRY, COMPLETED_ROUNDS_HISTORY
    while True:
        time.sleep(1)
        with lock:
            ENGINE_STATE['time_remaining'] -= 1
            
            # Phase transitions
            if ENGINE_STATE['phase'] == 'BETTING' and ENGINE_STATE['time_remaining'] <= 0:
                # Close betting window -> Shift into live simulation phase
                ENGINE_STATE['phase'] = 'PLAYING'
                ENGINE_STATE['time_remaining'] = 37 # 37 seconds match duration
                
                # Apply admin force manipulation checks if configured
                for idx, match in enumerate(ENGINE_STATE['active_matches']):
                    if idx in ENGINE_STATE['forced_results']:
                        choice = ENGINE_STATE['forced_results'][idx]
                        if choice == '1':
                            match['final_h_g'], match['final_a_g'] = 2, 0
                        elif choice == 'X':
                            match['final_h_g'], match['final_a_g'] = 1, 1
                        elif choice == '2':
                            match['final_h_g'], match['final_a_g'] = 0, 2
                        # Reset timeline sequence tracking for forced results
                        match['goals_timeline'] = [{'team': 'home' if choice=='1' else 'away', 'sec': 10}] if choice != 'X' else []

            elif ENGINE_STATE['phase'] == 'PLAYING' and ENGINE_STATE['time_remaining'] <= 0:
                # Settle active betting round balances
                settle_all_round_bets()
                
                # Archive results history log
                round_summary = {
                    'round': ENGINE_STATE['round_number'],
                    'results': [f"{m['home']} {m['final_h_g']}-{m['final_a_g']} {m['away']}" for m in ENGINE_STATE['active_matches']]
                }
                COMPLETED_ROUNDS_HISTORY.insert(0, round_summary)
                
                # Shift back into betting sequence for next generation phase
                ENGINE_STATE['round_number'] += 1
                ENGINE_STATE['phase'] = 'BETTING'
                ENGINE_STATE['time_remaining'] = 60
                ENGINE_STATE['active_matches'] = generate_new_round_fixtures()
                ENGINE_STATE['forced_results'].clear()

# Spin up daemon background runner threads
threading.Thread(target=continuous_loop_daemon, daemon=True).start()

def settle_all_round_bets():
    """Evaluates tickets against computed final whistle score matrix values"""
    global BETS_REGISTRY
    current_r = ENGINE_STATE['round_number']
    active_fixtures = ENGINE_STATE['active_matches']
    
    for bet in BETS_REGISTRY:
        if bet['round'] == current_r and bet['status'] == 'OPEN':
            match_data = active_fixtures[bet['match_idx']]
            h_g = match_data['final_h_g']
            a_g = match_data['final_a_g']
            
            actual = 'X'
            if h_g > a_g: actual = '1'
            elif h_g < a_g: actual = '2'
            
            user = USERS_DB.get(bet['email'])
            if bet['prediction'] == actual:
                winnings = bet['stake'] * bet['odds']
                bet['status'] = f"WON (KSh {winnings:.2f})"
                if user: user['balance'] += winnings
            else:
                bet['status'] = "LOST"

# ==========================================
# 4. VIEW ENGINE UI DESIGN INTERFACES
# ==========================================
COMMON_CSS = """
<style>
    body { font-family: 'Segoe UI', Arial, sans-serif; background-color: #0c131c; color: #fff; margin:0; padding:0; }
    .nav-bar { background: #16222f; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #223245; }
    .logo { font-size: 20px; font-weight: 900; color: #00ff66; letter-spacing: 1px; }
    .logo span { color: white; background: #ffcc00; padding: 2px 6px; border-radius: 4px; margin-left:4px; color:black; }
    .wrapper { max-width: 950px; margin: 20px auto; padding: 0 15px; }
    .grid-matrix { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
    .card { background: #16222f; border-radius: 8px; border: 1px solid #223245; padding: 15px; margin-bottom: 15px; }
    .timer-banner { text-align: center; font-size: 18px; font-weight: bold; background: #b20000; padding: 10px; border-radius: 6px; margin-bottom: 15px; letter-spacing: 1px;}
    .timer-banner.betting { background: #006633; }
    
    /* Layout table styling matching user upload profile */
    .table-match { width: 100%; border-collapse: collapse; margin-top: 10px; }
    .table-match th { text-align: left; background: #0f1822; padding: 10px; color: #8fa1b4; font-size: 12px; }
    .table-match td { padding: 12px 10px; border-bottom: 1px solid #1f2d3d; font-size: 14px; }
    .odds-group { display: flex; gap: 5px; }
    .odds-btn { background: #213244; border: 1px solid #2d425a; color: #00ff66; padding: 8px; border-radius: 4px; text-align: center; cursor: pointer; font-weight: bold; flex: 1; min-width:60px; font-size:12px;}
    .odds-btn:hover { background: #2d425a; }
    
    .input-field { width: 100%; padding: 10px; background: #0c131c; border: 1px solid #2d425a; color: white; border-radius: 6px; box-sizing: border-box; margin-bottom: 12px; }
    .submit-btn { background: #ffcc00; color: black; font-weight: bold; border: none; padding: 12px; width: 100%; border-radius: 6px; cursor: pointer; font-size: 15px; }
    .submit-btn:hover { background: #e6b800; }
    .badge { padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
    .badge.open { background: #ffcc00; color: black; }
    .badge.won { background: #00ff66; color: black; }
    .badge.lost { background: #ff3333; color: white; }
</style>
<script>
    // System auto-refresh to mirror the background engine clock state
    setTimeout(function(){ location.reload(); }, 2000);
</script>
"""

DASHBOARD_TEMPLATE = COMMON_CSS + """
<div class="nav-bar">
    <div class="logo">LIGI<span>BIGI V10</span></div>
    <div style="display:flex; align-items:center; gap:15px;">
        <span style="color:#8fa1b4;">Wallet: <strong>KSh {{ "%.2f"|format(user_data.balance) }}</strong></span>
        {% if user_data.is_admin %}<a href="/admin" style="color:#ffcc00; font-weight:bold;">Admin Panel</a>{% endif %}
        <a href="/logout" style="color:#aaa; text-decoration:none; font-size:13px;">Sign Out</a>
    </div>
</div>

<div class="wrapper">
    {% if state.phase == "BETTING" %}
    <div class="timer-banner betting">⏳ BETTING WINDOW OPEN — ROUND {{ state.round_number }} (LOCKS IN {{ state.time_remaining }}s)</div>
    {% else %}
    <div class="timer-banner">📺 SIMULATING LIVE MATCH RUNTIME — MINUTE {{ ((37 - state.time_remaining) * 2.4)|int }}' / 90'</div>
    {% endif %}

    {% if msg %}<div style="background:#006633; padding:10px; border-radius:6px; margin-bottom:15px;">{{ msg }}</div>{% endif %}
    {% if error %}<div style="background:#b20000; padding:10px; border-radius:6px; margin-bottom:15px;">{{ error }}</div>{% endif %}

    <div class="grid-matrix">
        <!-- Live Field Board Grid Left Panel -->
        <div>
            <div class="card">
                <h3 style="margin-top:0; border-bottom: 1px solid #223245; padding-bottom:8px;">Active Italian League Matrix</h3>
                <table class="table-match">
                    <thead>
                        <tr>
                            <th>FIXTURE MATCHUP</th>
                            <th style="width:230px; text-align:center;">1X2 SELECTION ODDS</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for match in state.active_matches %}
                        {% set match_idx = loop.index0 %}
                        <tr>
                            <td>
                                <strong>{{ match.home }}</strong> <span style="color:#00ff66;">
                                {% if state.phase == "PLAYING" %}
                                    <!-- Dynamic real-time live score calculation tracking based on timestamps -->
                                    {% set current_elapsed = 37 - state.time_remaining %}
                                    {% set ns = namespace(h=0, a=0) %}
                                    {% for g in match.goals_timeline %}
                                        {% if g.sec <= current_elapsed %}
                                            {% if g.team == 'home' %}{% set ns.h = ns.h + 1 %}{% else %}{% set ns.a = ns.a + 1 %}{% endif %}
                                        {% endif %}
                                    {% endfor %}
                                    {{ ns.h }} - {{ ns.a }}
                                {% else %}
                                    vs
                                {% endif %}
                                </span> <strong>{{ match.away }}</strong>
                            </td>
                            <td>
                                <div class="odds-group">
                                    <div class="odds-btn" onclick="selectBet('{{ match_idx }}', '1', '{{ match.odds_1 }}', '{{ match.home }} (Home)')">1 <span style="color:white; display:block;">{{ match.odds_1 }}</span></div>
                                    <div class="odds-btn" onclick="selectBet('{{ match_idx }}', 'X', '{{ match.odds_X }}', 'Draw')">X <span style="color:white; display:block;">{{ match.odds_X }}</span></div>
                                    <div class="odds-btn" onclick="selectBet('{{ match_idx }}', '2', '{{ match.odds_2 }}', '{{ match.away }} (Away)')">2 <span style="color:white; display:block;">{{ match.odds_2 }}</span></div>
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Betslip Management Section Right Panel -->
        <div>
            <div class="card" style="background:#1c2d3d;">
                <h3 style="margin-top:0; color:#ffcc00;">🛒 Multi-Betslip Console</h3>
                {% if state.phase != "BETTING" %}
                    <p style="color:#ff3333; font-size:12px; font-weight:bold;">⚠️ Market Suspended while match is running.</p>
                {% endif %}
                <form method="POST" action="/place-multibet">
                    <div id="slip-container">
                        <p style="color:#8fa1b4; font-size:13px;" id="empty-slip-msg">Click odds options on the match grid matrix to populate selection registry instantly.</p>
                    </div>
                    
                    <label style="font-size:12px; color:#8fa1b4; display:block; margin-top:10px;">Ticket Base Stake (KSh per selected match)</label>
                    <input type="number" name="stake" min="5" value="50" class="input-field" required>
                    
                    <button type="submit" class="submit-btn" {% if state.phase != "BETTING" %}disabled style="background:#444;color:#aaa;"{% endif %}>Book Virtual Bet Slips</button>
                </form>
            </div>

            <!-- Virtual M-Pesa Funding Portal Integration Wrap -->
            <div class="card">
                <h4 style="margin-top:0; color:#00ff66;">💸 Instant Virtual M-Pesa Deposit</h4>
                <form method="POST" action="/deposit">
                    <input type="number" name="amount" min="10" placeholder="Amount (KSh)" class="input-field" required>
                    <button type="submit" class="submit-btn" style="background:#00cc52; color:white; padding:8px;">Simulate STK Push</button>
                </form>
            </div>

            <!-- Historical Round Archive Logs Results Feed -->
            <div class="card" style="max-height:250px; overflow-y:auto;">
                <h4 style="margin-top:0; color:#8fa1b4;">🕒 Recent Results History Feed</h4>
                {% for r in history %}
                <div style="font-size:11px; margin-bottom:8px; border-bottom:1px solid #223245; padding-bottom:4px;">
                    <span style="color:#ffcc00; font-weight:bold;">Round #{{ r.round }} Results Archive:</span><br>
                    {% for res in r.results %}
                        • {{ res }}<br>
                    {% endfor %}
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <!-- Active Tickets Audit Grid Log Summary -->
    <div class="card">
        <h3>My Betting History Summary Status</h3>
        <table class="table-match">
            <thead>
                <tr>
                    <th>ROUND</th>
                    <th>TARGET MATCH SELECTION</th>
                    <th>PREDICTION</th>
                    <th>STAKE</th>
                    <th>ODDS</th>
                    <th>TICKET STATUS</th>
                </tr>
            </thead>
            <tbody>
                {% for b in tickets %}
                <tr>
                    <td>#{{ b.round }}</td>
                    <td>Match index reference code #{{ b.match_idx + 1 }}</td>
                    <td>Market Pick: (<strong>{{ b.prediction }}</strong>)</td>
                    <td>KSh {{ b.stake }}</td>
                    <td>{{ b.odds }}</td>
                    <td>
                        {% if "WON" in b.status %}
                            <span class="badge won">{{ b.status }}</span>
                        {% elif "LOST" in b.status %}
                            <span class="badge lost">{{ b.status }}</span>
                        {% else %}
                            <span class="badge open">{{ b.status }}</span>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>

<script>
function selectBet(matchIdx, selection, odds, label) {
    if ("{{ state.phase }}" !== "BETTING") {
        alert("Markets suspended! Wait until next round window opens.");
        return;
    }
    document.getElementById('empty-slip-msg').style.display = 'none';
    
    // Check if element target block item wrapper already configured to clean up duplicates
    var existing = document.getElementById('slip-item-' + matchIdx);
    if(existing) { existing.remove(); }
    
    var container = document.getElementById('slip-container');
    var div = document.createElement('div');
    div.id = 'slip-item-' + matchIdx;
    div.style.background = '#111e2b';
    div.style.padding = '8px';
    div.style.borderRadius = '4px';
    div.style.marginBottom = '6px';
    div.style.fontSize = '12px';
    
    div.innerHTML = `
        <div style="display:flex; justify-content:space-between; font-weight:bold;">
            <span>Match #${parseInt(matchIdx)+1}: ${label}</span>
            <span style="color:#00ff66;">@ ${odds}</span>
        </div>
        <input type="hidden" name="match_idx_list" value="${matchIdx}">
        <input type="hidden" name="pred_list" value="${selection}">
        <input type="hidden" name="odds_list" value="${odds}">
        <small style="color:red; cursor:pointer;" onclick="this.parentElement.remove()">[Remove Item Selection]</small>
    `;
    container.appendChild(div);
}
</script>
"""

ADMIN_TEMPLATE = COMMON_CSS + """
<div class="nav-bar">
    <div class="logo">CONTROL ROOM<span>ADMIN</span></div>
    <a href="/" style="color:white; text-decoration:none;">Back to Live Market Grid</a>
</div>
<div class="wrapper" style="max-width:700px;">
    <h2>Ligi Bigi System Override Controls</h2>
    <div class="card" style="background:#1c1212; border-color:#5a2d2d;">
        <h3 style="color:#ff3333; margin-top:0;">Force System Manipulation Overrides</h3>
        <p style="font-size:12px; color:#aaa;">Select an active match block below to instantly force its result outcome criteria during the upcoming transition playing loop phase.</p>
        
        <form method="POST" action="/admin/force-outcome">
            <label>Select Target Active Game Match Matchup Block</label>
            <select name="match_index" class="input-field">
                {% for m in state.active_matches %}
                <option value="{{ loop.index0 }}">Match #{{ loop.index + 1 }}: {{ m.home }} vs {{ m.away }}</option>
                {% endfor %}
            </select>
            
            <label>Force Allocation Target Result Outcome</label>
            <select name="forced_pick" class="input-field">
                <option value="1">Force Home Team to Win (1)</option>
                <option value="X">Force Fixed Draw Outcome (X)</option>
                <option value="2">Force Away Team to Win (2)</option>
            </select>
            <button type="submit" class="submit-btn" style="background:#ff3333; color:white;">Inject Matrix Result Override</button>
        </form>
    </div>
    
    <div class="card">
        <h3>Current Phase Execution Matrix Meta Logs</h3>
        <ul>
            <li>Active Core Loop Phase: <strong>{{ state.phase }}</strong></li>
            <li>Cycle State Timer Left: <strong>{{ state.time_remaining }} Seconds</strong></li>
            <li>Active Live User Registries Count: <strong>{{ user_count }} Accounts</strong></li>
        </ul>
        <form method="POST" action="/admin/skip-countdown">
            <button type="submit" class="submit-btn" style="background:#ffcc00; color:black; font-size:12px; padding:6px;">Force Skip Clock Phase Phase</button>
        </form>
    </div>
</div>
"""

LOGIN_REG_BASE = COMMON_CSS + """
<div style="max-width:400px; margin: 80px auto; padding:25px; background:#16222f; border-radius:8px; border: 1px solid #223245;">
    <h2 style="text-align:center; color:#00ff66; margin-top:0;">LIGI<span>BIGI</span> MATRIX</h2>
    {% if error %}<div style="background:#b20000; padding:8px; border-radius:4px; font-size:13px; text-align:center; margin-bottom:10px;">{{ error }}</div>{% endif %}
    {{ content|safe }}
</div>
"""

# ==========================================
# 5. CONTROLLER PIPELINE ROUTING INTERCEPTORS
# ==========================================
@app.route('/')
def home():
    if 'email' not in session: return redirect(url_for('login'))
    user = USERS_DB.get(session['email'])
    if not user: return redirect(url_for('logout'))
    
    # Filter tickets owned by user context
    my_tickets = [b for b in BETS_REGISTRY if b['email'] == session['email']][::-1]
    
    return render_template_string(
        DASHBOARD_TEMPLATE, 
        user_data=user, 
        state=ENGINE_STATE, 
        tickets=my_tickets,
        history=COMPLETED_ROUNDS_HISTORY,
        msg=request.args.get('msg'),
        error=request.args.get('error')
    )

@app.route('/place-multibet', methods=['POST'])
def place_multibet():
    if 'email' not in session: return redirect(url_for('login'))
    if ENGINE_STATE['phase'] != 'BETTING':
        return redirect(url_for('home', error="Bets rejected! Markets are locked during active matches."))
        
    user = USERS_DB.get(session['email'])
    match_indices = request.form.getlist('match_idx_list')
    predictions = request.form.getlist('pred_list')
    odds_list = request.form.getlist('odds_list')
    base_stake = float(request.form.get('stake', 0))
    
    if not match_indices:
        return redirect(url_for('home', error="Empty betslip matrix submission block!"))
        
    total_cost = base_stake * len(match_indices)
    if user['balance'] < total_cost:
        return redirect(url_for('home', error=f"Insufficient funds! Needed KSh {total_cost:.2f}."))
        
    with lock:
        user['balance'] -= total_cost
        for i in range(len(match_indices)):
            BETS_REGISTRY.append({
                'email': session['email'],
                'round': ENGINE_STATE['round_number'],
                'match_idx': int(match_indices[i]),
                'prediction': predictions[i],
                'odds': float(odds_list[i]),
                'stake': base_stake,
                'status': 'OPEN'
            })
            
    return redirect(url_for('home', msg=f"Successfully booked {len(match_indices)} slips! Cost: KSh {total_cost:.2f}"))

@app.route('/deposit', methods=['POST'])
def deposit():
    if 'email' not in session: return redirect(url_for('login'))
    amount = float(request.form['amount'])
    USERS_DB[session['email']]['balance'] += amount
    return redirect(url_for('home', msg=f"M-Pesa STK push simulated! Credited KSh {amount:.2f}."))

# Admin Dashboard Endpoints
@app.route('/admin')
def admin_panel():
    if 'email' not in session or not USERS_DB.get(session['email'], {}).get('is_admin'):
        return "Access Denied: Administration Authentication Credentials Missing.", 403
    return render_template_string(ADMIN_TEMPLATE, state=ENGINE_STATE, user_count=len(USERS_DB))

@app.route('/admin/force-outcome', methods=['POST'])
def admin_force_outcome():
    if 'email' not in session or not USERS_DB.get(session['email'], {}).get('is_admin'):
        return "Unauthorized", 403
    m_idx = int(request.form['match_index'])
    pick = request.form['forced_pick']
    with lock:
        ENGINE_STATE['forced_results'][m_idx] = pick
    return redirect(url_for('admin_panel', msg=f"Injected result force vector parameter outcome '{pick}' into slot index block #{m_idx+1} successfully."))

@app.route('/admin/skip-countdown', methods=['POST'])
def admin_skip_countdown():
    if 'email' not in session or not USERS_DB.get(session['email'], {}).get('is_admin'):
        return "Unauthorized", 403
    with lock:
        ENGINE_STATE['time_remaining'] = 0
    return redirect(url_for('admin_panel'))

# Simple Registration & Login Layout Interceptors
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        if email in USERS_DB:
            return render_template_string(LOGIN_REG_BASE, error="Email already exists.")
        USERS_DB[email] = {'phone': phone, 'password': password, 'balance': 100.0, 'is_admin': False}
        session['email'] = email
        return redirect(url_for('home'))
    
    content = """
    <form method="POST">
        <h3>Create Account Profile</h3>
        <label>Email Address</label><input type="email" name="email" class="input-field" required>
        <label>M-Pesa Number</label><input type="text" name="phone" class="input-field" required>
        <label>Password</label><input type="password" name="password" class="input-field" required>
        <button type="submit" class="submit-btn">Open Account</button>
    </form>
    <p style="font-size:12px; text-align:center; margin-top:10px;"><a href="/login" style="color:#00ff66;">Already have an account? Login</a></p>
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
        return render_template_string(LOGIN_REG_BASE, error="Invalid credentials matrix inputs.")
    
    content = """
    <form method="POST">
        <h3>Account Login Authentication</h3>
        <label>Email Address</label><input type="email" name="email" class="input-field" required>
        <label>Password</label><input type="password" name="password" class="input-field" required>
        <button type="submit" class="submit-btn">Login</button>
    </form>
    <p style="font-size:12px; text-align:center; margin-top:10px;"><a href="/register" style="color:#00ff66;">New user? Sign Up Here</a></p>
    """
    return render_template_string(LOGIN_REG_BASE, content=content)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
