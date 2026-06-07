from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import os
import time
import random
import threading

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'swiftpitch_clean_slate_2026')

# Thread safety lock to prevent concurrent modification crashes on cloud servers
state_lock = threading.Lock()

# --- LEAGUE CONTEXT CONFIGURATIONS ---
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

# Precise Cycle Constants
BETTING_WINDOW = 72.0
MATCH_WINDOW = 55.0

state = {
    'house_balance': 750000.0,
    'simulation_running': True,     
    'last_update': time.time(),
    'current_round': 1,
    'league_phase': 'BETTING',       
    'phase_start_time': time.time(),
    'season_fixtures_italian': {},
    'season_fixtures_english': {},
    'live_matches_italian': [],
    'live_matches_english': [],
    'match_logs': [],
    'sports_bets': [],               
    'standings_italian': {},
    'standings_english': {},
    'aviator': {'phase': 'BETTING', 'start': time.time(), 'multiplier': 1.0, 'stakes': {}}
}

users = {
    'admin@swiftpitch.com': {'password': 'adminpassword', 'phone': '0700000000', 'balance': 0.0, 'bonus': 0.0, 'bonus_locked': False, 'role': 'admin'},
    'player@swiftpitch.com': {'password': 'password123', 'phone': '0711223344', 'balance': 5000.0, 'bonus': 100.0, 'bonus_locked': True, 'role': 'user'}
}

def init_standings():
    state['standings_italian'] = {team: {'played': 0, 'won': 0, 'draw': 0, 'lost': 0, 'points': 0} for team in ITALIAN_TEAMS}
    state['standings_english'] = {team: {'played': 0, 'won': 0, 'draw': 0, 'lost': 0, 'points': 0} for team in ENGLISH_TEAMS}

def build_round_robin_schedule(teams, league_tag):
    rotation = list(teams)
    random.shuffle(rotation)
    n = len(rotation)
    schedule = {}
    match_id = 1 if league_tag == 'ITALIAN' else 5000
    
    for r in range(n - 1): 
        round_num = r + 1
        schedule[round_num] = []
        for i in range(n // 2):
            t1 = rotation[i]
            t2 = rotation[n - 1 - i]
            schedule[round_num].append({
                'id': match_id,
                'league': league_tag,
                'teams': f"{t1} vs {t2}",
                't1': t1,
                't2': t2,
                'score': '0-0',
                'status': 'PENDING',
                'minute': 0,
                'odds_home': round(random.uniform(1.4, 3.2), 2),
                'odds_draw': round(random.uniform(2.6, 3.6), 2),
                'odds_away': round(random.uniform(2.1, 4.5), 2),
                'timeline': []  
            })
            match_id += 1
        rotation = [rotation[0]] + [rotation[-1]] + rotation[1:-1]
    return schedule

def load_league_round_fixtures():
    r = state['current_round']
    if r > 19:
        state['current_round'] = 1
        r = 1
        init_standings()
        state['season_fixtures_italian'] = build_round_robin_schedule(ITALIAN_TEAMS, 'ITALIAN')
        state['season_fixtures_english'] = build_round_robin_schedule(ENGLISH_TEAMS, 'ENGLISH')

    state['live_matches_italian'] = state['season_fixtures_italian'][r]
    state['live_matches_english'] = state['season_fixtures_english'][r]
    
    for m in state['live_matches_italian'] + state['live_matches_english']:
        m['status'] = 'BETTING'
        m['minute'] = 0
        m['score'] = '0-0'
        m['timeline'] = []

def precalculate_match_events():
    for m in state['live_matches_italian'] + state['live_matches_english']:
        m['status'] = 'LIVE'
        gh = random.choices([0, 1, 2, 3], weights=[40, 35, 18, 7])[0]
        ga = random.choices([0, 1, 2, 3], weights=[45, 35, 15, 5])[0]
        
        timeline = []
        for _ in range(gh): timeline.append({'min': random.randint(1, 89), 'side': 'H'})
        for _ in range(ga): timeline.append({'min': random.randint(1, 89), 'side': 'A'})
        m['timeline'] = sorted(timeline, key=lambda x: x['min'])

init_standings()
state['season_fixtures_italian'] = build_round_robin_schedule(ITALIAN_TEAMS, 'ITALIAN')
state['season_fixtures_english'] = build_round_robin_schedule(ENGLISH_TEAMS, 'ENGLISH')
load_league_round_fixtures()

def dynamic_engine_loop():
    now = time.time()
    dt = now - state['last_update']
    state['last_update'] = now
    
    # --- AVIATOR CORE SIMULATION LOOP ---
    av_elapsed = now - state['aviator']['start']
    if state['aviator']['phase'] == 'BETTING' and av_elapsed > 12:
        state['aviator']['phase'] = 'FLYING'
        state['aviator']['start'] = now
        state['aviator']['multiplier'] = 1.0
    elif state['aviator']['phase'] == 'FLYING':
        state['aviator']['multiplier'] += round(dt * 0.6, 2)
        current_multiplier = state['aviator']['multiplier']
        
        # Process Auto Cash Out Parameters Before Crash Boundaries Execute
        auto_cashed_users = []
        for user_email, wager_info in state['aviator']['stakes'].items():
            target = wager_info.get('auto_cashout')
            if target and current_multiplier >= target:
                winnings = wager_info['stake'] * target
                if user_email in users:
                    users[user_email]['balance'] += winnings
                state['house_balance'] -= winnings
                auto_cashed_users.append(user_email)
                
        for user_email in auto_cashed_users:
            state['aviator']['stakes'].pop(user_email, None)

        # Dynamic Break/Crash Threshold Check
        if state['aviator']['multiplier'] > random.uniform(1.15, 6.0):
            state['aviator']['phase'] = 'BETTING'
            state['aviator']['start'] = now
            state['aviator']['stakes'] = {} 

    if not state['simulation_running']:
        return

    # Unified Match Clock Scheduler (72s / 55s)
    elapsed_phase = now - state['phase_start_time']
    if state['league_phase'] == 'BETTING':
        if elapsed_phase >= BETTING_WINDOW:
            state['league_phase'] = 'LIVE'
            state['phase_start_time'] = now
            precalculate_match_events()
            
    elif state['league_phase'] == 'LIVE':
        if elapsed_phase >= MATCH_WINDOW:
            finalize_and_settle_round()
            state['current_round'] += 1
            state['league_phase'] = 'BETTING'
            state['phase_start_time'] = now
            load_league_round_fixtures()
        else:
            ratio = elapsed_phase / MATCH_WINDOW
            current_game_minute = int(ratio * 90)
            
            for m in state['live_matches_italian'] + state['live_matches_english']:
                m['minute'] = current_game_minute
                home_goals = sum(1 for g in m['timeline'] if g['min'] <= current_game_minute and g['side'] == 'H')
                away_goals = sum(1 for g in m['timeline'] if g['min'] <= current_game_minute and g['side'] == 'A')
                m['score'] = f"{home_goals}-{away_goals}"

def finalize_and_settle_round():
    all_live = state['live_matches_italian'] + state['live_matches_english']
    match_map = {m['id']: m for m in all_live}
    
    for m in all_live:
        m['status'] = 'FINISHED'
        m['minute'] = 90
        s1, s2 = map(int, m['score'].split('-'))
        t1, t2 = m['t1'], m['t2']
        standings = state['standings_italian'] if m['league'] == 'ITALIAN' else state['standings_english']
        
        standings[t1]['played'] += 1
        standings[t2]['played'] += 1
        if s1 > s2:
            standings[t1]['won'] += 1; standings[t1]['points'] += 3
            standings[t2]['lost'] += 1
        elif s2 > s1:
            standings[t2]['won'] += 1; standings[t2]['points'] += 3
            standings[t1]['lost'] += 1
        else:
            standings[t1]['draw'] += 1; standings[t1]['points'] += 1
            standings[t2]['draw'] += 1; standings[t2]['points'] += 1
            
        state['match_logs'].append(f"[{m['league']}] Rd {state['current_round']} | {m['teams']} ({m['score']})")

    for bet in state['sports_bets']:
        if bet['status'] != 'PENDING':
            continue
            
        all_selections_resolved = True
        any_selection_lost = False
        
        for sel in bet['selections']:
            m = match_map.get(sel['match_id'])
            if m:
                s1, s2 = map(int, m['score'].split('-'))
                actual_outcome = '1' if s1 > s2 else ('2' if s2 > s1 else 'X')
                if actual_outcome == sel['prediction']:
                    sel['status'] = 'WON'
                else:
                    sel['status'] = 'LOST'
                    any_selection_lost = True
            else:
                all_selections_resolved = False
                
        if any_selection_lost:
            bet['status'] = 'LOST'
        elif all_selections_resolved and all(s['status'] == 'WON' for s in bet['selections']):
            bet['status'] = 'WON'
            payout = bet['stake'] * bet['total_odds']
            user_profile = users.get(bet['user'])
            if user_profile:
                user_profile['balance'] += payout
            state['house_balance'] -= payout

# --- ROUTES & CORE ENGINE HANDLERS ---

@app.route('/')
def index():
    if 'user' not in session
