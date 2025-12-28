from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='viewer') # admin, owner, viewer


    def get_id(self):
        return str(self.id)

class Team(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    owner_name = db.Column(db.String(100))
    purse = db.Column(db.Float, default=100.0)
    
    # Relationship with players
    # Relationship with players
    all_players = db.relationship('Player', backref='team', lazy=True)

    @property
    def players(self):
        return {
            'batsmen': [p for p in self.all_players if p.category == 'batsmen'],
            'bowlers': [p for p in self.all_players if p.category == 'bowlers'],
            'wicketkeepers': [p for p in self.all_players if p.category == 'wicketkeepers'],
            'allrounders': [p for p in self.all_players if p.category == 'allrounders']
        }

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'owner_name': self.owner_name,
            'purse': self.purse,
            'stats': self.calculate_stats()
        }

    @property
    def stats(self):
        stats = {
            'batsmen_count': 0, 'bowlers_count': 0, 
            'wicketkeepers_count': 0, 'allrounders_count': 0
        }
        for player in self.all_players:
            # Check player category and increment count
            # Ensure category matches the keys (batsmen, etc)
            cat_key = f"{player.category.lower()}_count"
            if cat_key in stats:
                stats[cat_key] += 1
        return stats

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    player_number = db.Column(db.Integer)
    base_price = db.Column(db.Float, default=0.0)
    selling_price = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='untouched')
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team_name = db.Column(db.String(100)) # Denormalized for Supabase view
    
    # Polymorphic identity
    type = db.Column(db.String(50))
    
    __mapper_args__ = {
        'polymorphic_identity': 'player',
        'polymorphic_on': type
    }
    
    @property
    def category(self):
        return self.type

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.type, # Use type as category
            'player_number': self.player_number,
            'base_price': self.base_price,
            'status': self.status,
            'selling_price': self.selling_price,
            'sold_to': self.team.name if self.team else None,
            'stats': {} # Base player has no stats, overridden by subclasses
        }

class Batsman(Player):
    id = db.Column(db.Integer, db.ForeignKey('player.id'), primary_key=True)
    player_name = db.Column(db.String(100)) # Denormalized for Supabase view
    matches = db.Column(db.Integer)
    runs = db.Column(db.Integer)
    average = db.Column(db.Float)
    strike_rate = db.Column(db.Float)
    highest_score = db.Column(db.Integer)
    fifties = db.Column(db.Integer)
    hundreds = db.Column(db.Integer)

    __mapper_args__ = {
        'polymorphic_identity': 'batsmen',
    }
    
    def to_dict(self):
        data = super().to_dict()
        data['stats'] = self.stats
        return data

    @property
    def stats(self):
        return {
            'matches': self.matches,
            'runs': self.runs,
            'average': self.average,
            'strike_rate': self.strike_rate,
            'highest_score': self.highest_score,
            'fifties': self.fifties,
            'hundreds': self.hundreds
        }


class Bowler(Player):
    id = db.Column(db.Integer, db.ForeignKey('player.id'), primary_key=True)
    player_name = db.Column(db.String(100)) # Denormalized for Supabase view
    matches = db.Column(db.Integer)
    wickets = db.Column(db.Integer)
    economy = db.Column(db.Float)
    best_bowling = db.Column(db.String(20))

    __mapper_args__ = {
        'polymorphic_identity': 'bowlers',
    }

    def to_dict(self):
        data = super().to_dict()
        data['stats'] = self.stats
        return data

    @property
    def stats(self):
        return {
            'matches': self.matches,
            'wickets': self.wickets,
            'economy': self.economy,
            'best_bowling': self.best_bowling
        }


class WicketKeeper(Player):
    id = db.Column(db.Integer, db.ForeignKey('player.id'), primary_key=True)
    player_name = db.Column(db.String(100)) # Denormalized for Supabase view
    matches = db.Column(db.Integer)
    runs = db.Column(db.Integer)
    average = db.Column(db.Float)
    strike_rate = db.Column(db.Float)
    highest_score = db.Column(db.Integer)
    fifties = db.Column(db.Integer)
    hundreds = db.Column(db.Integer)

    __mapper_args__ = {
        'polymorphic_identity': 'wicketkeepers',
    }

    def to_dict(self):
        data = super().to_dict()
        data['stats'] = self.stats
        return data

    @property
    def stats(self):
        return {
            'matches': self.matches,
            'runs': self.runs,
            'average': self.average,
            'strike_rate': self.strike_rate,
            'highest_score': self.highest_score,
            'fifties': self.fifties,
            'hundreds': self.hundreds
        }


class AllRounder(Player):
    id = db.Column(db.Integer, db.ForeignKey('player.id'), primary_key=True)
    player_name = db.Column(db.String(100)) # Denormalized for Supabase view
    matches = db.Column(db.Integer)
    runs = db.Column(db.Integer)
    average = db.Column(db.Float)
    strike_rate = db.Column(db.Float)
    highest_score = db.Column(db.Integer)
    fifties = db.Column(db.Integer)
    hundreds = db.Column(db.Integer)
    wickets = db.Column(db.Integer)
    economy = db.Column(db.Float)
    best_bowling = db.Column(db.String(20))

    __mapper_args__ = {
        'polymorphic_identity': 'allrounders',
    }

    def to_dict(self):
        data = super().to_dict()
        data['stats'] = self.stats
        return data

    @property
    def stats(self):
        return {
            'matches': self.matches,
            'runs': self.runs,
            'average': self.average,
            'strike_rate': self.strike_rate,
            'highest_score': self.highest_score,
            'fifties': self.fifties,
            'hundreds': self.hundreds,
            'wickets': self.wickets,
            'economy': self.economy,
            'best_bowling': self.best_bowling
        }


class BidHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
