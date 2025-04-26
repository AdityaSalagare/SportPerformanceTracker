from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from extensions import mongo, bcrypt
from forms import LoginForm, RegistrationForm
from models import User
import logging

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.find_by_email(form.email.data)
        if user and bcrypt.check_password_hash(user['password_hash'], form.password.data):
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['email'] = user['email']
            session['role'] = user['role']

            logging.info(f"User {form.email.data} logged in successfully as {user['role']}")
            flash('Login successful!', 'success')

            if user['role'] == 'coach':
                return redirect(url_for('coach.dashboard'))
            else:
                return redirect(url_for('athlete.dashboard'))
        else:
            logging.warning(f"Failed login attempt for {form.email.data}")
            flash('Login failed. Please check your email and password.', 'danger')

    return render_template('login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.find_by_email(form.email.data)
        if existing_user:
            flash('Email already registered.', 'danger')
            return render_template('register.html', form=form)

        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        user_id = User.create_user(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password,
            role=form.role.data
        )

        logging.info(f"User {form.email.data} registered successfully with role {form.role.data}")
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)

@auth_bp.route('/logout')
def logout():
    user = session.get('username', 'Unknown')
    session.clear()
    logging.info(f"User {user} has logged out")
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))
