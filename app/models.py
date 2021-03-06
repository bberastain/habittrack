from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from app import db, login
from flask_login import UserMixin
from time import time
import jwt
from flask import current_app


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    habit = db.relationship('Habit', backref='author', lazy='dynamic')
    book = db.relationship('Book', backref='reader', lazy='dynamic')
    life = db.relationship('Life', backref='person', lazy='dynamic')

# the backref creates a habit.author expression
# that returns the user given the habit

# what does lazy='dynamic' mean?

    def __repr__(self):
        return '<User: {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit = db.Column(db.String(140))  # index so it views in same order?
    start_date = db.Column(db.Date, default=date.today)
    # when you pass a function as a default, SQLAlchemy will set the field
    # to the value of calling that function
    # say x = datetime.utcnow(), so you need x.day
    # notice parenthesis here ^ but none over here ^
    end_date = db.Column(db.Date, default=date(9999, 1, 1))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    completed = db.relationship('Completed', backref='habit', lazy='dynamic')

# should I add another field so they can choose the order of habits?

    def __repr__(self):
        return '<Habit: {}>'.format(self.habit)


class Completed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'))

    def __repr__(self):
        return '<Completed: id-{}, date-{}>'.format(self.id, self.date)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140))
    author = db.Column(db.String(140))
    date = db.Column(db.Date)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Id: {}, Title: {}, Author: {}, Date Finished: {}>'.format(
            self.id, self.title, self.author, self.date)


class Life(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer)
    week = db.Column(db.Integer)
    content = db.Column(db.String(280))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Year: {}, Week: {}>'.format(self.year, self.week)
