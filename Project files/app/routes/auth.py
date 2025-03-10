from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from app.models import User, Professional, Service

auth = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Login Route
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return redirect(url_for('auth.login'))

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            if not user.is_active:
                flash("Your account is inactive. Contact Admin.", "danger")
                return redirect(url_for('auth.login'))
            login_user(user)
            flash("Logged in successfully!", "success")
            if user.role == 'professional':
                print("here")
                return redirect(url_for('professional.dashboard'))
            return redirect(url_for('customer.dashboard'))
        else:
            flash("Invalid username or password.", "danger")
    return render_template('login.html')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        if role not in ['professional', 'customer']:
            flash("Invalid role selected.", "danger")
            return redirect(url_for('auth.register'))

        user = User.query.filter_by(username=username).first()
        if user:
            flash("Username already exists. Choose another.", "danger")
            return redirect(url_for('auth.register'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()

        if role == 'professional':
            name = request.form['name']
            description = request.form['description']
            experience = int(request.form['experience'])
            service_type = request.form['service_type']

            new_professional = Professional(
                user_id=new_user.id,
                name=name,
                service_type=service_type,
                experience=experience,
                description=description
            )
            db.session.add(new_professional)
            db.session.commit()

            flash("Registered successfully! Awaiting admin approval.", "info")
            return redirect(url_for('auth.login'))

        flash("Registered successfully! You can now log in.", "success")
        return redirect(url_for('auth.login'))

    service_types = [service.name for service in Service.query.all()]
    return render_template('register.html', service_types=service_types)

# Logout Route
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for('auth.login'))
