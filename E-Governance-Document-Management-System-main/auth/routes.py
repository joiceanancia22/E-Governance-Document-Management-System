from flask import Blueprint, request, render_template, redirect, url_for, session, flash
import bcrypt
from datetime import datetime
from extensions import mongo 
from .utils import validate_registration, validate_login
from id_generator_utils import generate_user_id, generate_issuer_id

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Unified registration route for both users and issuers"""
    if request.method == 'POST':
        user_type = request.form.get('user_type')
        
        # Gather form data
        form_data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'password': request.form.get('password'),
            'confirm_password': request.form.get('confirm_password')
        }
        
        # Add user-specific or issuer-specific fields
        if user_type == 'user':
            form_data.update({
                'address': request.form.get('address'),
                'contact_number': request.form.get('contact_number'),
                'aadhaar_number': request.form.get('aadhaar_number'),
                'date_of_birth': request.form.get('date_of_birth'),
                'gender': request.form.get('gender'),
                'nationality': request.form.get('nationality')
            })
        else:  # issuer
            form_data.update({
                'issuer_name': request.form.get('issuer_name'),
                'issuer_type': request.form.get('issuer_type'),
                'address': request.form.get('address')
            })
            
        # Validate form data
        errors = validate_registration(form_data, user_type)
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html', data=form_data)
        
        # Check if email already exists
        if user_type == 'user':
            existing_user = mongo.db.users.find_one({'email': form_data['email']})
            if existing_user:
                flash('Email already registered. Please log in.', 'danger')
                return render_template('register.html', data=form_data)
        else:
            existing_issuer = mongo.db.issuers.find_one({'email': form_data['email']})
            if existing_issuer:
                flash('Email already registered. Please log in.', 'danger')
                return render_template('register.html', data=form_data)
        
        # Hash password
        hashed_password = bcrypt.hashpw(form_data['password'].encode('utf-8'), bcrypt.gensalt())
        
        # Create user or issuer
        if user_type == 'user':
            # Generate User_id using the new generator
            user_id = generate_user_id()
            
            user_data = {
                'User_id': user_id,
                'name': form_data['name'],
                'email': form_data['email'],
                'password': hashed_password.decode('utf-8'),
                'address': form_data['address'],
                'contact_number': form_data['contact_number'],
                'aadhaar_number': form_data['aadhaar_number'],
                'date_of_birth': form_data['date_of_birth'],
                'gender': form_data['gender'],
                'nationality': form_data['nationality'],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            mongo.db.users.insert_one(user_data)
            flash(f'User registration successful! Your User ID is: {user_id}', 'success')
        else:
            # Generate Issuer_id using the new generator
            issuer_id = generate_issuer_id(form_data['issuer_type'])
            
            issuer_data = {
                'Issuer_id': issuer_id,
                'issuer_name': form_data['issuer_name'],
                'issuer_type': form_data['issuer_type'],
                'email': form_data['email'],
                'password': hashed_password.decode('utf-8'),
                'address': form_data['address'],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            mongo.db.issuers.insert_one(issuer_data)
            flash(f'Issuer registration successful! Your Issuer ID is: {issuer_id}', 'success')
            
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type')
        
        # Validate login
        errors = validate_login(email, password)
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('login.html')
        
        # Check if user exists
        if user_type == 'user':
            user = mongo.db.users.find_one({'email': email})
            if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                flash('Invalid email or password', 'danger')
                return render_template('login.html')
                
            # Set session
            session['user_id'] = str(user['_id'])
            session['user_name'] = user['name']
            session['role'] = 'user'
            session['user_identifier'] = user['User_id']
            
            # Create audit log for login
            log_data = {
                'user_id': str(user['_id']),
                'action': 'Login',
                'performed_by': 'User',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            mongo.db.audit_logs.insert_one(log_data)
            
        else:  # issuer
            issuer = mongo.db.issuers.find_one({'email': email})
            if not issuer or not bcrypt.checkpw(password.encode('utf-8'), issuer['password'].encode('utf-8')):
                flash('Invalid email or password', 'danger')
                return render_template('login.html')
                
            # Set session
            session['user_id'] = str(issuer['_id'])
            session['user_name'] = issuer['issuer_name']
            session['role'] = 'issuer'
            session['user_identifier'] = issuer['Issuer_id']
            
            # Create audit log for login
            log_data = {
                'user_id': str(issuer['_id']),
                'action': 'Login',
                'performed_by': 'Issuer',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            mongo.db.audit_logs.insert_one(log_data)
        
        flash(f'Welcome back, {session["user_name"]}!', 'success')
        return redirect(url_for('documents.dashboard'))
        
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """User logout route"""
    # Create audit log for logout
    if 'user_id' in session:
        log_data = {
            'user_id': session['user_id'],
            'action': 'Logout',
            'performed_by': session['role'].capitalize(),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        mongo.db.audit_logs.insert_one(log_data)
    
    # Clear session
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register/user', methods=['GET', 'POST'])
def register_user():
    """Alternative user-only registration route (if needed)"""
    if request.method == 'POST':
        form_data = {
            'user_type': 'user',
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'password': request.form.get('password'),
            'confirm_password': request.form.get('confirm_password'),
            'address': request.form.get('address'),
            'contact_number': request.form.get('contact_number'),
            'aadhaar_number': request.form.get('aadhaar_number'),
            'date_of_birth': request.form.get('date_of_birth'),
            'gender': request.form.get('gender'),
            'nationality': request.form.get('nationality')
        }
        return register()  # Call the main register function
    
    return render_template('register_user.html')

@auth_bp.route('/register/issuer', methods=['GET', 'POST'])
def register_issuer():
    """Alternative issuer-only registration route (if needed)"""
    if request.method == 'POST':
        form_data = {
            'user_type': 'issuer',
            'issuer_name': request.form.get('issuer_name'),
            'issuer_type': request.form.get('issuer_type'),
            'email': request.form.get('email'),
            'password': request.form.get('password'),
            'confirm_password': request.form.get('confirm_password'),
            'address': request.form.get('address')
        }
        return register()  # Call the main register function
    
    return render_template('register_issuer.html')