from flask import Blueprint, render_template, session, request, flash, redirect, url_for
from datetime import datetime, timedelta
from extensions import mongo 
from auth.utils import login_required, issuer_required

audit_bp = Blueprint('audit', __name__, url_prefix='/audit')

@audit_bp.route('/logs')
@login_required
def view_logs():
    """View audit logs"""
    user_id = session['user_id']
    role = session.get('role')
    
    # Get filter parameters
    filter_type = request.args.get('filter_type', 'all')
    date_range = request.args.get('date_range', 'all')
    
    # Create filter criteria
    filter_criteria = {}
    if role == 'user':
        # Regular users can only see their own logs
        filter_criteria['user_id'] = user_id
    
    # Apply date range filter
    if date_range != 'all':
        today = datetime.now()
        if date_range == 'today':
            start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
            filter_criteria['timestamp'] = {'$gte': start_date}
        elif date_range == 'week':
            start_date = today - timedelta(days=7)
            filter_criteria['timestamp'] = {'$gte': start_date}
        elif date_range == 'month':
            start_date = today - timedelta(days=30)
            filter_criteria['timestamp'] = {'$gte': start_date}
    
    # Apply action type filter
    if filter_type != 'all':
        filter_criteria['action'] = filter_type
    
    # Get filtered logs
    logs = mongo.db.get_filtered_audit_logs(filter_criteria)
    
    # Get additional information for each log
    for log in logs:
        if 'document_id' in log:
            document = mongo.db.get_document_by_id(log['document_id'])
            if document:
                log['document_name'] = document['document_name']
    
    return render_template('audit_log.html', 
                          logs=logs, 
                          filter_type=filter_type,
                          date_range=date_range,
                          role=role)

@audit_bp.route('/export', methods=['GET'])
@login_required
def export_logs():
    """Export audit logs as CSV"""
    import csv
    from io import StringIO
    from flask import Response
    
    user_id = session['user_id']
    role = session.get('role')
    
    # Get filter parameters
    filter_type = request.args.get('filter_type', 'all')
    date_range = request.args.get('date_range', 'all')
    
    # Create filter criteria
    filter_criteria = {}
    if role == 'user':
        # Regular users can only see their own logs
        filter_criteria['user_id'] = user_id
    
    # Apply date range filter
    if date_range != 'all':
        today = datetime.now()
        if date_range == 'today':
            start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
            filter_criteria['timestamp'] = {'$gte': start_date}
        elif date_range == 'week':
            start_date = today - timedelta(days=7)
            filter_criteria['timestamp'] = {'$gte': start_date}
        elif date_range == 'month':
            start_date = today - timedelta(days=30)
            filter_criteria['timestamp'] = {'$gte': start_date}
    
    # Apply action type filter
    if filter_type != 'all':
        filter_criteria['action'] = filter_type
    
    # Get filtered logs
    logs = mongo.db.get_filtered_audit_logs(filter_criteria)
    
    # Create CSV
    output = StringIO()
    csv_writer = csv.writer(output)
    
    # Write header
    csv_writer.writerow(['Audit ID', 'User ID', 'Document ID', 'Action', 'Timestamp', 'Performed By'])
    
    # Write data
    for log in logs:
        csv_writer.writerow([
            log.get('Audit_id', ''),
            log.get('user_id', ''),
            log.get('document_id', ''),
            log.get('action', ''),
            log.get('timestamp', '').strftime('%Y-%m-%d %H:%M:%S') if log.get('timestamp') else '',
            log.get('performed_by', '')
        ])
    
    # Create response
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=audit_logs.csv'}
    )

@audit_bp.route('/document/<document_id>')
@login_required
def document_logs(document_id):
    """View logs for a specific document"""
    user_id = session['user_id']
    role = session.get('role')
    
    # Get document
    document = mongo.db.get_document_by_id(document_id)
    
    if not document:
        flash('Document not found', 'danger')
        return redirect(url_for('audit.view_logs'))
    
    # Check if user has permission to view this document's logs
    if role != 'issuer' and document['user_id'] != user_id:
        flash('You do not have permission to view these logs', 'danger')
        return redirect(url_for('audit.view_logs'))
    
    # Get logs for this document
    logs = mongo.db.get_audit_logs_by_document(document_id)
    
    return render_template('document_logs.html', 
                          logs=logs, 
                          document=document,
                          role=role)

