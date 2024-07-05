# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt, generate_password_hash, check_password_hash

db = SQLAlchemy()
bcrypt = Bcrypt()

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __str__(self):
        return self.name

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    date_joined = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    is_superuser = db.Column(db.Boolean, default=False, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    role = db.relationship('Role', backref=db.backref('users', lazy=True))

    profile_picture = db.Column(db.String(255), nullable=True)

    # Additional fields
    phone = db.Column(db.String(20), nullable=True)
    street = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    zip_code = db.Column(db.String(20), nullable=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f"User(id={self.id}, name='{self.name}', email='{self.email}')"


class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    ticker = db.Column(db.String(10), unique=True, nullable=False)
    open_price = db.Column(db.Float, nullable=False)
    close_price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"Stock(id={self.id}, name='{self.name}', ticker='{self.ticker}', open_price={self.open_price}, close_price={self.close_price})"


class Watchlist(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('watchlist', lazy=True))
    stock = db.relationship('Stock', backref=db.backref('watchlist', lazy=True))

    def __repr__(self):
        return f"Watchlist(user_id={self.user_id}, stock_id={self.stock_id})"

class UserInteraction(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_input = db.Column(db.String(255), nullable=False)
    assistant_response = db.Column(db.String(255), nullable=False)
    plot_filename = db.Column(db.String(255), nullable=True)

    user = db.relationship('User', backref=db.backref('interactions', lazy=True))

    def __repr__(self):
        return f"UserInteraction(id={self.id}, user_id={self.user_id}, user_input='{self.user_input}', assistant_response='{self.assistant_response}', plot_filename='{self.plot_filename}')"