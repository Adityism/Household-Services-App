from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import login_required, current_user
import os
from app import db
from app.models import Service, User, Professional

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        print(email, password, os.getenv('ADMIN_EMAIL'), os.getenv('ADMIN_PASSWORD'))
        if email == os.getenv('ADMIN_EMAIL') and password == os.getenv('ADMIN_PASSWORD'):
            session['admin_logged_in'] = True
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid credentials', 'danger')

    return render_template('admin_login.html')

@bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin.login'))


def filter_role(user):
    if user.role == 'professional':
        return True
    return False

@bp.route('/dashboard')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))

    users = User.query.all()
    services = Service.query.all()
    professionals = Professional.query.filter_by(verified=False).all()

    professionals_count = list(filter(filter_role, users))
    users_count = len(users) - len(professionals_count)

    stats = {
        'users': users_count,
        'services': len(services),
        'professionals': len(professionals_count)
    }

    return render_template('admin_dashboard.html', users=users, services=services, professionals=professionals, stats=stats)

# Block User
@bp.route('/block_user/<int:user_id>')
def block_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.is_active = not user.is_active
        db.session.commit()
        flash('User status updated successfully!', 'success')
    return redirect(url_for('admin.dashboard'))

# Delete User
@bp.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.dashboard'))

# Edit Service
@bp.route('/edit_service/<int:service_id>', methods=['GET', 'POST'])
def edit_service(service_id):
    service = Service.query.get(service_id)
    if not service:
        flash('Service not found!', 'danger')
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        service.name = request.form['name']
        service.price = request.form['price']
        service.description = request.form['description']
        db.session.commit()
        flash('Service updated successfully!', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('edit_service.html', service=service)

# Delete Service
@bp.route('/delete_service/<int:service_id>')
def delete_service(service_id):
    service = Service.query.get(service_id)
    if service:
        db.session.delete(service)
        db.session.commit()
        flash('Service deleted successfully!', 'success')
    return redirect(url_for('admin.dashboard'))

@bp.route('/create_service', methods=['GET', 'POST'])
def create_service():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))

    if request.method == 'POST':
        from app.models import Service
        name = request.form.get('name')
        base_price = request.form.get('base_price')
        description = request.form.get('description')
        image_url = request.form.get('image_url')
        new_service = Service(name=name, price=base_price, description=description, image_url=image_url)
        db.session.add(new_service)
        db.session.commit()
        flash('Service created successfully', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('create_service.html')


@bp.route('/approve/<int:id>')
def approve_professional(id):
    print(current_user)
    if not session.get('admin_logged_in'):
        return redirect('/')

    professional = Professional.query.get_or_404(id)
    professional.verified = True
    db.session.commit()
    flash("Professional approved successfully.", "success")
    return redirect(url_for('admin.dashboard'))

@bp.route('/reject/<int:id>')
def reject_professional(id):
    if not session.get('admin_logged_in'):
        return redirect('/')

    professional = Professional.query.get_or_404(id)
    user = User.query.get(professional.user_id)
    db.session.delete(professional)
    db.session.delete(user)
    db.session.commit()
    flash("Professional rejected successfully.", "success")
    return redirect(url_for('admin.dashboard'))
