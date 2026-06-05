from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
import time
import random
import requests
from requests.auth import HTTPBasicAuth
import base64

app = Flask(__name__)

app.config.update(
    SECRET_KEY='swiftpitch_super_secret_key_2026',
    SESSION_COOKIE_SECURE=False,  
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# --- DATABASE LOGIC ---
users = {
    'admin@swiftpitch.com': {
        'password': 'adminpassword', 
        'balance': 0, 
        'bonus_unlocked': True, 
        'is_admin': True
    },
    'player@test.com': {
        'password': 'password123',
        'balance': 1000,
        'bonus_unlocked': True,
        'is_admin': False
    }
}

placed_bets = []

# --- LEAGUE SQUADS DATA ---
ITALIAN_TEAMS = [
    "Roma", "Juventus", "Milaan Reds", "Torino", "Fiorentina",
    "Bologna", "Sassuolo", "Lazio", "Verona", "Atlanta",
    "Monza", "Cremonese", "Leece", "Udinese", "Spenzia",
    "Empoli", "Napoli", "Samdoria", "Salernitana", "Milan Blues"
]

ENGLISH_TEAMS = [
    "Manchester blue", "spurs", "A.Villa", "London blues", "Manchester red",
    "New castle", "Everton", "Bournemouth", "N. forrest", "Brighton",
    "London reds", "Brentford", "Wolves", "west Ham", "Southampton",
    "Fulham", "Liverpool", "C.Palace", "Leicester", "Leeds"
]

state = {
    'is_running': True,
    'start_time': time.time(),
    'paused_elapsed': 0,
    'company_balance': 500000.0  
}

# --- REAL-MONEY PAYMENTS GATEWAY CONFIGURATION ---
MPESA_CONSUMER_KEY = 'YOUR_ACTUAL_DARAJA_CONSUMER_KEY'
MPESA_CONSUMER_SECRET = 'YOUR_ACTUAL_DARAJA_CONSUMER_SECRET'
MPESA_SHORTCODE = '174379'  
MPESA_PASSKEY = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'

def get_mpesa_access_token():
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    try:
        response = requests.get(api_url, auth=HTTPBasicAuth(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET), timeout=10)
        if response.status_code == 200:
            return response.json().get('access_token')
    except Exception:
        pass
    return None

# --- ENGINE CALCULATION MATRICES ---

def generate_fixtures_for_round(round_num, team_list, seed_offset):
    random.seed(round_num + seed_offset) 
    shuffled_teams = list(team_list)
    random.shuffle(shuffled_teams)
    
    fixtures = []
    for i in range(0, len(shuffled_teams), 2):
        home = shuffled_teams[i]
        away = shuffled_teams[i+1]
        
        home_odds = round(random.uniform(1.30, 4.50), 2)
        draw_odds = round(random.uniform(2.60, 3.80), 2)
        away_odds = round(random.uniform(1.40, 5.00), 2)
        
        fixtures.append({
            'id': f"fix_{round_num}_{i}_{seed_offset}",
            'home': home,
            'away': away,
            'home_score': random.randint(0, 4),
            'away_score': random.randint(0, 4),
            'odds': {
                'HOME': home_odds,
                'DRAW': draw_odds,
                'AWAY': away_odds
            }
        })
    return fixtures

def get_current_match_state():
    total_loop_time = 115  
    TOTAL_ROUNDS_IN_SEASON = 19  
    
    if not state['is_running']:
        elapsed = int(state['paused_elapsed'])
    else:
        elapsed = int(time.time() - state['start_time'])
        
    total_season_time = total_loop_time * TOTAL_ROUNDS_IN_SEASON
    
    season_number = (elapsed // total_season_time) + 1
    time_into_current_season = elapsed % total_season_time
    
    current_round = (time_into_current_season // total_loop_time) + 1
    time_into_current_loop = time_into_current_season % total_loop_time
    
    if time_into_current_loop < 60:
        phase = 'BETTING'
        time_left = 60 - time_into_current_loop
    else:
        phase = 'PLAYING'
        time_left = 115 - time_into_current_loop
        
    italian_fixtures = generate_fixtures_for_round(current_round, ITALIAN_TEAMS, 111)
    english_fixtures = generate_fixtures_for_round(current_round, ENGLISH_TEAMS, 222)
        
    return {
        'phase': phase,
        'time': time_left,
        'time_into_loop': time_into_current_loop,
        'round': current_round,
        'season': season_number,
        'italian_fixtures': italian_fixtures,
        'english_fixtures': english_fixtures
    }

def generate_live_commentary(fixtures_ita, fixtures_eng, time_into_loop, round_num):
    random.seed(time_into_loop + round_num)
    all_fixtures = fixtures_ita + fixtures_eng
    focus_match = random.choice(all_fixtures)
    
    home = focus_match['home']
    away = focus_match['away']
    h_score = focus_match['home_score']
    a_score = focus_match['away_score']
    
    playing_second = time_into_loop - 60
    match_minute = int((playing_second / 55.0) * 90)
    if match_minute < 1: match_minute = 1
    if match_minute > 90: match_minute = 90

    commentary_pool = [
        f"🎙️ GOOOAAAL! Incredible scenes! {home} breaks through the defensive wall!",
        f"🎙️ BALL IN THE NET! A masterclass finish from the {away} forward line!",
        f"🎙️ GOAL! The keeper had absolutely no chance with that powerful strike!",
        f"🎙️ UNBELIEVABLE GOAL! The stadium erupts as {home} volley finds the top corner!",
        f"🎙️ [{match_minute}'] Tactical battle ongoing in midfield between {home} and {away}.",
        f"🎙️ [{match_minute}'] {home} is maintaining possession nicely, looking for an opening.",
        f"🎙️ [{match_minute}'] Crucial sliding tackle intercept from the {away} central defender!",
        f"🎙️ [{match_minute}'] SPECTACULAR SAVE! The goalkeeper dives wide to deny {away}!"
    ]
    
    line = random.choice(commentary_pool)
    if "GOAL" in line or "GOOOAAAL" in line:
        return f"[{match_minute}'] " + line + f" ({home} {h_score} - {a_score} {away})"
    return line

def get_league_standings(current_round, teams_list, seed_offset):
    table = {team: {'name': team, 'mp': 0, 'w': 0, 'd': 0, 'l': 0, 'pts': 0} for team in teams_list}
    for r in range(1, current_round):
        fixtures = generate_fixtures_for_round(r, teams_list, seed_offset)
        for f in fixtures:
            h, a = f['home'], f['away']
            hs, as_ = f['home_score'], f['away_score']
            table[h]['mp'] += 1; table[a]['mp'] += 1
            if hs > as_:
                table[h]['w'] += 1; table[h]['pts'] += 3; table[a]['l'] += 1
            elif as_ > hs:
                table[a]['w'] += 1; table[a]['pts'] += 3; table[h]['l'] += 1
            else:
                table[h]['d'] += 1; table[h]['pts'] += 1; table[a]['d'] += 1; table[a]['pts'] += 1
                
    return sorted(table.values(), key=lambda x: x['pts'], reverse=True)

# --- CONTROLLER ROUTING ---

@app.route('/')
def index():
    if 'user' not in session or session['user'] not in users:
        session.clear()
        return redirect(url_for('login'))
        
    try:
        current_state = get_current_match_state()
        my_bets = [b for b in placed_bets if b['email'] == session['user']]
        return render_template('index.html', state=current_state, user=users[session['user']], bets=my_bets)
    except Exception as e:
        session.clear()
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        if email in users and users[email]['password'] == password:
            session['user'] = email
            return redirect(url_for('index'))
        flash("Invalid email or password.")
    return '''
    <body style="background:#0b1118; color:white; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;">
        <div style="background:#121b26; padding:30px; border-radius:8px; border:1px solid #1c2a39; width:320px; text-align:center;">
            <h2 style="color:#ffcc00; margin-bottom:20px;">⚽ SWIFTPITCH LOGIN</h2>
            <form method="POST">
                <input type="text" name="email" placeholder="Email Address" required style="width:90%; padding:10px; margin-bottom:15px; background:#0b1118; border:1px solid #1c2a39; color:white; border-radius:4px;"><br>
                <input type="password" name="password" placeholder="Password" required style="width:90%; padding:10px; margin-bottom:20px; background:#0b1118; border:1px solid #1c2a39; color:white; border-radius:4px;"><br>
                <button type="submit" style="width:97%; background:#00ff66; color:black; font-weight:bold; padding:12px; border:none; border-radius:4px; cursor:pointer; text-transform:uppercase;">Sign In</button>
            </form>
        </div>
    </body>
    '''

@app.route('/place-multibet', methods=['POST'])
def place_multibet():
    if 'user' not in session: return jsonify({'success': False, 'message': 'Session expired.'}), 401
    
    current_state = get_current_match_state()
    if current_state['phase'] != 'BETTING':
        return jsonify({'success': False, 'message': 'Market closed! Matches are already in play.'}), 400
        
    data = request.get_json() or {}
    selections = data.get('selections', []) 
    try: stake = float(data.get('stake', 0))
    except ValueError: stake = 0
    
    if stake < 10:
        return jsonify({'success': False, 'message': 'Minimum stake is 10 KSH.'}), 400
        
    user = users[session['user']]
    if user['balance'] < stake:
        return jsonify({'success': False, 'message': 'Insufficient account balance.'}), 400
        
    if not selections:
        return jsonify({'success': False, 'message': 'Your betslip coupon is completely empty.'}), 400

    current_fixtures = {}
    for f in current_state['italian_fixtures']: current_fixtures[f['id']] = f
    for f in current_state['english_fixtures']: current_fixtures[f['id']] = f
    
    validated_selections = []
    accumulated_odds = 1.0
    
    for sel in selections:
        fix_id = sel.get('fixture_id')
        market = sel.get('market') 
        if fix_id not in current_fixtures:
            return jsonify({'success': False, 'message': 'Invalid match selection.'}), 400
            
        fixture = current_fixtures[fix_id]
        market_odds = fixture['odds'][market]
        accumulated_odds *= market_odds
        
        validated_selections.append({
            'fixture_id': fix_id,
            'home': fixture['home'],
            'away': fixture['away'],
            'market': market,
            'odds': market_odds
        })
        
    accumulated_odds = round(accumulated_odds, 2)
    user['balance'] -= stake
    
    placed_bets.append({
        'id': f"ticket_{int(time.time())}_{random.randint(1000,9999)}",
        'email': session['user'],
        'round': current_state['round'],
        'season': current_state['season'],
        'selections': validated_selections,
        'stake': stake,
        'total_odds': accumulated_odds,
        'status': 'PENDING'
    })
    
    return jsonify({'success': True, 'message': 'Bet ticket submitted and successfully verified!'})

@app.route('/deposit', methods=['POST'])
def deposit():
    if 'user' not in session: return redirect(url_for('login'))
    try: amount = int(float(request.form.get('amount', 0)))
    except ValueError: amount = 0
    if amount >= 10:
        users[session['user']]['balance'] += amount
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user' not in session: return redirect(url_for('login'))
    if not users.get(session['user'], {}).get('is_admin', False): return "Forbidden", 403
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'start' and not state['is_running']:
            state['is_running'] = True
            state['start_time'] = time.time() - state['paused_elapsed']
        elif action == 'stop' and state['is_running']:
            state['is_running'] = False
            state['paused_elapsed'] = time.time() - state['start_time']
            
    current_state = get_current_match_state()
    
    # Generate live rows of placed bets for admin supervision
    bet_rows = ""
    for b in reversed(placed_bets):
        legs_desc = ", ".join([f"{l['home']}-{l['away']} ({l['market']})" for l in b['selections']])
        color = "#ffcc00" if b['status'] == 'PENDING' else ("#00ff66" if b['status'] == 'WON' else "#ff3333")
        bet_rows += f'''
        <tr>
            <td style="padding:8px; border-bottom:1px solid #1c2a39;">{b['email']}</td>
            <td style="padding:8px; border-bottom:1px solid #1c2a39; font-size:12px;">{legs_desc}</td>
            <td style="padding:8px; border-bottom:1px solid #1c2a39;">{b['stake']} KSH</td>
            <td style="padding:8px; border-bottom:1px solid #1c2a39; color:{color}; font-weight:bold;">{b['status']}</td>
        </tr>
        '''

    return f'''
    <body style="background:#0b1118; color:white; font-family:sans-serif; padding:30px; margin:0;">
        <div style="max-width:900px; margin:0 auto;">
            <h2 style="color:#ffcc00; border-bottom:2px solid #1c2a39; padding-bottom:10px;">🛠️ SWIFTPITCH ADMIN COMMAND CENTRE</h2>
            
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:20px;">
                <div style="background:#121b26; padding:15px; border-radius:6px; border:1px solid #1c2a39;">
                    <p style="margin:0 0 5px 0; color:#a0aec0;">System Vault Reserve</p>
                    <h2 style="margin:0; color:#00ff66;">{state['company_balance']:,} KSH</h2>
                </div>
                <div style="background:#121b26; padding:15px; border-radius:6px; border:1px solid #1c2a39;">
                    <p style="margin:0 0 5px 0; color:#a0aec0;">Engine Status</p>
                    <h2 style="margin:0; color:#ffcc00;">{"RUNNING" if state['is_running'] else "PAUSED"}</h2>
                </div>
            </div>

            <form method="POST" style="margin-bottom:30px;">
                <button type="submit" name="action" value="start" style="padding:12px 24px; background:#00ff66; border:none; margin-right:10px; font-weight:bold; cursor:pointer; border-radius:4px;">START SIMULATION</button>
                <button type="submit" name="action" value="stop" style="padding:12px 24px; background:#ff3333; color:white; border:none; font-weight:bold; cursor:pointer; border-radius:4px;">PAUSE SIMULATION</button>
            </form>

            <h3 style="color:#ffcc00;">📋 USER RISK ASSIGNMENT LEDGER (LIVE BETS)</h3>
            <table style="width:100%; border-collapse:collapse; background:#121b26; text-align:left;">
                <thead>
                    <tr style="background:#1c2a39; color:#a0aec0;">
                        <th style="padding:10px;">User Account</th>
                        <th style="padding:10px;">Leg Selections</th>
                        <th style="padding:10px;">Stake</th>
                        <th style="padding:10px;">Outcome</th>
                    </tr>
                </thead>
                <tbody>
                    {bet_rows if bet_rows else '<tr><td colspan="4" style="padding:15px; text-align:center; color:#a0aec0;">No bets placed yet this round.</td></tr>'}
                </tbody>
            </table>
            
            <br><br><a href="/" style="color:#ffcc00; text-decoration:none; font-weight:bold;">← Back to Sportsbook Dashboard</a>
        </div>
    </body>
    '''

@app.route('/api/state')
def get_state():
    current_state = get_current_match_state()
    standings_ita = get_league_standings(current_state['round'], ITALIAN_TEAMS, 111)
    standings_eng = get_league_standings(current_state['round'], ENGLISH_TEAMS, 222)
    
    # Process pending bets
    for b in placed_bets:
        if b['status'] == 'PENDING' and b['round'] < current_state['round']:
            past_ita = {f['home']: f for f in generate_fixtures_for_round(b['round'], ITALIAN_TEAMS, 111)}
            past_eng = {f['home']: f for f in generate_fixtures_for_round(b['round'], ENGLISH_TEAMS, 222)}
            past_fixtures = {**past_ita, **past_eng}
            
            ticket_failed = False
            for leg in b['selections']:
                fix = past_fixtures.get(leg['home'])
                if not fix:
                    ticket_failed = True; break
                hs, as_ = fix['home_score'], fix['away_score']
                if leg['market'] == 'HOME' and not (hs > as_): ticket_failed = True
                elif leg['market'] == 'DRAW' and not (hs == as_): ticket_failed = True
                elif leg['market'] == 'AWAY' and not (as_ > hs): ticket_failed = True
                if ticket_failed: break
                
            if ticket_failed:
                b['status'] = 'LOST'
                state['company_balance'] += b['stake'] 
            else:
                b['status'] = 'WON'
                payout = round(b['stake'] * b['total_odds'], 2)
                users[b['email']]['balance'] += payout
                state['company_balance'] -= (payout - b['stake']) 

    if current_state['phase'] == 'PLAYING':
        commentary_line = generate_live_commentary(current_state['italian_fixtures'], current_state['english_fixtures'], current_state['time_into_loop'], current_state['round'])
        logs_feed = [
            f"[System] Season {current_state['season']} | Round #{current_state['round']} active.",
            commentary_line
        ]
    else:
        logs_feed = [
            f"[System] Season {current_state['season']} | Round #{current_state['round']} active.",
            "🎙️ [Pre-Match] Market open! Construct your cross-league multibet slip now."
        ]

    return {
        'phase': current_state['phase'],
        'time': current_state['time'],
        'round': current_state['round'],
        'season': current_state['season'],
        'italian_fixtures': current_state['italian_fixtures'],
        'english_fixtures': current_state['english_fixtures'],
        'standings_ita': standings_ita,
        'standings_eng': standings_eng,
        'logs': logs_feed
    }

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
