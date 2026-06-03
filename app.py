from flask import Flask, request, render_template_string, redirect, session, url_for, jsonify
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
BETS_REGISTRY = [] 
COMPLETED_ROUNDS_HISTORY = []

ALL_TEAMS = [
    'Roma', 'Juventus', 'Milan Reds', 'Torino', 'Fiorentina',
    'Bologna', 'Sassuolo', 'Lazio', 'Verona', 'Atalanta',
    'Monza', 'Cremonese', 'Lecce', 'Udinese', 'Spezia',
    'Empoli', 'Napoli', 'Sampdoria', 'Salernitana', 'Milan Blues'
]

ENGINE_STATE = {
    'round_number': 1,
    'phase': 'BETTING',       
    'time_remaining': 60,     
    'active_matches': [],     
    'forced_results': {}      
}

lock = threading.Lock()

# ==========================================
# 2. MATCH & ODDS MATRIX SIMULATION ENGINE
# ==========================================
def generate_new_round_fixtures():
    random.shuffle(ALL_TEAMS)
    fixtures = []
    for i in range(0, len(ALL_TEAMS), 2):
        home = ALL_TEAMS[i]
        away = ALL_TEAMS[i+1]
        
        h_weight = random.uniform(1.3, 4.5)
        a_weight = random.uniform(1.3, 4.5)
        d_weight = random.uniform(2.8, 3.9)
        
        final_home_goals = min(5, int(random.gammavariate(2, 0.6)))
        final_away_goals = min(5, int(random.gammavariate(2, 0.5)))
        
        goal_events = []
        for _ in range(final_home_goals):
            goal_events.append({'team': 'home', 'sec': random.randint(1, 35)})
        for _ in range(final_away_goals):
            goal_events.append({'team': 'away', 'sec': random.randint(1, 35)})
            
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

ENGINE_STATE['active_matches'] = generate_new_round_fixtures()

# ==========================================
# 3. BACKGROUND CONTINUOUS TIMING LOOP
# ==========================================
def continuous_loop_daemon():
    global ENGINE_STATE, BETS_REGISTRY, COMPLETED_ROUNDS_HISTORY
    while True:
        time.sleep(1)
        with lock:
            ENGINE_STATE['time_remaining'] -= 1
            
            if ENGINE_STATE['phase'] == 'BETTING' and ENGINE_STATE['time_remaining'] <= 0:
                ENGINE_STATE['phase'] = 'PLAYING'
                ENGINE_STATE['time_remaining'] = 37 
                
                for idx, match in enumerate(ENGINE_STATE['active_matches']):
                    if idx in ENGINE_STATE['forced_results']:
                        choice = ENGINE_STATE['forced_results'][idx]
                        if choice == '1':
                            match['final_h_g'], match['final_a_g'] = 2, 0
                        elif choice == 'X':
                            match['final_h_g'], match['final_a_g'] = 1, 1
                        elif choice == '2':
                            match['final_h_g'], match['final_a_g'] = 0, 2
                        match['goals_timeline'] = [{'team': 'home' if choice=='1' else 'away', 'sec': 5}] if choice != 'X' else []

            elif ENGINE_STATE['phase'] == 'PLAYING' and ENGINE_STATE['time_remaining'] <= 0:
                settle_all_round_bets()
                
                round_summary = {
                    'round': ENGINE_STATE['round_number'],
                    'results': [f"{m['home']} {m['final_h_g']}-{m['final_a_g']} {m['away']}" for m in ENGINE_STATE['active_matches']]
                }
                COMPLETED_ROUNDS_HISTORY.insert(0, round_summary)
                
                ENGINE_STATE['round_number'] += 1
                ENGINE_STATE['phase'] = 'BETTING'
                ENGINE_STATE['time_remaining'] = 60
                ENGINE_STATE['active_matches'] = generate_new_round_fixtures()
                ENGINE_STATE['forced_results'].clear()

threading.Thread(target=continuous_loop_daemon, daemon=True).start()

def settle_all_round_bets():
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
    .logo span { color: black; background: #ffcc00; padding: 2px 6px; border-radius: 4px; margin-left:4px; font-weight: bold; }
    .wrapper { max-width: 950px; margin: 20px auto; padding: 0 15px; }
    .grid-matrix { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
    .card { background: #16222f; border-radius: 8px; border: 1px solid #223245; padding: 15px; margin-bottom: 15px; }
    .timer-banner { text-align: center; font-size: 18px; font-weight: bold; padding: 10px; border-radius: 6px; margin-bottom: 15px; letter-spacing: 1px; transition: background 0.3s ease; }
    .timer-banner.betting { background: #006633; color: white; }
    .timer-banner.playing { background: #b20000; color: white; }
    
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
"""

DASHBOARD_TEMPLATE = COMMON_CSS + """
<div class="nav-bar">
    <div class="logo">LIGI<span>BIGI V10</span></div>
    <div style="display:flex; align-items:center; gap:15px;">
        <span style="color:#8fa1b4;">Wallet: <strong id="top-wallet-bal">KES {{ "%.2f"|format(user_data.balance) }}</strong></span>
        {% if user_data.is_admin %}<a href="/admin" style="color:#ffcc00; font-weight:bold;">Admin Panel</a>{% endif %}
        <a href="/logout" style="color:#aaa; text-decoration:none; font-size:13px;">Sign Out</a>
    </div>
</div>

<div class="wrapper">
    <div id="live-timer-banner" class="timer-banner betting">Loading Virtual Match Data Stream...</div>

    {% if msg %}<div style="background:#006633; padding:10px; border-radius:6px; margin-bottom:15px;">{{ msg }}</div>{% endif %}
    {% if error %}<div style="background:#b20000; padding:10px; border-radius:6px; margin-bottom:15px;">{{ error }}</div>{% endif %}

    <div class="grid-matrix">
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
                    <tbody id="match-rows-container">
                        {% for match in state.active_matches %}
                        {% set match_idx = loop.index0 %}
                        <tr>
                            <td>
                                <strong id="home-name-{{ match_idx }}">{{ match.home }}</strong> 
                                <span id="score-space-{{ match_idx }}" style="color:#00ff66; margin: 0 10px; font-weight:bold;">vs</span> 
                                <strong id="away-name-{{ match_idx }}">{{ match.away }}</strong>
                            </td>
                            <td>
                                <div class="odds-group">
                                    <div class="odds-btn" onclick="selectBet('{{ match_idx }}', '1', '{{ match.odds_1 }}', '{{ match.home }}')">1 <span id="o1-val-{{ match_idx }}" style="color:white; display:block;">{{ match.odds_1 }}</span></div>
                                    <div class="odds-btn" onclick="selectBet('{{ match_idx }}', 'X', '{{ match.odds_X }}', 'Draw')">X <span id="ox-val-{{ match_idx }}" style="color:white; display:block;">{{ match.odds_X }}</span></div>
                                    <div class="odds-btn" onclick="selectBet('{{ match_idx }}', '2', '{{ match.odds_2 }}', '{{ match.away }}')">2 <span id="o2-val-{{ match_idx }}" style="color:white; display:block;">{{ match.odds_2 }}</span></div>
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <div>
            <div class="card" style="background:#1c2d3d;">
                <h3 style="margin-top:0; color:#ffcc00;">🛒 Multi-Betslip Console</h3>
                <div id="market-lock-msg" style="display:none; color:#ff3333; font-size:12px; font-weight:bold; margin-bottom:10px;">⚠️ Market Suspended while match is running.</div>
                <form method="POST" action="/place-multibet">
                    <div id="slip-container">
                        <p style="color:#8fa1b4; font-size:13px;" id="empty-slip-msg">Click odds options on the match grid matrix to populate selection registry instantly.</p>
                    </div>
                    
                    <label style="font-size:12px; color:#8fa1b4; display:block; margin-top:10px;">Ticket Base Stake (KSh per selected match)</label>
                    <input type="number" name="stake" min="5" value="50" class="input-field" required>
                    
                    <button type="submit" id="submit-slip-btn" class="submit-btn">Book Virtual Bet Slips</button>
                </form>
            </div>

            <div class="card">
                <h4 style="margin-top:0; color:#00ff66;">💸 Instant Virtual M-Pesa Deposit</h4>
                <form method="POST" action="/deposit">
                    <input type="number" name="amount" min="10" placeholder="Amount (KSh)" class="input-field" required>
                    <button type="submit" class="submit-btn" style="background:#00cc52; color:white; padding:8px;">Simulate STK Push</button>
                </form>
            </div>

            <div class="card">
                <h4 style="margin-top:0; color:#8fa1b4;">🕒 Recent Results History Feed</h4>
                <div id="history-feed-box" style="max-height:200px; overflow-y:auto; font-size:11px;">
                    </div>
            </div>
        </div>
    </div>

    <div class="card">
        <h3>My Betting History Summary Status</h3>
        <table class="table-match">
            <thead>
                <tr>
                    <th>ROUND</th>
                    <th>TARGET MATCH</th>
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
                    <td>Game Index Reference: Slot #{{ b.match_idx + 1 }}</td>
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
let currentPhase = "BETTING";
let currentRound = 0;

function selectBet(matchIdx, selection, odds, label) {
    if (currentPhase !== "BETTING") {
        alert("Markets suspended! Wait until next round window opens.");
        return;
    }
    document.getElementById('empty-slip-msg').style.display = 'none';
    
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
            <span>Match #${parseInt(matchIdx)+1}: ${label} (${selection})</span>
            <span style="color:#00ff66;">@ ${odds}</span>
        </div>
        <input type="hidden" name="match_idx_list" value="${matchIdx}">
        <input type="hidden" name="pred_list" value="${selection}">
        <input type="hidden" name="odds_list" value="${odds}">
        <small style="color:#ff3333; cursor:pointer;" onclick="this.parentElement.remove()">[Remove Item]</small>
    `;
    container.appendChild(div);
}

// Seamless dynamic fetching background execution system loop
function syncEngineState() {
    fetch('/api/state')
        .then(response => response.json())
        .then(data => {
            currentPhase = data.phase;
            
            // Auto reload cleanly ONCE only when the round changes to refresh betting grids and history lists cleanly
            if (currentRound !== 0 && currentRound !== data.round_number) {
                location.reload();
                return;
            }
            currentRound = data.round_number;

            // 1. Update Top Banner elements smoothly
            let banner = document.getElementById('live-timer-banner');
            if (data.phase === "BETTING") {
                banner.className = "timer-banner betting";
                banner.innerHTML = `⏳ BETTING WINDOW OPEN — ROUND ${data.round_number} (LOCKS IN ${data.time_remaining}s)`;
                document.getElementById('market-lock-msg').style.display = 'none';
                document.getElementById('submit-slip-btn').disabled = false;
                document.getElementById('submit-slip-btn').style.background = "#ffcc00";
            } else {
                banner.className = "timer-banner playing";
                let matchMinute = Math.min(90, Math.floor((37 - data.time_remaining) * 2.43));
                banner.innerHTML = `📺 SIMULATING LIVE MATCH RUNTIME — MINUTE ${matchMinute}' / 90'`;
                document.getElementById('market-lock-msg').style.display = 'block';
                document.getElementById('submit-slip-btn').disabled = true;
                document.getElementById('submit-slip-btn').style.background = "#444";
            }

            // 2. Loop update team matchups and real-time live score lines
            data.active_matches.forEach((match, idx) => {
                document.getElementById('home-name-{{ idx }}').innerText = match.home;
                document.getElementById('away-name-{{ idx }}').innerText = match.away;
                document.getElementById('o1-val-{{ idx }}').innerText = match.odds_1;
                document.getElementById('ox-val-{{ idx }}').innerText = match.odds_X;
                document.getElementById('o2-val-{{ idx }}').innerText = match.odds_2;

                let scoreSpace = document.getElementById('score-space-' + idx);
                if (data.phase === "PLAYING") {
                    let elapsed = 37 - data.time_remaining;
                    let liveH = 0, liveA = 0;
                    match.goals_timeline.forEach(g => {
                        if (g.sec <= elapsed) {
                            if (g.team === 'home') liveH++; else liveA++;
                        }
                    });
                    scoreSpace.innerText = `${liveH} - ${liveA}`;
                    scoreSpace.style.color = "#ffcc00";
                } else {
                    scoreSpace.innerText = "vs";
                    scoreSpace.style.color = "#00ff66";
                }
            });

            // 3. Inject history list data items smoothly 
            let histBox = document.getElementById('history-feed-box');
            histBox.innerHTML = "";
            data.history.forEach(r => {
                let div = document.createElement('div');
                div.style.marginBottom = "8px";
                div.style.borderBottom = "1px solid #223245";
                div.style.paddingBottom = "4px";
                let matchSummaryString = r.results.join(" | ");
                div.innerHTML = `<span style="color:#ffcc00; font-weight:bold;">Round #${r.round}:</span><br><span style="color:#ccc;">${matchSummaryString}</span>`;
                histBox.appendChild(div);
            });
        });
}

setInterval(syncEngineState, 1000);
syncEngineState();
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
        
        <form method="POST" action="/admin/force-outcome">
            <label>Select Target Active Game Match</label>
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
@app.route('/api/state')
def api_state():
    """Background data pipeline API endpoint"""
    with lock:
        return jsonify({
            'round_number': ENGINE_STATE['round_number'],
            'phase': ENGINE_STATE['phase'],
            'time_remaining': ENGINE_STATE['time_remaining'],
            'active_matches': [{
                'home': m['home'], 'away': m['away'],
                'odds_1': m['odds_1'], 'odds_X': m['odds_X'], 'odds_2': m['odds_2'],
                'goals_timeline': m['goals_timeline']
            } for m in ENGINE_STATE['active_matches']],
            'history': COMPLETED_ROUNDS_HISTORY[:5]
        })

@app.route('/')
def home():
    if 'email' not in session: return redirect(url_for('login'))
    user = USERS_DB.get(session['email'])
    if not user: return redirect(url_for('logout'))
    
    my_tickets = [b for b in BETS_REGISTRY if b['email'] == session['email']][::-1]
    return render_template_string(DASHBOARD_TEMPLATE, user_data=user, state=ENGINE_STATE, tickets=my_tickets)

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
        return redirect(url_for('home', error="Empty betslip entry."))
        
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

@app.route('/admin')
def admin_panel():
    if 'email' not in session or not USERS_DB.get(session['email'], {}).get('is_admin'):
        return "Access Denied", 403
    return render_template_string(ADMIN_TEMPLATE, state=ENGINE_STATE)

@app.route('/admin/force-outcome', methods=['POST'])
def admin_force_outcome():
    if 'email' not in session or not USERS_DB.get(session['email'], {}).get('is_admin'):
        return "Unauthorized", 403
    m_idx = int(request.form['match_index'])
    pick = request.form['forced_pick']
    with lock:
        ENGINE_STATE['forced_results'][m_idx] = pick
    return redirect(url_for('admin_panel'))

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
