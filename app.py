from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

def load_players():
    """Load players data from JSON file with error handling"""
    try:
        with open('data/players.json', 'r') as f:
            data = json.load(f)
            # Ensure the required structure exists
            if 'all_players' not in data:
                data['all_players'] = {'batsmen': [], 'bowlers': [], 'wicketkeepers': [], 'allrounders': []}
            if 'available_players' not in data:
                data['available_players'] = {'batsmen': [], 'bowlers': [], 'wicketkeepers': [], 'allrounders': []}
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        default_data = {
            'all_players': {'batsmen': [], 'bowlers': [], 'wicketkeepers': [], 'allrounders': []},
            'available_players': {'batsmen': [], 'bowlers': [], 'wicketkeepers': [], 'allrounders': []}
        }
        save_players(default_data)
        return default_data

def save_players(players_data):
    """Save players data to JSON file"""
    with open('data/players.json', 'w') as f:
        json.dump(players_data, f, indent=4)

def load_teams():
    """Load teams data from JSON file with error handling"""
    try:
        with open('data/teams.json', 'r') as f:
            data = json.load(f)
            return data.get('teams', [])
    except (FileNotFoundError, json.JSONDecodeError):
        print("Teams data file not found or invalid")
        return []

def save_teams(teams_data):
    """Save teams data to JSON file"""
    with open('data/teams.json', 'w') as f:
        json.dump({'teams': teams_data}, f, indent=4)

@app.route('/')
def index():
    """Home page with player selection and teams overview"""
    players_data = load_players()
    teams_data = load_teams()

    # Process and sort available players for each category
    available_players = {}
    for category in players_data['available_players']:
        players = players_data['available_players'][category]
        # Ensure each player has required attributes
        for player in players:
            if 'player_number' not in player:
                player['player_number'] = 0  # Default value
            if 'status' not in player:
                player['status'] = 'untouched'
            if 'base_price' not in player:
                player['base_price'] = 5.0
        # Sort players by number
        available_players[category] = sorted(players, key=lambda x: x.get('player_number', 0))

    return render_template('index.html', 
                         players=available_players, 
                         teams=teams_data)

@app.route('/teams')
def teams():
    """Teams page showing detailed team information"""
    teams_data = load_teams()
    return render_template('teams.html', teams=teams_data)

@app.route('/players')
def players():
    """View all players page"""
    players_data = load_players()
    all_players = {category: sorted(players_data['all_players'][category], key=lambda x: x.get('player_number', 0))
                   for category in players_data['all_players']}
    return render_template('players.html', players=all_players)

@app.route('/team/<team_name>')
def view_team(team_name):
    """View specific team details"""
    teams_data = load_teams()
    team = next((t for t in teams_data if t['name'] == team_name), None)
    if team:
        # Calculate total money spent for each category
        total_spent = {
            'batsmen': sum(player.get('selling_price', player['base_price']) for player in team['players']['batsmen']),
            'bowlers': sum(player.get('selling_price', player['base_price']) for player in team['players']['bowlers']),
            'wicketkeepers': sum(player.get('selling_price', player['base_price']) for player in team['players']['wicketkeepers']),
            'allrounders': sum(player.get('selling_price', player['base_price']) for player in team['players']['allrounders']),
        }
        # Calculate overall total
        total_spent['overall'] = sum(total_spent.values())
        return render_template('team_detail.html', team=team, total_spent=total_spent)
    return redirect(url_for('teams'))
    return render_template('team_detail.html', team=team)
    return redirect(url_for('teams'))

def evaluate_team(team):
    """Calculate team score and analysis based on player composition"""
    score = 0
    strengths = []
    weaknesses = []

    # Evaluate batting strength
    if team['stats']['batsmen_count'] >= 4:
        score += 5
        strengths.append(f"Strong batting lineup with {team['stats']['batsmen_count']} batsmen")
    else:
        weaknesses.append(f"Need more specialist batsmen (currently {team['stats']['batsmen_count']})")

    # Evaluate bowling strength
    if team['stats']['bowlers_count'] >= 4:
        score += 5
        strengths.append(f"Well-rounded bowling attack with {team['stats']['bowlers_count']} bowlers")
    else:
        weaknesses.append(f"Bowling attack needs strengthening (currently {team['stats']['bowlers_count']})")

    # Evaluate wicketkeeper presence
    if team['stats']['wicketkeepers_count'] >= 1:
        score += 5
        strengths.append(f"Has {team['stats']['wicketkeepers_count']} dedicated wicketkeeper(s)")
    else:
        weaknesses.append("Missing specialist wicketkeeper")

    # Evaluate all-rounders
    if team['stats']['allrounders_count'] >= 2:
        score += 5
        strengths.append(f"Good balance with {team['stats']['allrounders_count']} all-rounders")
    else:
        weaknesses.append(f"Need more all-rounders for team balance (currently {team['stats']['allrounders_count']})")

    # Evaluate budget management
    #if team['purse'] > 30:
    #    score += 20
    #    strengths.append(f"Good budget management (₹{team['purse']}M remaining)")
    #else:
    #    weaknesses.append(f"Limited budget remaining (₹{team['purse']}M)")

    return {
        'score': score,
        'grade': 'A+' if score >= 18 else 'A' if score >= 15 else 'B' if score >= 12 else 'C' if score >= 9 else 'D',
        'strengths': strengths,
        'weaknesses': weaknesses,
        'stats': team['stats']
    }

@app.route('/add-player', methods=['GET', 'POST'])
def add_player():
    if request.method == 'POST':
        try:
            category = request.form.get('category')
            if not category or category not in ['batsmen', 'bowlers', 'wicketkeepers', 'allrounders']:
                flash('Invalid player category', 'error')
                return redirect(url_for('add_player'))

            players = load_players()

            start_number = {
                'batsmen': 1,
                'bowlers': 101,
                'wicketkeepers': 201,
                'allrounders': 301
            }.get(category, 1)

            existing_numbers = [p.get('player_number', 0) for p in players['all_players'][category]]
            next_number = max([num for num in existing_numbers if num >= start_number] or [start_number - 1]) + 1

            # Get base price from the form input
            base_price = float(request.form.get('base_price', 0))  # Default to 0 if not provided
            if base_price <= 0:
                flash('Base price must be greater than 0', 'error')
                return redirect(url_for('add_player'))

            player_data = {
                'player_number': next_number,
                'name': request.form.get('name'),
                'base_price': base_price,  # Use the base price from the form
                'status': 'available',
                'stats': {
                    'matches': int(request.form.get('matches', 0)),
                    'runs': int(request.form.get('runs', 0)) if category in ['batsmen', 'wicketkeepers', 'allrounders'] else 0,
                    'average': float(request.form.get('average', 0)) if category in ['batsmen', 'wicketkeepers', 'allrounders'] else 0,
                    'strike_rate': float(request.form.get('strike_rate', 0)) if category in ['batsmen', 'wicketkeepers', 'allrounders'] else 0,
                    'highest_score': int(request.form.get('highest_score', 0)) if category in ['batsmen', 'wicketkeepers', 'allrounders'] else 0,
                    'fifties': int(request.form.get('fifties', 0)) if category in ['batsmen', 'wicketkeepers', 'allrounders'] else 0,
                    'hundreds': int(request.form.get('hundreds', 0)) if category in ['batsmen', 'wicketkeepers', 'allrounders'] else 0,
                    'wickets': int(request.form.get('wickets', 0)) if category in ['bowlers', 'allrounders'] else 0,
                    'economy': float(request.form.get('economy', 0)) if category in ['bowlers', 'allrounders'] else 0,
                    'best_bowling': request.form.get('best_bowling', '0/0') if category in ['bowlers', 'allrounders'] else ''
                }
            }

            players['all_players'][category].append(player_data)
            players['available_players'][category].append(player_data.copy())
            save_players(players)

            flash('Player added successfully', 'success')
            return redirect(url_for('players'))
        except Exception as e:
            flash(f'Error adding player: {str(e)}', 'error')
            return redirect(url_for('add_player'))

    return render_template('add_player.html')

@app.route('/api/player/<category>/<player_name>/action', methods=['POST'])
def player_action(category, player_name):
    try:
        action = request.json.get('action')
        team_name = request.json.get('team')
        price = float(request.json.get('price', 0))

        # Ensure the minimum selling price is 2
        if action == 'sold' and price < 2:
            return jsonify({'error': 'Minimum selling price is 2'}), 400

        players = load_players()
        teams = load_teams()

        if action == 'sold':
            # Find the player and team
            player = next((p for p in players['available_players'][category] 
                        if p['name'] == player_name), None)
            team = next((t for t in teams if t['name'] == team_name), None)

            if not player:
                return jsonify({'error': 'Player not found'}), 404
            if not team:
                return jsonify({'error': 'Team not found'}), 404

            if team['purse'] >= price:
                # Update player status and store the selling price
                player['status'] = 'sold'
                player['selling_price'] = price  # Store the selling price

                # Update the same player in all_players
                all_player = next((p for p in players['all_players'][category] 
                                if p['name'] == player_name), None)
                if all_player:
                    all_player['status'] = 'sold'
                    all_player['selling_price'] = price  # Store the selling price

                # Remove from available players
                players['available_players'][category] = [
                    p for p in players['available_players'][category]
                    if p['name'] != player_name
                ]

                # Add to team
                team['players'][category].append(player)
                team['purse'] -= price
                team['stats'][f'{category}_count'] += 1

                save_players(players)
                save_teams(teams)
                return jsonify({'success': True})
            return jsonify({'error': 'Insufficient team budget'}), 400

        elif action == 'unsold':
            # Update player status in both available_players and all_players
            player = next((p for p in players['available_players'][category] 
                        if p['name'] == player_name), None)
            all_player = next((p for p in players['all_players'][category] 
                            if p['name'] == player_name), None)

            if player:
                player['status'] = 'unsold'
                player.pop('selling_price', None)  # Remove selling price if it exists
            if all_player:
                all_player['status'] = 'unsold'
                all_player.pop('selling_price', None)  # Remove selling price if it exists

            save_players(players)
            return jsonify({'success': True})

        return jsonify({'error': 'Invalid action'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/team/<team_name>/reset', methods=['POST'])
def reset_team(team_name):
    try:
        teams = load_teams()
        players = load_players()

        # Find the team to reset
        team = next((t for t in teams if t['name'] == team_name), None)
        if not team:
            return jsonify({'error': 'Team not found'}), 404

        # Restore the team's purse to its original value (assuming original purse is 100M)
        original_purse = 100  # Change this to the actual original purse value if different
        team['purse'] = original_purse

        # Move all players back to the available players list and reset their status
        for category in ['batsmen', 'bowlers', 'wicketkeepers', 'allrounders']:
            for player in team['players'][category]:
                player['status'] = 'untouched'
                players['available_players'][category].append(player)
            # Clear the team's players in this category
            team['players'][category] = []
            # Reset the player count for this category
            team['stats'][f'{category}_count'] = 0

        # Save the updated data
        save_teams(teams)
        save_players(players)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/remove-player-all', methods=['POST'])
def remove_player_all():
    data = request.json
    player_name = data.get('player')
    category = data.get('category')
    
    players = load_players()
    teams = load_teams()
    
    # Find the player in all_players
    player = next((p for p in players['all_players'].get(category, []) if p['name'] == player_name), None)
    if not player:
        return jsonify({'error': 'Player not found'}), 404

    # Check if player is in a team
    for team in teams:
        for cat in ['batsmen', 'bowlers', 'wicketkeepers', 'allrounders']:
            team_players = team['players'].get(cat, [])
            for p in team_players:
                if p['name'] == player_name:
                    team['purse'] += p.get('selling_price', p['base_price'])
                    team['players'][cat] = [pl for pl in team_players if pl['name'] != player_name]
                    team['stats'][f'{cat}_count'] -= 1
                    save_teams(teams)
                    break

    # Remove from all_players and available_players
    players['all_players'][category] = [p for p in players['all_players'][category] if p['name'] != player_name]
    players['available_players'][category] = [p for p in players['available_players'][category] if p['name'] != player_name]
    
    save_players(players)
    return jsonify({'success': True})

@app.route('/api/remove-player', methods=['POST'])
def remove_player():
    try:
        data = request.json
        team_name = data.get('team')
        player_name = data.get('player')
        category = data.get('category')

        if not all([team_name, player_name, category]):
            return jsonify({'error': 'Missing required fields'}), 400

        teams = load_teams()
        players = load_players()

        team = next((t for t in teams if t['name'] == team_name), None)
        if not team:
            return jsonify({'error': 'Team not found'}), 404

        # Find player in team
        player = next((p for p in team['players'][category] 
                    if p['name'] == player_name), None)
        if not player:
            return jsonify({'error': 'Player not found in team'}), 404

        # Increase team's purse by the selling price (stored in the player's data)
        selling_price = player.get('selling_price', player['base_price'])  # Default to base_price if selling_price is not set
        team['purse'] += selling_price

        # Remove from team
        team['players'][category] = [
            p for p in team['players'][category]
            if p['name'] != player_name
        ]
        team['stats'][f'{category}_count'] -= 1

        # Add back to available players with status 'untouched'
        player['status'] = 'untouched'
        players['available_players'][category].append(player)

        save_teams(teams)
        save_players(players)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/evaluation')
def evaluation():
    """Team evaluation page showing analysis of all teams"""
    teams_data = load_teams()
    evaluations = {}

    for team in teams_data:
        evaluations[team['name']] = evaluate_team(team)

    return render_template('evaluation.html', teams=teams_data, evaluations=evaluations)

def evaluate_team(team):
    """Calculate team score and analysis based on player composition"""
    score = 0
    strengths = []
    weaknesses = []

    # Initialize stats for evaluation
    total_runs_batsmen = 0
    total_runs_allrounders = 0
    total_runs_wicketkeepers = 0
    total_wickets_bowlers = 0
    total_wickets_allrounders = 0
    total_matches = 0
    total_average_batsmen = 0
    total_average_allrounders = 0
    total_average_wicketkeepers = 0
    total_strike_rate_batsmen = 0
    total_strike_rate_allrounders = 0
    total_strike_rate_wicketkeepers = 0
    total_economy_bowlers = 0
    total_economy_allrounders = 0
    total_fifties_batsmen = 0
    total_fifties_allrounders = 0
    total_fifties_wicketkeepers = 0
    total_hundreds_batsmen = 0
    total_hundreds_allrounders = 0
    total_hundreds_wicketkeepers = 0

    batsmen_count = 0
    bowlers_count = 0
    allrounders_count = 0
    wicketkeepers_count = 0

    # Calculate stats for each category
    for category in ['batsmen', 'bowlers', 'wicketkeepers', 'allrounders']:
        for player in team['players'][category]:
            total_matches += player['stats']['matches']
            if category == 'batsmen':
                total_runs_batsmen += player['stats']['runs']
                total_average_batsmen += player['stats']['average']
                total_strike_rate_batsmen += player['stats']['strike_rate']
                total_fifties_batsmen += player['stats']['fifties']
                total_hundreds_batsmen += player['stats']['hundreds']
                batsmen_count += 1
            elif category == 'wicketkeepers':
                total_runs_wicketkeepers += player['stats']['runs']
                total_average_wicketkeepers += player['stats']['average']
                total_strike_rate_wicketkeepers += player['stats']['strike_rate']
                total_fifties_wicketkeepers += player['stats']['fifties']
                total_hundreds_wicketkeepers += player['stats']['hundreds']
                wicketkeepers_count += 1
            elif category == 'allrounders':
                total_runs_allrounders += player['stats']['runs']
                total_average_allrounders += player['stats']['average']
                total_strike_rate_allrounders += player['stats']['strike_rate']
                total_fifties_allrounders += player['stats']['fifties']
                total_hundreds_allrounders += player['stats']['hundreds']
                total_wickets_allrounders += player['stats']['wickets']
                total_economy_allrounders += player['stats']['economy']
                allrounders_count += 1
            elif category == 'bowlers':
                total_wickets_bowlers += player['stats']['wickets']
                total_economy_bowlers += player['stats']['economy']
                bowlers_count += 1

    # Calculate averages
    avg_runs_batsmen = total_runs_batsmen / batsmen_count if batsmen_count > 0 else 0
    avg_runs_wicketkeepers = total_runs_wicketkeepers / wicketkeepers_count if wicketkeepers_count > 0 else 0
    avg_runs_allrounders = total_runs_allrounders / allrounders_count if allrounders_count > 0 else 0
    avg_average_batsmen = total_average_batsmen / batsmen_count if batsmen_count > 0 else 0
    avg_average_wicketkeepers = total_average_wicketkeepers / wicketkeepers_count if wicketkeepers_count > 0 else 0
    avg_average_allrounders = total_average_allrounders / allrounders_count if allrounders_count > 0 else 0
    avg_strike_rate_batsmen = total_strike_rate_batsmen / batsmen_count if batsmen_count > 0 else 0
    avg_strike_rate_wicketkeepers = total_strike_rate_wicketkeepers / wicketkeepers_count if wicketkeepers_count > 0 else 0
    avg_strike_rate_allrounders = total_strike_rate_allrounders / allrounders_count if allrounders_count > 0 else 0
    avg_economy_bowlers = total_economy_bowlers / bowlers_count if bowlers_count > 0 else 0
    avg_economy_allrounders = total_economy_allrounders / allrounders_count if allrounders_count > 0 else 0

    # Evaluate batting strength (batsmen only)
    if batsmen_count >= 7 and avg_average_batsmen > 40 and avg_strike_rate_batsmen > 150 and total_runs_batsmen > 2000:
        score += 25
        strengths.append(f"Strong batting lineup with {batsmen_count} batsmen, average of {avg_average_batsmen:.2f}, strike rate of {avg_strike_rate_batsmen:.2f}, and {total_runs_batsmen} runs")
    elif batsmen_count >= 5 and avg_average_batsmen > 30 and avg_strike_rate_batsmen > 130 and total_runs_batsmen > 1500:
        score += 15
        strengths.append(f"Decent batting lineup with {batsmen_count} batsmen, average of {avg_average_batsmen:.2f}, strike rate of {avg_strike_rate_batsmen:.2f}, and {total_runs_batsmen} runs")
    elif batsmen_count >= 3 and avg_average_batsmen > 15 and avg_strike_rate_batsmen > 100 and total_runs_batsmen > 500:
        score += 10
        strengths.append(f"Average batting lineup with {batsmen_count} batsmen, average of {avg_average_batsmen:.2f}, strike rate of {avg_strike_rate_batsmen:.2f}, and {total_runs_batsmen} runs")
    else:
        weaknesses.append(f"Batting lineup needs improvement: {batsmen_count} batsmen, average of {avg_average_batsmen:.2f}, strike rate of {avg_strike_rate_batsmen:.2f}, and {total_runs_batsmen} runs")

    # Evaluate bowling strength (bowlers only)
    if bowlers_count >= 7 and avg_economy_bowlers < 8 and total_wickets_bowlers > 100:
        score += 25
        strengths.append(f"Excellent bowling attack with {bowlers_count} bowlers, economy of {avg_economy_bowlers:.2f}, and {total_wickets_bowlers} wickets")
    elif bowlers_count >= 5 and avg_economy_bowlers < 10 and total_wickets_bowlers > 50:
        score += 15
        strengths.append(f"Good bowling attack with {bowlers_count} bowlers, economy of {avg_economy_bowlers:.2f}, and {total_wickets_bowlers} wickets")
    elif bowlers_count >= 3 and avg_economy_bowlers < 12 and total_wickets_bowlers > 20:
        score += 10
        strengths.append(f"Average bowling attack with {bowlers_count} bowlers, economy of {avg_economy_bowlers:.2f}, and {total_wickets_bowlers} wickets")
    else:
        weaknesses.append(f"Bowling attack needs improvement: {bowlers_count} bowlers, economy of {avg_economy_bowlers:.2f}, and {total_wickets_bowlers} wickets")

    # Evaluate all-rounders
    if allrounders_count >= 7 and avg_average_allrounders > 30 and avg_economy_allrounders < 8 and avg_strike_rate_allrounders > 120 and total_wickets_allrounders > 50:
        score += 20
        strengths.append(f"Good balance with {allrounders_count} all-rounders, average of {avg_average_allrounders:.2f}, economy of {avg_economy_allrounders:.2f}, and {total_wickets_allrounders} wickets with {avg_strike_rate_allrounders:.2f} strike rate")
    elif allrounders_count >= 5 and avg_average_allrounders > 20 and avg_economy_allrounders < 10 and avg_strike_rate_allrounders > 110 and total_wickets_allrounders > 20:
        score += 15
        strengths.append(f"Decent balance with {allrounders_count} all-rounders, average of {avg_average_allrounders:.2f}, economy of {avg_economy_allrounders:.2f}, and {total_wickets_allrounders} wickets with {avg_strike_rate_allrounders:.2f} strike rate")
    elif allrounders_count >= 3 and avg_average_allrounders > 12 and avg_economy_allrounders < 15 and avg_strike_rate_allrounders > 100 and total_wickets_allrounders > 10:
        score += 5
        strengths.append(f"Average balance with {allrounders_count} all-rounders, average of {avg_average_allrounders:.2f}, economy of {avg_economy_allrounders:.2f}, and {total_wickets_allrounders} wickets with {avg_strike_rate_allrounders:.2f} strike rate")
    else:
        weaknesses.append(f"Need more all-rounders for team balance: {allrounders_count} all-rounders, average of {avg_average_allrounders:.2f}, economy of {avg_economy_allrounders:.2f}, and {total_wickets_allrounders} wickets and {avg_strike_rate_allrounders:.2f} strike rate")

    # Evaluate wicketkeepers
    if wicketkeepers_count >= 3 and avg_average_wicketkeepers > 30 and avg_strike_rate_wicketkeepers > 130:
        score += 10
        strengths.append(f"Has {wicketkeepers_count} dedicated wicketkeeper(s) with an average of {avg_average_wicketkeepers:.2f} and strike rate of {avg_strike_rate_wicketkeepers:.2f}")
    elif wicketkeepers_count >= 2 and avg_average_wicketkeepers > 15 and avg_strike_rate_wicketkeepers > 100:
        score += 5
        strengths.append(f"Has {wicketkeepers_count} dedicated wicketkeeper(s) with an average of {avg_average_wicketkeepers:.2f} and strike rate of {avg_strike_rate_wicketkeepers:.2f}")
    else:
        weaknesses.append(f"Missing specialist wicketkeepers or wicketkeeper stats need improvement because of an average of {avg_average_wicketkeepers:.2f} and strike rate of {avg_strike_rate_wicketkeepers:.2f}")

    # Evaluate team composition
    if batsmen_count >= 5:
        score += 5
        strengths.append(f"Strong batting lineup with {batsmen_count} batsmen")
    else:
        weaknesses.append(f"Need more specialist batsmen (currently {batsmen_count})")

    if bowlers_count >= 5:
        score += 5
        strengths.append(f"Well-rounded bowling attack with {bowlers_count} bowlers")
    else:
        weaknesses.append(f"Bowling attack needs strengthening (currently {bowlers_count})")

    if wicketkeepers_count >= 3:
        score += 5
        strengths.append(f"Has {wicketkeepers_count} dedicated wicketkeeper(s)")
    else:
        weaknesses.append("Missing specialist wicketkeeper")

    if allrounders_count >= 5:
        score += 5
        strengths.append(f"Good balance with {allrounders_count} all-rounders")
    else:
        weaknesses.append(f"Need more specialist all-rounders (currently {allrounders_count})")

    # Cap the score at 100
    score = min(score, 100)

    return {
        'score': score,
        'grade': 'A+' if score >= 90 else 'A' if score >= 80 else 'B+' if score >= 70 else 'B' if score >= 60 else 'C' if score >= 50 else 'C+' if score >= 40 else 'D',
        'strengths': strengths,
        'weaknesses': weaknesses,
        'stats': {
            'batsmen_count': batsmen_count,
            'bowlers_count': bowlers_count,
            'wicketkeepers_count': wicketkeepers_count,
            'allrounders_count': allrounders_count,
            'avg_runs_batsmen': avg_runs_batsmen,
            'avg_runs_wicketkeepers': avg_runs_wicketkeepers,
            'avg_runs_allrounders': avg_runs_allrounders,
            'avg_average_batsmen': avg_average_batsmen,
            'avg_average_wicketkeepers': avg_average_wicketkeepers,
            'avg_average_allrounders': avg_average_allrounders,
            'avg_strike_rate_batsmen': avg_strike_rate_batsmen,
            'avg_strike_rate_wicketkeepers': avg_strike_rate_wicketkeepers,
            'avg_strike_rate_allrounders': avg_strike_rate_allrounders,
            'avg_economy_bowlers': avg_economy_bowlers,
            'avg_economy_allrounders': avg_economy_allrounders,
            'total_runs_batsmen': total_runs_batsmen,
            'total_runs_wicketkeepers': total_runs_wicketkeepers,
            'total_runs_allrounders': total_runs_allrounders,
            'total_wickets_bowlers': total_wickets_bowlers,
            'total_wickets_allrounders': total_wickets_allrounders,
            'total_fifties_batsmen': total_fifties_batsmen,
            'total_fifties_wicketkeepers': total_fifties_wicketkeepers,
            'total_fifties_allrounders': total_fifties_allrounders,
            'total_hundreds_batsmen': total_hundreds_batsmen,
            'total_hundreds_wicketkeepers': total_hundreds_wicketkeepers,
            'total_hundreds_allrounders': total_hundreds_allrounders,
            'total_matches': total_matches
        }
    }


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)