from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nickname = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    joke_balance = db.Column(db.Integer, default=0)
    jokes = db.relationship('Joke', backref='author', lazy='dynamic')
    role = db.Column(db.String(10), default='User')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_moderator(self):
        return self.role == 'Moderator'

class Joke(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Add created_at field
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ratings = db.relationship('Rating', backref='joke', lazy=True)

    def average_rating(self):
        ratings = [rating.value for rating in self.ratings]
        return sum(ratings) / len(ratings) if ratings else 0
class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    joke_id = db.Column(db.Integer, db.ForeignKey('joke.id'), nullable=False)