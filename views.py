# views.py
from cgitb import text
from functools import wraps

from email_validator import validate_email, EmailNotValidError
from flask import Blueprint, render_template, request, redirect, url_for, flash, session,g
from sqlalchemy import func

from models import db, bcrypt, Role, User
from flask_mail import Message
from __init__ import mail
import random
import datetime
import pytz
import re



main_bp = Blueprint('main', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def send_otp(email, otp):
    subject = "OTP Verification"
    body = f"Your OTP for verification is: {otp}"
    msg = Message(subject, sender='your_email@gmail.com', recipients=[email])
    msg.body = body
    mail.send(msg)


def is_valid_email(email):
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False


@main_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        name = request.form['name']
        password1 = request.form["password"]
        password2 = request.form['password_confirmation']





        user = User.query.filter_by(email=email).first()

        if user:
            flash("Email already exists.", category="error")
        elif not email or not name or not password1 or not password2:
            flash("Please fill out all fields", category="error")
        elif len(email) < 4:
            flash("Email must be greater than 4 characters", category="error")
        elif not is_valid_email(email):
            flash("Email provided is not valid", category="error")
        elif len(name) < 2:
            flash("Name must be greater than 2 characters", category="error")
        elif password1 != password2:
            flash("Passwords don't match.", category="error")
        elif len(password1) < 8:
            flash("Password must be at least 8 characters", category="error")
        elif not re.search(r'[!@#$%^&*(),.?":{}|<>]', password1):
            flash("Password must have at least one special character", category="error")
        elif not re.search(r'\d', password1):
            flash("Password must have at least one digit", category="error")
        else:
            hashed_password = bcrypt.generate_password_hash(password1).decode('utf-8')

            role = Role.query.filter_by(name="unassigned").first()
            if not role:
                role = Role(name="unassigned")
                db.session.add(role)
                db.session.commit()

            user = User(name=name, email=email, password=hashed_password, role=role)
            db.session.add(user)
            db.session.commit()

            # **OTP Verification Step:**
            otp = random.randint(100000, 999999)
            session['email_verification_otp'] = otp
            session['email_verification_email'] = email
            session['otp_generation_time'] = datetime.datetime.now(pytz.utc).isoformat()
            session['signedin']= True
            session['name'] = name



            send_otp(email, otp)

            flash('An OTP has been sent to your email for verification.', category='success')
            return redirect(url_for('main.verify_email'))  # Redirect to OTP verification page

    return render_template('signup.html')
@main_bp.route('/verify_email', methods=['GET', 'POST'])
def verify_email():
    if request.method == "POST":
        otp_input = request.form['otp']
        email = session.get('email_verification_email')
        otp = session.get('email_verification_otp')
        otp_generation_time = session.get('otp_generation_time')

        if not email or not otp or not otp_generation_time:
            flash('OTP verification failed. Please try again.', 'error')
            return redirect(url_for('main.signup'))  # Redirect back to signup for clarity

        otp_generation_time = datetime.datetime.fromisoformat(otp_generation_time)
        if datetime.datetime.now(pytz.utc) > otp_generation_time + datetime.timedelta(minutes=10):
            flash('OTP has expired. Please try again.', 'error')
            return redirect(url_for('main_bp.signup'))  # Redirect back to signup for clarity

        if otp_input == str(otp):
            user = User.query.filter_by(email=email).first()
            if user:
                user.is_active = True
                db.session.commit()
                flash('You have successfully signed up', 'success')
                session['loggedin'] = True
                # **Redirect to Dashboard:**
                return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid OTP. Please try again.', 'error')

    return render_template('verify_email.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        session['name'] = user.name
        session['password'] = user.password

        if user and bcrypt.check_password_hash(user.password, password):
            if user.is_active:
                otp = random.randint(100000, 999999)
                session['login_otp'] = otp
                session['login_email'] = email
                session['otp_generation_time'] = datetime.datetime.now(pytz.utc).isoformat()
                send_otp(email, otp)
                flash('An OTP has been sent to your email for verification.')
                return redirect(url_for('main.verify_login_otp'))
            else:
                flash('Please verify your email first.')
                return redirect(url_for('main.signin'))
        else:
            flash('Invalid email or password.')
            return redirect(url_for('main.signin'))

    return render_template('signin.html')


@main_bp.route('/verify_login_otp', methods=['GET', 'POST'])
def verify_login_otp():


    if request.method == 'POST':

        user_otp = request.form['otp']
        email = session.get('login_email')
        otp = session.get('login_otp')
        otp_generation_time_str = session.get('otp_generation_time')



        if email and otp and otp_generation_time_str:
            otp_generation_time = datetime.datetime.fromisoformat(otp_generation_time_str).replace(tzinfo=pytz.utc)
            current_time = datetime.datetime.now(pytz.utc)

            if (current_time - otp_generation_time).total_seconds() > 300:  # 5 minutes expiration
                flash("OTP has expired. Please login again.")
                session.pop('login_otp', None)
                session.pop('otp_generation_time', None)
                return redirect(url_for('main.signin'))

            if int(user_otp) == otp:
                session['loggedin'] = True
                user = User.query.filter_by(email=email).first()
                session['user_id'] = user.id
                session['email'] = user.email

                session.pop('login_otp', None)
                session.pop('login_email', None)
                session.pop('otp_generation_time', None)
                flash("Logged in successfully!")
                return redirect(url_for('main.dashboard'))
            else:
                flash("Invalid OTP. Please try again.")
                return render_template('verify_login_otp.html')


        flash("Invalid session data. Please try again.")
        return redirect(url_for('main.signin'))


    return render_template('verify_login_otp.html')



@main_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['newpassword']
        confirm_password = request.form['confirm_newpassword']

        user = User.query.filter_by(email=session['email']).first()

        if user and bcrypt.check_password_hash(user.password, current_password):
            if new_password == confirm_password:
                if len(new_password) < 8:
                    flash("Password must be at least 8 characters long.", "error")
                elif not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
                    flash("Password must have at least one special character.", "error")
                elif not re.search(r'\d', new_password):
                    flash("Password must have at least one digit.", "error")
                else:
                    hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
                    user.password = hashed_password
                    db.session.commit()
                    flash('Your password has been updated!', 'success')
                    return redirect(url_for('main.dashboard'))
            else:
                flash('New password and confirm password do not match.', 'error')
        else:
            flash('Current password is incorrect.', 'error')

    return render_template('change_password.html')


@main_bp.route('/logout')
@login_required
def logout():
    # Clear all session data
    session.clear()
    # Optionally, you can add a flash message
    flash('You have been logged out successfully.', 'success')
    # Redirect to the login page
    return redirect(url_for('main.login'))


@main_bp.route('/lock_screen', methods=['GET', 'POST'])
@login_required
def lock_screen():
    if request.method == 'POST':
        password = request.form['password']
        email = session.get('email')

        if email:
            user = User.query.filter_by(email=email).first()
            if user and bcrypt.check_password_hash(user.password, password):
                session.pop('locked', None)  # Unlock the session
                return redirect(url_for('main.dashboard'))
            else:
                flash('Invalid password. Please try again.', 'error')

    session['locked'] = True  # Lock the session
    return render_template('lock_screen.html')



@main_bp.route('/home')
def home():
    if 'loggedin' in session:
        return render_template("dashboard.html")
    return redirect(url_for('main.login'))

def check_lock(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'locked' in session:
            return redirect(url_for('main.lock_screen'))
        return f(*args, **kwargs)
    return decorated_function

# Apply the custom decorator to the dashboard route
@main_bp.before_request
def before_request():
    if not request.endpoint or request.endpoint == 'lock_screen':
        return
    if 'locked' in session and request.endpoint == 'main.dashboard':
        return redirect(url_for('main.lock_screen'))

@main_bp.route('/dashboard')
def dashboard():
    if 'locked' in session:
        return redirect(url_for('main.lock_screen'))

    if 'loggedin' in session or "signedin" in session:
        username = session.get('name')
        return render_template('dashboard.html', user=username)

    return redirect(url_for('main.login'))