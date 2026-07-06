import sys
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, send_file
from flask_pymongo import PyMongo
from functools import wraps
import os
from datetime import datetime, timedelta
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid
from flask_login import login_user, logout_user, current_user, login_required, LoginManager
from bson.objectid import ObjectId
from documents.forms import UploadDocumentForm
from extensions import mongo 
from documents.routes import documents_bp

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(16))
# Initialize the LoginManager
login_manager = LoginManager()
login_manager.init_app(app)

# Set the login_view to the name of your login route
login_manager.login_view = 'login'
# File Upload Configuration
UPLOAD_FOLDER = r'C:\Users\Moogambigai_M.Tech\project\uploads'  # Use raw string to avoid escape issues
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_user(user_id):
    return mongo.db.users.find_one({"_id": ObjectId(user_id)})
# Register the blueprint with proper template folder

app.register_blueprint(documents_bp, url_prefix='/documents')

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/e_governance_dms"
mongo.init_app(app)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xls', 'xlsx'}
@login_manager.user_loader
def load_user(user_id):
    return mongo.db.users.find_one({"_id": ObjectId(user_id)})
# Helper Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Custom filter to format datetime
@app.template_filter('format_datetime')
def format_datetime(value):
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')  # Customize the format as needed
    return value
@app.template_filter('to_objectid')
def to_objectid(value):
    """Convert a string to an ObjectId."""
    try:
        return ObjectId(value)
    except Exception:
        return None  
# ID Generation Functions
def generate_user_id():
    # Count the number of users in the collection
    user_count = mongo.db.users.count_documents({})
    new_id = user_count + 101  # Start from U101
    return f'U{new_id}'

def generate_issuer_id():
    # Count the number of issuers in the collection
    issuer_count = mongo.db.issuers.count_documents({})
    new_id = issuer_count + 101  # Start from I101
    return f'I{new_id}'

def generate_doc_id():
    # Count the number of documents in the collection
    document_count = mongo.db.documents.count_documents({})
    new_id = document_count + 101  # Start from D101
    return f'D{new_id}'
# Authentication Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def issuer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session or session['user_type'] != 'issuer':
            flash('Access denied. Issuer privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# User Authentication Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type')
        
        if user_type == 'user':
            user = mongo.db.users.find_one({'email': email})
        else:
            user = mongo.db.issuers.find_one({'email': email})
            
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['user_type'] = user_type
            session['name'] = user['name'] if user_type == 'user' else user['issuer_name']  # Removed extra space
            
            # Log the login activity
            log_data = {
                "user_id": str(user['_id']),
                "action": "Login",
                "timestamp": datetime.now(),
                "performed_by": user_type.capitalize(),
                "details": f"{user_type.capitalize()} logged in"
            }
            mongo.db.audit_logs.insert_one(log_data)
            
            flash(f'Welcome back, {session["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_type = request.form.get('user_type')
        
        if user_type == 'user':
            email = request.form.get('email')
            new_user_id = generate_user_id()
            password = request.form.get('password')
            hashed_password = generate_password_hash(password)
            name = request.form.get('name')
            
            existing_user = mongo.db.users.find_one({'email': email})
            if existing_user:
                flash('Email already registered', 'danger')
                return redirect(url_for('register'))
            
            mongo.db.users.insert_one({
                'user_id': new_user_id,
                'email': email,
                'password': hashed_password,
                'name': name
            })
            flash('User  registered successfully', 'success')
            return redirect(url_for('login'))
        
        elif user_type == 'issuer':
            email = request.form.get('email')
            new_issuer_id = generate_issuer_id()
            password = request.form.get('password')
            hashed_password = generate_password_hash(password)
            issuer_name = request.form.get('issuer_name')
            
            existing_issuer = mongo.db.issuers.find_one({'email': email})
            if existing_issuer:
                flash('Email already registered', 'danger')
                return redirect(url_for('register'))
            
            mongo.db.issuers.insert_one({
                'issuer_id': new_issuer_id,
                'email': email,
                'password': hashed_password,
                'issuer_name': issuer_name
            })
            flash('Issuer registered successfully', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_document():
    form = UploadDocumentForm()
    print("Form created")  # Debug
    
    if form.validate_on_submit():
        print("Form validated")  # Debug
        file = form.file.data
        print(f"File received: {file.filename}")  # Debug
        
        if file and allowed_file(file.filename):
            print("File allowed")  # Debug
            try:
                doc_id = generate_doc_id()
                original_filename = secure_filename(file.filename)
                unique_filename = f"{doc_id}_{original_filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                print(f"Saving to: {file_path}")
                file.save(file_path)
                print("File saved successfully")
                mongo.db.documents.insert_one({
                    'doc_id': doc_id,
                    'filename': unique_filename,
                    'original_filename': original_filename,
                    'file_path': file_path,
                    'uploaded_by': session['user_id'],
                    'uploaded_at': datetime.now(),
                    'file_size': os.path.getsize(file_path),
                    'file_type': file.content_type
                })
                
                flash('Document uploaded successfully', 'success')
                return redirect(url_for('dashboard'))
                
            except Exception as e:
                flash(f'Error uploading file: {str(e)}', 'danger')
                app.logger.error(f"Upload error: {str(e)}")
                return redirect(request.url)
        else:
            flash('Invalid file type', 'danger')
    
    return render_template('upload_document.html', form=form)
@app.route('/search_document', methods=['GET', 'POST'])
@login_required
def search_document():
    if request.method == 'POST':
        doc_id = request.form.get('doc_id')
        user_id = request.form.get('user_id')
        issuer_id = request.form.get('issuer_id')
        
        query = {}
        if doc_id:
            query['doc_id'] = doc_id
        if user_id:
            query['uploaded_by'] = user_id
        if issuer_id:
            query['issuer_id'] = issuer_id
        
        documents = mongo.db.documents.find(query)
        return render_template('search_results.html', documents=documents)
    
    return render_template('search_document.html')

# Dashboard Routes
@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    user_type = session['user_type']
    
    if user_type == 'user':
        # Get user's documents
        documents = list(mongo.db.documents.find({'uploaded_by': user_id}))
        
        # Check for soon-to-expire documents
        expiring_docs = []
        for doc in documents:
            if 'approval' in doc and doc['approval'].get('expiry_date'):
                expiry_date = doc['approval']['expiry_date']
                if isinstance(expiry_date, str):
                    expiry_date = datetime.strptime(expiry_date, "%Y-%m-%dT%H:%M:%SZ")
                days_to_expiry = (expiry_date - datetime.now()).days
                if 0 < days_to_expiry <= 30:
                    doc['days_to_expiry'] = days_to_expiry
                    expiring_docs.append(doc)
        
        return render_template('dashboard.html', 
                              documents=documents, 
                              expiring_docs=expiring_docs,
                              user_type=user_type)
    else:
        # For issuers, show all documents
        documents = list(mongo.db.documents.find())
        users = {u['_id']: u['name'] for u in mongo.db.users.find()}
        
        return render_template('dashboard.html', 
                              documents=documents, 
                              users=users,
                              user_type=user_type)

@app.route('/documents/view/<document_id>')
def view_document(document_id):
    document = mongo.db.documents.find_one({"_id": ObjectId(document_id)})
    
    # Check if the document exists
    if not document:
        flash('Document not found', 'danger')
        return redirect(url_for('dashboard'))
    
    user_type = session['user_type']
    user_id = session['user_id']
    
    # Check authorization: only the owner or issuer can view the document
    if user_type == 'user' and document['uploaded_by'] != user_id:
        flash('You are not authorized to view this document', 'danger')
        return redirect(url_for('dashboard'))
    
    # Create audit log for viewing the document
    log_data = {
        "user_id": user_id,
        "document_id": document_id,
        "action": "View",
        "timestamp": datetime.now(),
        "performed_by": user_type.capitalize(),
        "details": f"Document '{document.get('document_name', 'Unknown Document')}' viewed"
    }
    mongo.db.audit_logs.insert_one(log_data)
    
    return render_template('document_detail.html', document=document)

@app.route('/document/<document_id>/download')
def download_document(document_id):
    doc = mongo.db.documents.find_one({'_id': ObjectId(document_id)})
    if not doc:
        flash("Document not found", "danger")
        return redirect(url_for('dashboard'))

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc['filename'])
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash("File not found on server", "danger")
        return redirect(url_for('dashboard'))

@app.route('/documents/edit/<document_id>', methods=['GET', 'POST'])
@login_required
@issuer_required
def edit_document(document_id):
    document = mongo.db.documents.find_one({"_id": ObjectId(document_id)})
    
    if not document:
        flash('Document not found', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Update document details
        update_data = {
            "document_name": request.form.get('document_name'),
            "document_type": request.form.get('document_type')
        }
        
        # Update approval information
        validity_type = request.form.get('validity_type')
        expiry_date = None
        renewal_required = False
        
        if validity_type == 'temporary':
            expiry_date_str = request.form.get('expiry_date')
            if expiry_date_str:
                expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
            renewal_required = request.form.get('renewal_required') == 'yes'
        
        approval_update = {
            "approval.validity_type": validity_type,
            "approval.expiry_date": expiry_date,
            "approval.renewal_required": renewal_required
        }
        
        update_data.update(approval_update)
        
        # Update the document
        mongo.db.documents.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": update_data}
        )
        
        # Create audit log
        log_data = {
            "user_id": session['user_id'],
            "document_id": document_id,
            "action": "Edit",
            "timestamp": datetime.now(),
            "performed_by": "Issuer",
            "details": f"Document '{document['document_name']}' edited"
        }
        mongo.db.audit_logs.insert_one(log_data)
        
        flash('Document updated successfully', 'success')
        return redirect(url_for('view_document', document_id=document_id))
    
    return render_template('edit_document.html', document=document)

@app.route('/document/<document_id>/delete', methods=['POST'])
def delete_document(document_id):
    doc = mongo.db.documents.find_one({'_id': ObjectId(document_id)})
    if doc:
        mongo.db.documents.delete_one({'_id': ObjectId(document_id)})
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)
        flash("Document deleted successfully", "success")
    else:
        flash("Document not found", "danger")
    return redirect(url_for('dashboard'))

# Audit Log Routes
@app.route('/audit-logs')
@login_required
def audit_logs():
    user_id = session['user_id']
    user_type = session['user_type']
    
    # Filter options
    filter_type = request.args.get('filter_type', 'all')
    filter_date = request.args.get('filter_date', 'all')
    filter_user = request.args.get('filter_user', 'all')
    
    # Base query
    query = {}
    
    # Apply filtering
    if user_type == 'user':
        # Users can only see their own logs
        query['user_id'] = user_id
    elif user_type == 'issuer':
        # Issuers can see all logs, but can filter by user
        if filter_user != 'all':
            query['user_id'] = filter_user
    
    # Apply action type filter
    if filter_type != 'all':
        query['action'] = filter_type
    
    # Apply date filter
    if filter_date != 'all':
        today = datetime.now()
        if filter_date == 'today':
            start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
            query['timestamp'] = {'$gte': start_date}
        elif filter_date == 'week':
            start_date = today - timedelta(days=7)
            query['timestamp'] = {'$gte': start_date}
        elif filter_date == 'month':
            start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            query['timestamp'] = {'$gte': start_date}
    
    # Get logs with pagination
    page = int(request.args.get('page', 1))
    per_page = 20
    skip = (page - 1) * per_page
    
    logs = list(mongo.db.audit_logs.find(query).sort('timestamp', -1).skip(skip).limit(per_page))
    total_logs = mongo.db.audit_logs.count_documents(query)
    
    # Get user info for issuer view
    users = None
    if user_type == 'issuer':
        users = list(mongo.db.users.find())
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total_logs,
        'pages': (total_logs + per_page - 1) // per_page
    }
    
    return render_template('audit_logs.html', 
                          logs=logs, 
                          users=users, 
                          pagination=pagination,
                          filter_type=filter_type,
                          filter_date=filter_date,
                          filter_user=filter_user)

# Expiry notification checker (to be called via scheduler)
def check_expiring_documents():
    # Find documents expiring in the next 7 days
    current_date = datetime.now()
    expiry_date = current_date + timedelta(days=7)
    
    query = {
        "approval.expiry_date": {
            "$gte": current_date,
            "$lte": expiry_date
        }
    }
    
    expiring_docs = list(mongo.db.documents.find(query))
    
    for doc in expiring_docs:
        user_id = doc['user_id']
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        
        if user:
            # In a real application, send email/SMS here
            print(f"Notification for {user['name']}: Your document '{doc['document_name']}' is expiring soon!")
            
            # Log the notification
            log_data = {
                "user_id": user_id,
                "document_id": str(doc['_id']),
                "action": "Expiry Notification",
                "timestamp": datetime.now(),
                "performed_by": "System",
                "details": f"Expiry notification sent for document '{doc['document_name']}'"
            }
            mongo.db.audit_logs.insert_one(log_data)
@app.route('/logout')
def logout():
    if 'user_id' in session:
        # Log the logout activity
        log_data = {
            "user_id": session['user_id'],
            "action": "Logout",
            "timestamp": datetime.now(),
            "performed_by": session['user_type'].capitalize(),
            "details": f"{session['user_type'].capitalize()} logged out"
        }
        mongo.db.audit_logs.insert_one(log_data)
    
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5050)

