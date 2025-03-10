from flask import Blueprint, abort, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user, logout_user
from app import db
from app.models import Service, ServiceRequest, Professional
from datetime import datetime
from sqlalchemy.orm import joinedload

bp = Blueprint('customer', __name__, url_prefix='/customer')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'customer':
        return redirect(url_for('auth.login'))

    service_requests = (
        ServiceRequest.query
        .join(Service, ServiceRequest.service_id == Service.id)
        .filter(ServiceRequest.customer_id == current_user.id)
        .add_columns(Service.name, Service.price, Service.description, Service.time_required, ServiceRequest.status, ServiceRequest.date_requested, ServiceRequest.date_completed, ServiceRequest.remarks, ServiceRequest.id)
        .all()
    )
    professionals = (
        Professional.query
        .join(Service, Professional.service_type == Service.name)
        .add_columns(
            Professional.id, Professional.name, Professional.experience, Professional.description,
            Professional.reviews, Professional.verified, Service.name.label('service_name'),
            Service.price.label('service_price'), Service.description.label('service_description'),
            Service.time_required.label('service_time_required'), Service.image_url.label('service_image_url')
        )
        .all()
    )

    return render_template(
        'customer_dashboard.html',
        service_requests=service_requests,
        professionals=professionals
    )

@bp.route('/request_service/<int:professional_id>', methods=['GET', 'POST'])
@login_required
def request_service(professional_id):
    if current_user.role != 'customer':
        return redirect(url_for('auth.login'))

    professional = Professional.query.get_or_404(professional_id)
    service = Service.query.filter_by(name=professional.service_type).first()

    if request.method == 'POST':
        new_request = ServiceRequest(
            service_id=service.id,
            customer_id=current_user.id,
            professional_id=professional_id,
            date_requested=datetime.utcnow(),
            status='Pending'
        )
        db.session.add(new_request)
        db.session.commit()

        return redirect(url_for('customer.dashboard'))

    return render_template('request_service.html', service=service)

# Cancel a service request
@bp.route('/cancel_request/<int:request_id>')
@login_required
def cancel_request(request_id):
    request = ServiceRequest.query.get_or_404(request_id)
    if request.customer_id != current_user.id or request.status != 'Pending':
        abort(403)
    db.session.delete(request)
    db.session.commit()
    flash('Service request cancelled successfully.', 'success')
    return redirect(url_for('customer.dashboard'))

# Close a service request
@bp.route('/close_request/<int:request_id>')
@login_required
def close_request(request_id):
    request = ServiceRequest.query.get_or_404(request_id)
    if request.customer_id != current_user.id or request.status != 'accepted':
        abort(403)
    request.status = 'closed'
    request.date_completed = datetime.utcnow()
    db.session.commit()
    flash('Service request closed successfully.', 'success')
    return redirect(url_for('customer.payment   '))

@bp.route('/payment', methods=['GET', 'POST'])
@login_required
def payment():
    if request.method == 'POST':
        flash('Payment successful!', 'success')
        return redirect(url_for('customer.dashboard'))

    return render_template('payment.html')

# Post a review
@bp.route('/post_review/<int:request_id>', methods=['GET', 'POST'])
@login_required
def post_review(request_id):
    s_request = ServiceRequest.query.options(joinedload(ServiceRequest.service)) \
        .filter(ServiceRequest.id == request_id).first()
    if s_request.customer_id != current_user.id or s_request.status != 'closed':
        abort(403)

    if request.method == 'POST':
        review = request.form['review']
        remarks = request.form['remarks']
        professional = Professional.query.get(s_request.professional_id)
        all_requests = ServiceRequest.query.filter(ServiceRequest.professional_id == s_request.professional_id, ServiceRequest.status == 'closed').all()
        prev_review = professional.reviews
        total_reviews = len(all_requests)
        new_review = (prev_review * (total_reviews - 1) + int(review)) / total_reviews
        professional.reviews = new_review
        s_request.remarks = remarks
        db.session.commit()
        flash('Review submitted successfully.', 'success')
        return redirect(url_for('customer.dashboard'))

    return render_template('post_review.html', s_request=s_request)


# Search services
@bp.route('/search_services', methods=['GET'])
def search_services():
    service_name = request.args.get('service_name')
    query = Service.query

    professionals = (
        Professional.query
        .join(Service, Professional.service_type.like(f'%{service_name}%'))
        .add_columns(
            Professional.id, Professional.name, Professional.experience, Professional.description,
            Professional.reviews, Professional.verified, Service.name.label('service_name'),
            Service.price.label('service_price'), Service.description.label('service_description'),
            Service.time_required.label('service_time_required')
        )
        .all()
    )

    services = query.all()
    return render_template('customer_dashboard.html', professionals=professionals)
