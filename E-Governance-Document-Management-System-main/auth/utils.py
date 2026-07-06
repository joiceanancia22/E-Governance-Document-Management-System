import re
from extensions import mongo 
import datetime
import random
import string


def generate_user_id():
    """
    Generates a unique User ID in the format U{4-digit number}
    e.g., U1001, U1002, etc.
    """
    # Get the last user ID from the database
    last_user = mongo.db.User.find_one(sort=[("User_id", -1)])
    
    # If no users exist yet, start with U1001
    if not last_user:
        return "U1001"
    
    # Extract the numeric part of the last user ID
    try:
        last_id_num = int(last_user["User_id"][1:])
        # Increment by 1
        new_id_num = last_id_num + 1
        return f"U{new_id_num:04d}"
    except (ValueError, TypeError, KeyError):
        # If there's an issue with the existing ID format, create a fallback
        timestamp = datetime.datetime.now().strftime("%y%m%d%H%M")
        random_digits = ''.join(random.choices(string.digits, k=2))
        return f"U{timestamp}{random_digits}"

def generate_issuer_id(issuer_type):
    """
    Generates a unique Issuer ID based on the issuer type
    Format: {Abbreviation}-{3-digit number}
    e.g., CBSE-001, GOV-001, etc.
    """
    # Create an abbreviation based on issuer type
    if issuer_type.lower() == "educational board":
        prefix = "EDU"
    elif issuer_type.lower() == "government":
        prefix = "GOV"
    elif issuer_type.lower() == "financial institution":
        prefix = "FIN"
    elif issuer_type.lower() == "corporate":
        prefix = "CORP"
    else:
        # Get first 3-4 letters of the issuer type as prefix
        prefix = ''.join(c for c in issuer_type.upper() if c.isalpha())[:4]
    
    # Get the last issuer ID with the same prefix from the database
    last_issuer = mongo.db.Issuer.find_one(
        {"Issuer_id": {"$regex": f"^{prefix}-"}}, 
        sort=[("Issuer_id", -1)]
    )
    
    # If no issuer with this prefix exists yet, start with 001
    if not last_issuer:
        return f"{prefix}-001"
    
    try:
        # Extract the numeric part of the last issuer ID
        last_id_num = int(last_issuer["Issuer_id"].split('-')[1])
        # Increment by 1
        new_id_num = last_id_num + 1
        return f"{prefix}-{new_id_num:03d}"
    except (ValueError, TypeError, KeyError, IndexError):
        # If there's an issue with the existing ID format, create a fallback
        timestamp = datetime.datetime.now().strftime("%y%m%d")
        random_digits = ''.join(random.choices(string.digits, k=2))
        return f"{prefix}-{timestamp}{random_digits}"

def validate_registration(data, user_type):
    """Validate registration form data"""
    errors = []
    
    # Check required fields
    required_fields = ['name', 'email', 'password', 'confirm_password']
    
    if user_type == 'user':
        required_fields.extend(['address', 'contact_number', 'date_of_birth', 'gender', 'nationality'])
    else:  # issuer
        required_fields.extend(['issuer_name', 'issuer_type', 'address'])
        
    for field in required_fields:
        if not data.get(field):
            errors.append(f'{field.replace("_", " ").title()} is required')
    
    # If required fields are missing, return early
    if errors:
        return errors
    
    # Validate email format
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, data['email']):
        errors.append('Invalid email format')
    
    # Check if email already exists
    if user_type == 'user' and mongo.db.get_user_by_email(data['email']):
        errors.append('Email already registered as a user')
    elif user_type == 'issuer' and mongo.db.get_issuer_by_email(data['email']):
        errors.append('Email already registered as an issuer')
    
    # Validate password
    if len(data['password']) < 8:
        errors.append('Password must be at least 8 characters long')
    
    # Check if passwords match
    if data['password'] != data['confirm_password']:
        errors.append('Passwords do not match')
    
    # User-specific validations
    if user_type == 'user':
        # Validate contact number
        if not re.match(r'^\+?[0-9]{10,15}$', data['contact_number']):
            errors.append('Invalid contact number format')
        
        # Validate Aadhaar number if provided
        if data.get('aadhaar_number') and not re.match(r'^[0-9]{4}-[0-9]{4}-[0-9]{4}$', data['aadhaar_number']):
            errors.append('Invalid Aadhaar number format (should be XXXX-XXXX-XXXX)')
    
    return errors

def validate_login(email, password):
    """Validate login form data"""
    errors = []
    
    # Check required fields
    if not email:
        errors.append('Email is required')
    
    if not password:
        errors.append('Password is required')
    
    return errors

def is_authenticated():
    """Check if user is authenticated"""
    from flask import session
    return 'user_id' in session

def is_issuer():
    """Check if authenticated user is an issuer"""
    from flask import session
    return is_authenticated() and session.get('role') == 'issuer'

def login_required(view_function):
    """Decorator for routes that require login"""
    from functools import wraps
    from flask import redirect, url_for, flash, session
    
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('auth.login'))
        return view_function(*args, **kwargs)
    
    return decorated_function

def issuer_required(view_function):
    """Decorator for routes that require issuer privileges"""
    from functools import wraps
    from flask import redirect, url_for, flash
    
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if not is_issuer():
            flash('You need issuer privileges to access this page', 'warning')
            return redirect(url_for('documents.dashboard'))
        return view_function(*args, **kwargs)
    
    return decorated_function
