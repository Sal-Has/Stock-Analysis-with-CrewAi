# views.py
import signal
import subprocess
from functools import wraps
import yfinance as yf
from email_validator import validate_email, EmailNotValidError
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response, jsonify
from flask_bcrypt import check_password_hash
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename
from models import db, bcrypt, Role, User, Stock, Watchlist, UserInteraction
from flask_mail import Message
from __init__ import mail,cache
import random
import datetime
import pytz
import re
from forms import UploadForm, UpdateProfileForm
from PIL import Image
import os

streamlit_process =None

main_bp = Blueprint('main', __name__)


UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)






def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('main.login'))
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
                return redirect(url_for('main.login'))
        else:
            flash('Invalid email or password.')
            return redirect(url_for('main.login'))

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
                return redirect(url_for('main.login'))

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
        return redirect(url_for('main.login'))


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

@login_required
@main_bp.route('/dashboard')
@cache.cached(timeout=0)
def dashboard():
    if 'locked' in session:
        return redirect(url_for('main.lock_screen'))

    if 'loggedin' in session or 'signedin' in session:
        username = session.get('name')

        # Fetch user profile picture from session or database
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user:
                profile_picture = user.profile_picture  # Assuming profile_picture is stored in User model


        response = make_response(render_template('dashboard.html', user=user))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    return redirect(url_for('main.login'))


@main_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if user:
            otp = random.randint(100000, 999999)
            session['reset_password_otp'] = otp
            session['reset_password_email'] = email
            session['otp_generation_time'] = datetime.datetime.now(pytz.utc).isoformat()

            send_otp(email, otp)
            flash('An OTP has been sent to your email for password reset.', 'success')
            return redirect(url_for('main.verify_reset_otp'))
        else:
            flash('Email not found. Please check and try again.', 'error')

    return render_template('forgot_password.html')


@main_bp.route('/verify_reset_otp', methods=['GET', 'POST'])
def verify_reset_otp():
    if request.method == 'POST':
        otp_input = request.form['otp']
        email = session.get('reset_password_email')
        otp = session.get('reset_password_otp')
        otp_generation_time = session.get('otp_generation_time')

        if not email or not otp or not otp_generation_time:
            flash('OTP verification failed. Please try again.', 'error')
            return redirect(url_for('main.forgot_password'))

        otp_generation_time = datetime.datetime.fromisoformat(otp_generation_time)
        if datetime.datetime.now(pytz.utc) > otp_generation_time + datetime.timedelta(minutes=10):
            flash('OTP has expired. Please try again.', 'error')
            return redirect(url_for('main.forgot_password'))

        if otp_input == str(otp):
            flash('OTP verified successfully. Please enter a new password.', 'success')
            return redirect(url_for('main.reset_password'))
        else:
            flash('Invalid OTP. Please try again.', 'error')

    return render_template('verify_reset_otp.html')


@main_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        email = session.get('reset_password_email')

        if not email:
            flash('Session expired. Please try again.', 'error')
            return redirect(url_for('main.forgot_password'))

        if new_password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
        elif len(new_password) < 8:
            flash('Password must be at least 8 characters long.', 'error')
        elif not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
            flash('Password must have at least one special character.', 'error')
        elif not re.search(r'\d', new_password):
            flash('Password must have at least one digit.', 'error')
        else:
            user = User.query.filter_by(email=email).first()
            if user:
                hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
                user.password = hashed_password
                db.session.commit()
                flash('Your password has been updated successfully.', 'success')
                return redirect(url_for('main.login'))

    return render_template('reset_password.html')

@main_bp.route('/user-profile')
@login_required
def user_profile():
    # Fetch user information from your data source
    user_id = session.get('user_id')
    user = User.query.get(user_id)  # Replace with actual method to fetch user

    form = UpdateProfileForm()

    if user:
        return render_template('user-profile.html', user=user, form=form)
    else:
        # Handle the case where the user is not found
        flash('User not found', 'error')
        return redirect(url_for('main.dashboard'))  # Redirect to a safe default page
@main_bp.route('/account-settings')
@login_required
def account_settings():
    form = UploadForm()  # Create an instance of the form
    if 'loggedin' in session or 'signedin' in session:
        user = User.query.filter_by(email=session['email']).first()
        return render_template('account-settings.html', form=form, user=user)  # Pass the form and user to the template
    return redirect(url_for('main.login'))


@main_bp.route('/upload_profile_picture', methods=['GET', 'POST'])
@login_required  # Ensure user is logged in to access this route
def upload_profile_picture():
    form = UploadForm()

    if form.validate_on_submit():
        try:
            photo = form.photo.data
            filename = secure_filename(photo.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)

            # Save the uploaded file to the UPLOAD_FOLDER
            photo.save(filepath)

            # Open the image for further processing
            img = Image.open(filepath)

            # Get cropping coordinates from the form (x, y, width, height)
            x = int(form.x.data)
            y = int(form.y.data)
            width = int(form.width.data)
            height = int(form.height.data)

            # Crop and resize the image based on the user's selection
            cropped_img = img.crop((x, y, x + width, y + height))
            resized_img = cropped_img.resize((256, 256), Image.LANCZOS)

            # Save the processed image back to the same file
            resized_img.save(filepath, optimize=True, quality=85)

            # Update the user profile with the new picture
            user_id = session.get('user_id')  # Assuming you store user_id in session
            user = User.query.filter_by(id=user_id).first()
            if user:
                user.profile_picture = filename  # Save only the filename or the relative path
                db.session.commit()
                flash('Profile picture updated successfully!', 'success')
                return jsonify({'success': True, 'new_image_url': url_for('static', filename='uploads/' + filename)})
            else:
                return jsonify({'success': False, 'error': 'User not found.'}), 404

        except Exception as e:
            print(str(e))  # Log the error for debugging purposes
            return jsonify({'success': False, 'error': 'An error occurred while processing the image.'}), 500

    # Handle form validation errors
    errors = form.errors  # Assuming your form setup includes error handling
    return jsonify({'success': False, 'error': errors}), 400


@main_bp.route('/update_profile', methods=['GET', 'POST'])
@login_required
def edit_user_profile():
    user_id = session.get('user_id')
    if not user_id:
        flash('User ID not found in session.', 'error')
        return redirect(url_for('index'))

    user = User.query.get_or_404(user_id)
    form = UpdateProfileForm(obj=user)

    if form.validate_on_submit():
        user.name = form.name.data
        user.email = form.email.data
        user.phone = form.phone.data
        user.street = form.street.data
        user.city = form.city.data
        user.state = form.state.data
        user.zip_code = form.zip_code.data
        db.session.commit()

        # Display success message
        flash('Your profile has been successfully updated.', 'success')

        # Clear form data after successful update
        form.name.data = ''
        form.email.data = ''
        form.phone.data = ''
        form.street.data = ''
        form.city.data = ''
        form.state.data = ''
        form.zip_code.data = ''

        return redirect(url_for('main.edit_user_profile'))

    return render_template('user-profile.html', form=form, user=user)


@main_bp.route('/search_stock', methods=['GET'])
@login_required
def search_stock():
    try:
        # Fetch all stocks from the database
        stocks = Stock.query.all()
        user_id = session.get('user_id')
        user = User.query.get(user_id)

        return render_template('searchstock.html', stocks=stocks,user=user)

    except Exception as e:
        # Flash an error message to the user
        flash(f"An error occurred: {str(e)}", 'error')

        # Redirect to the search_stock page to handle the error gracefully
        return redirect(url_for('main.search_stock'))


@main_bp.route('/add_stock',methods=['POST'])
@login_required
def add_stock():
    try:
        ticker = request.form['new_data'].strip()

        if not ticker:
            flash('Ticker not provided in request data', 'error')
            return redirect(url_for('search_stock'))

        stock = yf.Ticker(ticker)
        stock_info = stock.info
        name = stock_info.get('longName', ticker)

        stock_data = stock.history(period='1d')

        if stock_data.empty:
            flash('No data found for the provided ticker', 'error')
            return redirect(url_for('search_stock'))

        latest_data = stock_data.iloc[-1]

        new_stock = Stock(
            name=name,
            ticker=ticker,
            open_price=latest_data['Open'],
            close_price=latest_data['Close']
        )

        db.session.add(new_stock)
        db.session.commit()

        flash('Stock added successfully', 'success')
        return redirect(url_for('main.search_stock'))

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('main.search_stock'))

@main_bp.route('/add_to_watchlist/<int:stock_id>', methods=['POST'])
@login_required
def add_to_watchlist(stock_id):
    try:
        stock = Stock.query.get(stock_id)
        if not stock:
            flash('Stock not found.', 'error')
            return redirect(url_for('main.search_stock'))

        watchlist_item = Watchlist(user_id=session.get('user_id'), stock_id=stock.id)
        db.session.add(watchlist_item)
        db.session.commit()

        flash(f'{stock.name} added to your watchlist.', 'success')
    except Exception as e:
        flash(f'Failed to add stock to watchlist: {str(e)}', 'error')

    return redirect(url_for('main.search_stock'))






@main_bp.route('/stock_input', methods=['GET'])
@login_required
def stock_input():
    # Assuming you obtain the user object somehow, replace with your logic
    user_id = session.get('user_id')
    user = User.query.filter_by(user_id).first()  # Replace with your actual user retrieval logic
    return render_template('stock_input.html', user=user)

@main_bp.route('/start-streamlit', methods=['POST'])
def start_streamlit():
    global streamlit_process
    if not streamlit_process:
        streamlit_process = subprocess.Popen(['streamlit', 'run', 'streamlit_app.py'])
        flash('Streamlit started successfully!', 'success')
    else:
        flash('Streamlit is already running.', 'info')
    return redirect(url_for('main.dashboard'))

@main_bp.route('/stop-streamlit', methods=['POST'])
def stop_streamlit():
    global streamlit_process

    if streamlit_process:
        try:
            # Check if OS is Windows (for cross-platform handling)
            if os.name == 'nt':
                streamlit_process.terminate()  # Terminate the process in Windows
            else:
                os.kill(streamlit_process.pid, signal.SIGTERM)  # Send SIGTERM signal in Unix-like systems
            streamlit_process = None
            flash('Streamlit stopped successfully!', 'success')
        except Exception as e:
            flash(f'Error stopping Streamlit: {str(e)}', 'error')
    else:
        flash('Streamlit is not running.', 'info')

    return redirect(url_for('main.dashboard'))



@main_bp.route('/store_interaction', methods=['POST'])
def store_interaction():
    try:
        data = request.json
        print(f"Received data: {data}")  # Debugging statement

        user_input = data.get('user_input')
        assistant_response = data.get('assistant_response')
        plot_filename = data.get('plot_filename')
        user_id = data.get('user_id')

        print(f"user_input: {user_input}, assistant_response: {assistant_response}, plot_filename: {plot_filename}")  # Debugging statement

        if not user_id:
            return jsonify({"error": "User not logged in"}), 400

        interaction = UserInteraction(
            user_id=user_id,
            user_input=user_input,
            assistant_response=assistant_response,
            plot_filename=plot_filename
        )

        db.session.add(interaction)
        db.session.commit()

        return jsonify({"message": "Interaction stored successfully"}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"SQLAlchemy error: {str(e)}")  # Debugging statement
        return jsonify({"error": "Database error"}), 500

    except Exception as e:
        print(f"Unexpected error: {str(e)}")  # Debugging statement
        return jsonify({"error": str(e)}), 500


@main_bp.route('/update_stock', methods=['POST'])
def update_stock():
    try:
        stock_id = request.form.get('stock_id')
        stock = Stock.query.get(stock_id)

        # Update stock attributes based on form submission data
        stock.ticker = request.form.get('ticker')
        stock.name = request.form.get('name')
        stock.open_price = request.form.get('open_price')
        stock.close_price = request.form.get('close_price')

        db.session.commit()

        flash('Stock updated successfully', 'success')
        return redirect(url_for('main.search_stock'))

    except Exception as e:
        flash(f'Failed to update stock: {str(e)}', 'error')
        return redirect(url_for('main.search_stock'))

@main_bp.route('/delete_stock', methods=['POST'])
def delete_stock():
    try:
        data = request.get_json()
        stock_id = data.get('stock_id')
        stock = Stock.query.get(stock_id)

        db.session.delete(stock)
        db.session.commit()

        flash('Stock deleted successfully', 'success')
        return redirect(url_for('main.search_stock'))

    except Exception as e:
        flash(f'Failed to delete stock: {str(e)}', 'error')
        return redirect(url_for('main.search_stock'))




@main_bp.route('/signup-admin', methods=['GET', 'POST'])
def signup_admin():
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

            # Assign 'admin' role directly
            admin_role = Role.query.filter_by(name='admin').first()
            if not admin_role:
                admin_role = Role(name='admin')
                db.session.add(admin_role)
                db.session.commit()

            user = User(name=name, email=email, password=hashed_password, role=admin_role)
            db.session.add(user)
            db.session.commit()

            # OTP Verification Step
            otp = random.randint(100000, 999999)
            session['email_verification_otp'] = otp
            session['email_verification_email'] = email
            session['otp_generation_time'] = datetime.datetime.now(pytz.utc).isoformat()

            send_otp(email, otp)

            # Redirect to OTP verification page
            flash('An OTP has been sent to your email for verification.', category='success')
            return redirect(url_for('main.verify_email_admin'))

    return render_template('signup-admin.html')


@main_bp.route('/verify-email-admin', methods=['GET', 'POST'])
def verify_email_admin():
    if request.method == 'POST':
        otp_attempt = request.form.get('otp')

        if 'email_verification_otp' in session and 'email_verification_email' in session:
            saved_otp = session['email_verification_otp']
            email = session['email_verification_email']

            if otp_attempt == str(saved_otp):
                # OTP verification successful
                user = User.query.filter_by(email=email).first()
                if user:
                    # Mark the session as signed in
                    session['signedin'] = True
                    session['user_id'] = user.id
                    session['name'] = user.name
                    session['email'] = user.email

                    # Check if the user's role is "admin"
                    if user.role.name == 'admin':
                        # Redirect to admin dashboard
                        return redirect(url_for('main.dashboard_admin'))

                    # For other roles or if role isn't specified, redirect to a general dashboard
                    return redirect(url_for('main.dashboard'))

            flash('Invalid OTP. Please try again.', category='error')
        else:
            flash('OTP session expired. Please resend OTP.', category='error')

    return render_template('verify_email.html')


@main_bp.route('/login-admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if user.role.name == 'admin' and check_password_hash(user.password, password):
                # Log in the user by setting session variables
                session['signedin'] = True
                session['user_id'] = user.id
                session['name'] = user.name
                session['email'] = user.email

                # Redirect to admin dashboard
                return redirect(url_for('main.dashboard_admin'))
            else:
                flash('Invalid email or password.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template('signin_admin.html')


@main_bp.route('/dashboard-admin')
def dashboard_admin():
    # Check if user is locked or not signed in
    if 'locked' in session:
        return redirect(url_for('main.lock_screen'))

    if 'signedin' in session:
        email = session.get('email')
        if not email:
            flash('No email found in session. Please log in again.', category='error')
            return redirect(url_for('main.login'))

        # Fetch current user from the database
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('User not found', category='error')
            return redirect(url_for('main.login'))

        # Fetch users with role 'unassigned'
        unassigned_role = Role.query.filter_by(name='unassigned').first()
        if unassigned_role:
            unassigned_users = User.query.filter_by(role_id=unassigned_role.id).all()
        else:
            unassigned_users = []

        # Prepare data for Highcharts - Pie Chart
        pie_chart_data = []
        for user in unassigned_users:
            pie_chart_data.append({
                'name': user.name,
                'y': 1  # Example: you need to format data appropriately for the pie chart
            })

        # Prepare data for Highcharts - Bar Chart
        bar_chart_data = []
        for user in unassigned_users:
            bar_chart_data.append({
                'name': user.name,
                'data': [1]  # Example: you need to format data appropriately for the bar chart
            })

        # Get profile picture from the user model (assuming profile_picture is a field in User model)
        profile_picture = user.profile_picture

        # Prevent caching of the response
        response = make_response(render_template('dashboard-admin.html',
                                                 user=user,
                                                 profile_picture=profile_picture,
                                                 unassigned_users=unassigned_users,
                                                 pie_chart_data=pie_chart_data,
                                                 bar_chart_data=bar_chart_data))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    # If not signed in, redirect to login page
    return redirect(url_for('main.login'))



@main_bp.route('/edit-user', methods=['POST'])
def edit_user():
    user_id = request.form.get('user_id')
    name = request.form.get('name')

    user = User.query.get(user_id)
    if user:
        user.name = name
        db.session.commit()
        flash(f'User {user.name} edited successfully', category='success')
    else:
        flash('User not found', category='error')

    return redirect(url_for('main.dashboard_admin'))


@main_bp.route('/delete-user', methods=['POST'])
def delete_user():
    user_id = request.form.get('user_id')

    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.name} deleted successfully', category='success')
    else:
        flash('User not found', category='error')

    return redirect(url_for('main.dashboard_admin'))
