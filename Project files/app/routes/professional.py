from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user, logout_user
from app import db
from app.models import Professional, ServiceRequest, Service, User

bp = Blueprint('professional', __name__, url_prefix='/professional')

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'professional':
        return redirect('auth.login')

    professional_entry = Professional.query.filter_by(user_id=current_user.id).first()
    if not professional_entry.verified:
        return render_template('professional_pending.html')

    new_requests = (
        ServiceRequest.query
        .join(Service, ServiceRequest.service_id == Service.id)
        .join(User, ServiceRequest.customer_id == User.id)
        .filter(ServiceRequest.professional_id == professional_entry.id, ServiceRequest.status == 'Pending')
        .add_columns(
            ServiceRequest.id, ServiceRequest.date_requested, ServiceRequest.remarks,
            Service.name.label('service_name'), Service.price.label('service_price'), Service.description.label('service_description'),
            User.id.label('customer_id'), User.username.label('customer_name'),
        )
        .all()
    )
    # fetch both in same above style
    old_services = (
        ServiceRequest.query
        .join(Service, ServiceRequest.service_id == Service.id)
        .join(User, ServiceRequest.customer_id == User.id)
        .filter(ServiceRequest.professional_id == professional_entry.id, ServiceRequest.status == 'closed')
        .add_columns(
            ServiceRequest.id, ServiceRequest.date_requested, ServiceRequest.remarks, ServiceRequest.date_completed,
            Service.name.label('service_name'), Service.price.label('service_price'), Service.description.label('service_description'),
            User.id.label('customer_id'), User.username.label('customer_name'),
        )
        .all()
    )

    accepted_requests = (
        ServiceRequest.query
        .join(Service, ServiceRequest.service_id == Service.id)
        .join(User, ServiceRequest.customer_id == User.id)
        .filter(ServiceRequest.professional_id == professional_entry.id, ServiceRequest.status == 'accepted')
        .add_columns(
            ServiceRequest.id, ServiceRequest.date_requested, ServiceRequest.remarks, ServiceRequest.date_completed,
            Service.name.label('service_name'), Service.price.label('service_price'), Service.description.label('service_description'),
            User.id.label('customer_id'), User.username.label('customer_name'),
        )
        .all()
    )

    return render_template(
        'professional_dashboard.html',
        new_requests=new_requests,
        old_services=old_services,
        professional=professional_entry,
        accepted_requests=accepted_requests
    )

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('auth.login')

@bp.route('/pending')
@login_required
def pending_requests():
    if current_user.role != 'professional':
        return redirect('/')

    professional_entry = Professional.query.filter_by(user_id=current_user.id).first()
    if not professional_entry.verified:
        return render_template('professional_pending.html')

    return render_template('professional_pending.html', current_user=current_user)

@bp.route('/accept-request/<int:request_id>')
@login_required
def accept_request(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    service_request.status = 'accepted'
    db.session.commit()
    flash('Service request accepted.', 'success')
    return redirect(url_for('professional.dashboard'))

@bp.route('/reject-request/<int:request_id>')
@login_required
def reject_request(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    service_request.status = 'rejected'
    db.session.commit()
    flash('Service request rejected.', 'success')
    return redirect(url_for('professional.dashboard'))