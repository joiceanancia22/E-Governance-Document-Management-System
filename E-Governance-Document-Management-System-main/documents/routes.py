from flask import Blueprint, request, render_template, redirect, url_for, flash, send_file, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
import os
import datetime
from extensions import mongo 
from documents.forms import UploadDocumentForm
from id_generator_utils import generate_document_id
from audit.audit_logger_utils import log_action

documents_bp = Blueprint('documents', __name__, template_folder='templates')

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@documents_bp.route('/')
@login_required
def dashboard():
    """Dashboard showing all documents"""
    try:
        if current_user.user_type == 'user':
            documents = list(mongo.__getattribute__db.documents.find({'user_id': ObjectId(current_user.get_id())}))
            users = None
        else:
            documents = list(mongo.db.documents.find())
            users = {str(u['_id']): u['name'] for u in mongo.db.users.find()}
        
        return render_template('dashboard.html', 
                            documents=documents,
                            users=users,
                            user_type=current_user.user_type)
    
    except Exception as e:
        current_app.logger.error(f"Error loading dashboard: {str(e)}", exc_info=True)
        flash('Error loading dashboard', 'danger')
        return redirect(url_for('main.index'))

@documents_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadDocumentForm()

    print("\n=== UPLOAD DEBUG ===")
    print("Form submitted:", request.method)
    print("Form valid:", form.validate_on_submit())
    print("Form errors:", form.errors)
    print("Files received:", request.files)

    # Populate user choices if current user is an issuer
    if current_user.user_type == 'issuer':
        users = mongo.db.users.find({}, {'_id': 1, 'name': 1, 'email': 1})
        form.selected_user.choices = [
            (str(user['_id']), f"{user['name']} ({user['email']})") 
            for user in users
        ]
        form.selected_user.choices.insert(0, ('', 'Select a user...'))

    if form.validate_on_submit():
        try:
            if 'file' not in request.files or not form.file.data:
                flash('No file part', 'error')
                return redirect(request.url)

            file = form.file.data

            if file.filename == '':
                flash('No selected file', 'error')
                return redirect(request.url)

            document_name = form.document_name.data
            document_type = form.document_type.data

            document_id = generate_document_id(current_user.get_id(), document_type)
            filename = secure_filename(f"{document_id}_{file.filename}")

            # Build upload path
            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)

            # Prepare base document data
            new_document = {
                '_id': document_id,
                'user_id': ObjectId(current_user.get_id()),
                'document_name': document_name,
                'document_type': document_type,
                'file_name': filename,
                'file_path': file_path,
                'file_size': os.path.getsize(file_path),
                'file_type': os.path.splitext(file.filename)[1][1:].upper(),
                'uploaded_at': datetime.utcnow(),
                'status': 'pending'
            }

            # If issuer, assign additional metadata
            if current_user.user_type == 'issuer':
                selected_user_id = form.selected_user.data
                if not selected_user_id:
                    flash('Please select a user to assign the document to.', 'error')
                    return redirect(request.url)

                expiry_date = (
                    form.expiry_date.data
                    if form.validity_type.data == 'temporary'
                    else None
                )

                new_document.update({
                    'user_id': ObjectId(selected_user_id),
                    'issuer_id': ObjectId(current_user.get_id()),
                    'status': 'approved',
                    'approval': {
                        'status': 'Approved',
                        'approved_by': ObjectId(current_user.get_id()),
                        'approval_date': datetime.utcnow(),
                        'validity_type': form.validity_type.data,
                        'expiry_date': expiry_date,
                        'renewal_required': form.renewal_required.data == 'true'
                    }
                })

            # Save to DB
            mongo.db.documents.insert_one(new_document)

            # Log the action
            log_action(
                user_id=ObjectId(current_user.get_id()),
                document_id=document_id,
                action="Uploaded",
                performed_by=current_user.user_type.capitalize(),
                details=f"Document '{document_name}' uploaded"
            )

            flash('Document uploaded successfully!', 'success')
            return redirect(url_for('documents.view', document_id=document_id))

        except Exception as e:
            current_app.logger.error(f"Document upload failed: {str(e)}", exc_info=True)
            flash('An error occurred during document upload.', 'danger')

    return render_template(
        'upload_document.html',
        form=form,
        allowed_extensions=current_app.config['ALLOWED_EXTENSIONS'],
        max_file_size=current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
    )

@documents_bp.route('/view/<document_id>')
@login_required
def view(document_id):
    """View document details"""
    try:
        document = mongo.db.documents.find_one({'_id': ObjectId(document_id)})
        if not document:
            flash('Document not found', 'danger')
            return redirect(url_for('documents.dashboard'))
        
        # Authorization check
        if (current_user.user_type == 'user' and 
            str(document['user_id']) != current_user.get_id()):
            abort(403)
        
        # Get related data
        issuer = None
        if document.get('issuer_id'):
            issuer = mongo.db.users.find_one({'_id': document['issuer_id']})
        
        audit_logs = list(mongo.db.audit_logs.find({'document_id': document_id})
                         .sort('timestamp', -1)
                         .limit(10))
        
        # Check expiry status
        document['is_expired'] = False
        document['is_expiring'] = False
        
        if document.get('approval', {}).get('expiry_date'):
            expiry_date = document['approval']['expiry_date']
            today = datetime.datetime.utcnow()
            if expiry_date < today:
                document['is_expired'] = True
            elif (expiry_date - today).days <= 7:
                document['is_expiring'] = True
        
        # Log view action
        log_action(
            user_id=ObjectId(current_user.get_id()),
            document_id=document_id,
            action="Viewed",
            performed_by=current_user.user_type.capitalize()
        )
        
        return render_template('view_document.html', 
                            document=document, 
                            issuer=issuer, 
                            audit_logs=audit_logs)
    
    except Exception as e:
        current_app.logger.error(f"Error viewing document {document_id}: {str(e)}", exc_info=True)
        flash('Error loading document', 'danger')
        return redirect(url_for('documents.dashboard'))

@documents_bp.route('/download/<document_id>')
@login_required
def download(document_id):
    """Download document file"""
    try:
        document = mongo.db.documents.find_one({'_id': ObjectId(document_id)})
        if not document:
            flash('Document not found', 'danger')
            return redirect(url_for('documents.dashboard'))
        
        # Authorization check
        if (current_user.user_type == 'user' and 
            str(document['user_id']) != current_user.get_id()):
            abort(403)
        
        # Verify file exists
        if not os.path.exists(document['file_path']):
            current_app.logger.error(f"File not found at {document['file_path']}")
            flash('File not found', 'danger')
            return redirect(url_for('documents.view', document_id=document_id))
        
        # Log download action
        log_action(
            user_id=ObjectId(current_user.get_id()),
            document_id=document_id,
            action="Downloaded",
            performed_by=current_user.user_type.capitalize()
        )
        
        return send_file(
            document['file_path'],
            as_attachment=True,
            download_name=f"{secure_filename(document['document_name'])}.{document['file_type'].lower()}"
        )
    
    except Exception as e:
        current_app.logger.error(f"Error downloading document {document_id}: {str(e)}", exc_info=True)
        flash('Error downloading document', 'danger')
        return redirect(url_for('documents.view', document_id=document_id))

@documents_bp.route('/edit/<document_id>', methods=['GET', 'POST'])
@login_required
def edit(document_id):
    """Edit document details"""
    document = mongo.db.documents.find_one({'_id': ObjectId(document_id)})
    if not document:
        flash('Document not found', 'danger')
        return redirect(url_for('documents.dashboard'))

    # Authorization check
    if (current_user.user_type == 'user' and 
        str(document['user_id']) != current_user.get_id()):
        abort(403)

    if request.method == 'POST':
        try:
            # Process form data
            document_name = request.form['document_name']
            document_type = request.form['document_type']
            new_file = request.files.get('new_file')

            # Update document fields
            update_data = {
                'document_name': document_name,
                'document_type': document_type,
            }

            # Handle file replacement
            if new_file and allowed_file(new_file.filename):
                filename = secure_filename(new_file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                new_file.save(file_path)
                update_data['file_name'] = filename
                update_data['file_path'] = file_path
                update_data['file_size'] = os.path.getsize(file_path)

            # Update approval information if needed
            approval_status = request.form['approval_status']
            if approval_status:
                update_data['approval'] = {
                    'status': approval_status,
                    'approved_by': request.form['approved_by'],
                    'validity_type': request.form['validity_type'],
                    'expiry_date': request.form.get('expiry_date'),
                    'renewal_required': 'renewal_required' in request.form
                }

            # Update the document in the database
            mongo.db.documents.update_one({'_id': ObjectId(document_id)}, {'$set': update_data})

            flash('Document updated successfully!', 'success')
            return redirect(url_for('documents.view', document_id=document_id))

        except Exception as e:
            current_app.logger.error(f"Error updating document {document_id}: {str(e)}", exc_info=True)
            flash('An error occurred while updating the document', 'danger')

    return render_template('edit_document.html', document=document)

@documents_bp.route('/delete/<document_id>', methods=['POST'])
@login_required
def delete(document_id):
    """Delete a document and its associated file"""
    try:
        document = mongo.db.documents.find_one({'_id': ObjectId(document_id)})
        
        if not document:
            flash('Document not found', 'danger')
            return redirect(url_for('documents.dashboard'))
        
        # Authorization check
        if (current_user.user_type == 'user' and 
            str(document['user_id']) != current_user.get_id()):
            abort(403)
        
        # Delete the document from database
        mongo.db.documents.delete_one({'_id': ObjectId(document_id)})
        
        # Delete the associated file
        try:
            if os.path.exists(document['file_path']):
                os.remove(document['file_path'])
        except OSError as e:
            current_app.logger.error(f"Error deleting file {document['file_path']}: {str(e)}")
            # Continue even if file deletion fails
        
        # Log the deletion action
        log_action(
            user_id=ObjectId(current_user.get_id()),
            document_id=document_id,
            action="Deleted",
            performed_by=current_user.user_type.capitalize(),
            details=f"Document '{document.get('document_name', 'unnamed')}' deleted"
        )
        
        flash('Document deleted successfully', 'success')
        return redirect(url_for('documents.dashboard'))
    
    except Exception as e:
        current_app.logger.error(f"Error deleting document {document_id}: {str(e)}", exc_info=True)
        flash('An error occurred while deleting the document', 'danger')
        return redirect(url_for('documents.view', document_id=document_id))