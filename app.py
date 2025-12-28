from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import os
from dotenv import load_dotenv
from models import db, Team, Player, BidHistory, Batsman, Bowler, WicketKeeper, AllRounder
from sqlalchemy import func

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SUPABASE_DB_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/')
def index():
    """Home page with player selection and teams overview"""
    teams_data = Team.query.all()
    
    # Process available players
    # Fetch ALL players so frontend can filter by status (Available, Sold, Unsold)
    available_players_query = Player.query.all()
    
    available_players = {
        'batsmen': [], 'bowlers': [], 'wicketkeepers': [], 'allrounders': []
    }
    
    for player in available_players_query:
        # Group by category
        cat = player.category
        if cat in available_players:
            # Convert to dict for template if needed, or pass object
            # Template expects player['name'], player['base_price'], etc.
            # Start strict: DB objects can be accessed like attributes
            # BUT existing templates use dict syntax {{ player.name }} works for both IF access is attribute-like
            # Jinja2 handles dot notation for both dict keys and object attributes transparently.
            # Except if template uses player['name'] explicitly.
            # Let's check templates later. Safe bet is objects.
            available_players[cat].append(player)
            
    # Sort by number
    for cat in available_players:
        available_players[cat].sort(key=lambda x: x.player_number or 0)

    return render_template('index.html', 
                         players=available_players, 
                         teams=teams_data)

@app.route('/teams')
def teams():
    """Teams page showing detailed team information"""
    teams_data = Team.query.all()
    return render_template('teams.html', teams=teams_data)

@app.route('/players')
def players():
    """View all players page"""
    all_players_query = Player.query.all()
    all_players = {
        'batsmen': [], 'bowlers': [], 'wicketkeepers': [], 'allrounders': []
    }
    for player in all_players_query:
        if player.category in all_players:
            all_players[player.category].append(player)
            
    for cat in all_players:
        all_players[cat].sort(key=lambda x: x.player_number or 0)
        
    return render_template('players.html', players=all_players)

@app.route('/team/<team_name>')
def view_team(team_name):
    """View specific team details"""
    team = Team.query.filter_by(name=team_name).first()
    if team:
        # Calculate money spent
        total_spent = {
            'batsmen': 0, 'bowlers': 0, 'wicketkeepers': 0, 'allrounders': 0, 'overall': 0
        }
        
        for player in team.all_players:
            price = player.selling_price or player.base_price
            cat = player.category
            if cat in total_spent:
                total_spent[cat] += price
                total_spent['overall'] += price
        
        return render_template('team_detail.html', team=team, total_spent=total_spent)
    return redirect(url_for('teams'))

@app.route('/add-player', methods=['GET', 'POST'])
def add_player():
    if request.method == 'POST':
        try:
            category = request.form.get('category')
            print(f"DEBUG: Adding player. Category: {category}, Name: {request.form.get('name')}")
            
            # Simple Validation
            if not category or category not in ['batsmen', 'bowlers', 'wicketkeepers', 'allrounders']:
                print(f"DEBUG: Invalid category '{category}'")
                flash('Invalid player category', 'error')
                return redirect(url_for('add_player'))

            # Calculate next number
            # Query max player number in this category
            # Calculate next player number (Gap Filling)
            start_number = {
                'batsmen': 1, 'bowlers': 101, 'wicketkeepers': 201, 'allrounders': 301
            }.get(category, 1)

            # Get all existing numbers for this category
            existing_numbers = set(p.player_number for p in Player.query.filter_by(type=category).all() if p.player_number)
            
            next_number = start_number
            while next_number in existing_numbers:
                next_number += 1
            
            print(f"DEBUG: Calculated Gap-Filling Player Number: {next_number}")

            base_price = float(request.form.get('base_price', 0))
            if base_price < 0:
                flash('Base price cannot be negative', 'error')
                return redirect(url_for('add_player'))

            # Calculate lowest available ID (Gap Filling)
            # Fetch all existing IDs
            existing_ids = [p.id for p in Player.query.all()]
            new_id = 1
            while new_id in existing_ids:
                new_id += 1
            


            # Create specific player instance based on category
            if category == 'batsmen':
                player = Batsman(
                    id=new_id,
                    name=request.form.get('name'),
                    player_name=request.form.get('name'), # Denormalized
                    player_number=next_number,
                    base_price=base_price,
                    status='untouched',
                    matches=int(request.form.get('matches') or 0),
                    runs=int(request.form.get('runs') or 0),
                    average=float(request.form.get('average') or 0),
                    strike_rate=float(request.form.get('strike_rate') or 0),
                    highest_score=int(request.form.get('highest_score') or 0),
                    fifties=int(request.form.get('fifties') or 0),
                    hundreds=int(request.form.get('hundreds') or 0)
                )
            elif category == 'bowlers':
                player = Bowler(
                    id=new_id,
                    name=request.form.get('name'),
                    player_name=request.form.get('name'), # Denormalized
                    player_number=next_number,
                    base_price=base_price,
                    status='untouched',
                    matches=int(request.form.get('matches') or 0),
                    wickets=int(request.form.get('wickets') or 0),
                    economy=float(request.form.get('economy') or 0),
                    best_bowling=request.form.get('best_bowling') or '0/0'
                )
            elif category == 'wicketkeepers':
                player = WicketKeeper(
                    id=new_id,
                    name=request.form.get('name'),
                    player_name=request.form.get('name'), # Denormalized
                    player_number=next_number,
                    base_price=base_price,
                    status='untouched',
                    matches=int(request.form.get('matches') or 0),
                    runs=int(request.form.get('runs') or 0),
                    average=float(request.form.get('average') or 0),
                    strike_rate=float(request.form.get('strike_rate') or 0),
                    highest_score=int(request.form.get('highest_score') or 0),
                    fifties=int(request.form.get('fifties') or 0),
                    hundreds=int(request.form.get('hundreds') or 0)
                )
            elif category == 'allrounders':
                player = AllRounder(
                    id=new_id,
                    name=request.form.get('name'),
                    player_name=request.form.get('name'), # Denormalized
                    player_number=next_number,
                    base_price=base_price,
                    status='untouched',
                    matches=int(request.form.get('matches') or 0),
                    runs=int(request.form.get('runs') or 0),
                    average=float(request.form.get('average') or 0),
                    strike_rate=float(request.form.get('strike_rate') or 0),
                    highest_score=int(request.form.get('highest_score') or 0),
                    fifties=int(request.form.get('fifties') or 0),
                    hundreds=int(request.form.get('hundreds') or 0),
                    wickets=int(request.form.get('wickets') or 0),
                    economy=float(request.form.get('economy') or 0),
                    best_bowling=request.form.get('best_bowling') or '0/0'
                )
            
            db.session.add(player)
            db.session.commit()

            flash('Player added successfully', 'success')
            return redirect(url_for('add_player'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding player: {str(e)}', 'error')
            return redirect(url_for('add_player'))

    return render_template('add_player.html')

@app.route('/add-team', methods=['POST'])
def add_team():
    if request.method == 'POST':
        try:
            team_name = request.form.get('team_name')
            owner_name = request.form.get('owner_name')
            
            if not team_name:
                flash('Team name is required!', 'error')
                return redirect(url_for('add_player'))

            if Team.query.filter(func.lower(Team.name) == func.lower(team_name)).first():
                flash('Team already exists!', 'error')
                return redirect(url_for('add_player'))

            # Calculate lowest available ID (Gap Filling)
            # Fetch all existing IDs
            existing_ids = [t.id for t in Team.query.all()]
            new_id = 1
            while new_id in existing_ids:
                new_id += 1
            
            print(f"DEBUG: Calculated Gap-Filling Team ID: {new_id}")
                
            new_team = Team(
                id=new_id,
                name=team_name,
                owner_name=owner_name,
                purse=100.0
            )
            
            db.session.add(new_team)
            db.session.commit()

            flash('Team added successfully', 'success')
            return redirect(url_for('add_player'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding team: {str(e)}', 'error')
            return redirect(url_for('add_player'))

@app.route('/api/player/<int:player_id>/action', methods=['POST'])
def player_action(player_id):
    try:
        data = request.json
        action = data.get('action')
        team_name = data.get('team')
        price = float(data.get('price', 0))

        if action == 'sold' and price < 2:
            return jsonify({'error': 'Minimum selling price is 2'}), 400

        # Look up player directly by ID
        player = db.session.get(Player, player_id)
        if not player:
            return jsonify({'error': 'Player not found'}), 404

        if action == 'sold':
            team = Team.query.filter_by(name=team_name).first()
            if not team:
                return jsonify({'error': 'Team not found'}), 404

            if team.purse >= price:
                player.status = 'sold'
                player.selling_price = price
                player.team_id = team.id
                player.team_name = team.name # Denormalized
                
                team.purse -= price
                
                db.session.commit()
                return jsonify({'success': True})
            return jsonify({'error': 'Insufficient team budget'}), 400

        elif action == 'unsold':
            player.status = 'unsold'
            player.selling_price = None
            player.team_id = None
            player.team_name = None # Clear denormalized
            db.session.commit()
            return jsonify({'success': True})

        return jsonify({'error': 'Invalid action'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/team/<team_name>/reset', methods=['POST'])
def reset_team(team_name):
    try:
        team = Team.query.filter_by(name=team_name).first()
        if not team:
            return jsonify({'error': 'Team not found'}), 404

        team.purse = 100.0
        
        # Reset all players in this team
        for player in team.all_players:
            player.status = 'untouched'
            player.selling_price = None
            player.team_id = None # Removes from team
            player.team_name = None # Clear denormalized
            
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/team/<team_name>/update-purse', methods=['POST'])
def update_team_purse(team_name):
    try:
        data = request.json
        amount = float(data.get('amount', 0))
        
        if amount < 0:
            return jsonify({'error': 'Amount must be non-negative'}), 400

        team = Team.query.filter_by(name=team_name).first()
        if not team:
            return jsonify({'error': 'Team not found'}), 404

        team.purse = amount
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/team/<team_name>/delete', methods=['POST'])
def delete_team(team_name):
    try:
        team = Team.query.filter_by(name=team_name).first()
        if team:
            # Release all players first
            for p in team.all_players:
                p.status = 'untouched'
                p.selling_price = None
                p.team_id = None
                p.team_name = None # Clear denormalized
            
            db.session.delete(team)
            db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/remove-player', methods=['POST'])
def remove_player():
    try:
        data = request.json
        team_name = data.get('team')
        player_name = data.get('player')
        category = data.get('category')

        team = Team.query.filter_by(name=team_name).first()
        if not team:
            return jsonify({'error': 'Team not found'}), 404

        player = Player.query.filter_by(name=player_name, team_id=team.id).first()
        if not player:
            return jsonify({'error': 'Player not found in team'}), 404

        selling_price = player.selling_price or player.base_price
        team.purse += selling_price
        
        player.status = 'untouched'
        player.selling_price = None
        player.team_id = None
        player.team_name = None # Clear denormalized
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/remove-player-all', methods=['POST'])
def remove_player_all():
    try:
        data = request.json
        player_name = data.get('player')

        # Find player by name (polymorphic)
        player = Player.query.filter_by(name=player_name).first()
        
        if not player:
            return jsonify({'error': 'Player not found'}), 404

        # If player is sold, refund the team first
        if player.status == 'sold' and player.team_id:
             team = db.session.get(Team, player.team_id)
             if team:
                 team.purse += (player.selling_price or player.base_price)

        db.session.delete(player)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-player', methods=['POST'])
def update_player():
    try:
        data = request.json
        category = data.get('category')
        original_name = data.get('original_name')
        updates = data.get('updates', {})

        # Query generic player first to check existence
        player = Player.query.filter_by(name=original_name).first() # polymorphic load
        if not player:
            return jsonify({'error': 'Player not found'}), 404
            
        if player.type != category:
             return jsonify({'error': 'Category mismatch'}), 400

        # Update base fields if any (currently none in updates dict usually)
        
        # Update subclass specific fields
        # Define allowed fields per category
        allowed_fields = {
            'batsmen': ['matches', 'runs', 'average', 'strike_rate', 'highest_score', 'fifties', 'hundreds'],
            'bowlers': ['matches', 'wickets', 'economy', 'best_bowling'],
            'wicketkeepers': ['matches', 'runs', 'average', 'strike_rate', 'highest_score', 'fifties', 'hundreds'],
            'allrounders': ['matches', 'runs', 'average', 'strike_rate', 'highest_score', 'fifties', 'hundreds', 'wickets', 'economy', 'best_bowling']
        }
        
        # Helper to unpack updates - frontend sends {name: "foo", stats: {runs: 10, ...}}
        stats_updates = updates.get('stats', {})
        
        # Update name if present
        if 'name' in updates:
            player.name = updates['name']
            
            # Update denormalized player_name in subclass
            # Polymorphic load means 'player' is already the instance of Batsman/Bowler etc.
            if hasattr(player, 'player_name'):
                player.player_name = updates['name']

        fields = allowed_fields.get(category, [])
        for field in fields:
            # Check in stats object first, then top-level updates (backward compat)
            if field in stats_updates:
                setattr(player, field, stats_updates[field])
            elif field in updates:
                setattr(player, field, updates[field])
        
        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/team/<team_name>/update', methods=['POST'])
def update_team(team_name):
    try:
        data = request.json
        new_name = data.get('name')
        new_owner = data.get('owner_name')
        
        team = Team.query.filter_by(name=team_name).first()
        if not team:
            return jsonify({'error': 'Team not found'}), 404
            
        if new_name != team_name:
             if Team.query.filter(func.lower(Team.name) == func.lower(new_name)).first():
                return jsonify({'error': 'Team name already exists'}), 400
             
             # Sync new team name to all players
             for p in team.all_players:
                 p.team_name = new_name
        
        team.name = new_name
        team.owner_name = new_owner
        
        # No need to manually update players Sold To if using Relation/ForeignKey?
        # status="sold", team_id=X. 
        # When displaying, we use player.team.name.
        # So renaming team AUTOMATICALLY reflects in all players!
        # This is the beauty of Relational DBs!
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/evaluation')
def evaluation():
    """Team evaluation page showing analysis of all teams"""
    teams_data = Team.query.all()
    evaluations = {}

    for team in teams_data:
        evaluations[team.name] = evaluate_team(team)

    return render_template('evaluation.html', teams=teams_data, evaluations=evaluations)

def evaluate_team(team):
    """Calculate team score and analysis based on player composition"""
    score = 0
    strengths = []
    weaknesses = []
    
    # We can use team.stats property we created in models.py
    stats = team.stats # This gives counts
    
    # But we need deeper stats (avg runs etc)
    # So we need to iterate players again
    
    # Reuse the logic from before but adapt dictionary access to object access
    # player['stats']['runs'] -> player.stats['runs']
    
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
    # Iterate through team.all_players relationship
    for player in team.all_players:
        # category is stored in type column but available as attribute if needed, 
        # or we check instance type. Polymorphic query returns specific instances!
        
        # However, for simplicity and compatibility with existing logic:
        category = player.type # 'batsmen', 'bowlers' etc.
        
        total_matches += getattr(player, 'matches', 0) or 0
        
        if category == 'batsmen':
            total_runs_batsmen += getattr(player, 'runs', 0) or 0
            total_average_batsmen += getattr(player, 'average', 0) or 0
            total_strike_rate_batsmen += getattr(player, 'strike_rate', 0) or 0
            total_fifties_batsmen += getattr(player, 'fifties', 0) or 0
            total_hundreds_batsmen += getattr(player, 'hundreds', 0) or 0
            batsmen_count += 1
        elif category == 'wicketkeepers':
            total_runs_wicketkeepers += getattr(player, 'runs', 0) or 0
            total_average_wicketkeepers += getattr(player, 'average', 0) or 0
            total_strike_rate_wicketkeepers += getattr(player, 'strike_rate', 0) or 0
            total_fifties_wicketkeepers += getattr(player, 'fifties', 0) or 0
            total_hundreds_wicketkeepers += getattr(player, 'hundreds', 0) or 0
            wicketkeepers_count += 1
        elif category == 'allrounders':
            total_runs_allrounders += getattr(player, 'runs', 0) or 0
            total_average_allrounders += getattr(player, 'average', 0) or 0
            total_strike_rate_allrounders += getattr(player, 'strike_rate', 0) or 0
            total_fifties_allrounders += getattr(player, 'fifties', 0) or 0
            total_hundreds_allrounders += getattr(player, 'hundreds', 0) or 0
            total_wickets_allrounders += getattr(player, 'wickets', 0) or 0
            total_economy_allrounders += getattr(player, 'economy', 0) or 0
            allrounders_count += 1
        elif category == 'bowlers':
            total_wickets_bowlers += getattr(player, 'wickets', 0) or 0
            total_economy_bowlers += getattr(player, 'economy', 0) or 0
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
    if batsmen_count >= 7 and avg_average_batsmen > 35 and avg_strike_rate_batsmen > 140 and total_runs_batsmen > 2000:
        score += 25
        strengths.append(f"Strong batting lineup with {batsmen_count} batsmen, average of {avg_average_batsmen:.2f}, strike rate of {avg_strike_rate_batsmen:.2f}, and {total_runs_batsmen} runs")
    elif batsmen_count >= 5 and avg_average_batsmen > 25 and avg_strike_rate_batsmen > 130 and total_runs_batsmen > 1500:
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
    if allrounders_count >= 7 and avg_average_allrounders > 25 and avg_economy_allrounders < 9 and avg_strike_rate_allrounders > 120 and total_wickets_allrounders > 50:
        score += 20
        strengths.append(f"Good balance with {allrounders_count} all-rounders, average of {avg_average_allrounders:.2f}, economy of {avg_economy_allrounders:.2f}, and {total_wickets_allrounders} wickets with {avg_strike_rate_allrounders:.2f} strike rate")
    elif allrounders_count >= 5 and avg_average_allrounders > 15 and avg_economy_allrounders < 12 and avg_strike_rate_allrounders > 110 and total_wickets_allrounders > 20:
        score += 15
        strengths.append(f"Decent balance with {allrounders_count} all-rounders, average of {avg_average_allrounders:.2f}, economy of {avg_economy_allrounders:.2f}, and {total_wickets_allrounders} wickets with {avg_strike_rate_allrounders:.2f} strike rate")
    elif allrounders_count >= 3 and avg_average_allrounders > 10 and avg_economy_allrounders < 15 and avg_strike_rate_allrounders > 100 and total_wickets_allrounders > 10:
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
    
    # Return structure matching original format stats
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
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)