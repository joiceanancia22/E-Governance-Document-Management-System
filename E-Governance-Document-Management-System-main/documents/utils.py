import re
import database as db
import datetime
import random
import string

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_extension(filename):
    """Get the file extension"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def get_document_status_class(status):
    """Get CSS class for document status"""
    status_classes = {
        'Approved': 'success',
        'Pending': 'warning',
        'Rejected': 'danger',
        'Expired': 'secondary'
    }
    return status_classes.get(status, 'primary')

def is_document_expired(expiry_date):
    """Check if document is expired"""
    from datetime import datetime
    if not expiry_date:
        return False
    return datetime.now() > expiry_date

def generate_document_id(user_id, document_type):
    """
    Generates a unique Document ID in the format D{YMD}{User-specific counter}
    e.g., D202503001, D202503002, etc.
    """
    # Current date in YYYYMM format
    date_prefix = datetime.datetime.now().strftime("%Y%m")
    
    # Get the last document ID from the database for this user
    last_document = db.documents.find_one(
        {"document_id": {"$regex": f"^D{date_prefix}"}},
        sort=[("document_id", -1)]
    )
    
    # If no documents exist yet with this prefix, start with 001
    if not last_document:
        counter = 1
    else:
        try:
            # Extract the counter part of the last document ID
            counter_part = last_document["document_id"][7:]  # After 'D' and YYYYMM
            counter = int(counter_part) + 1
        except (ValueError, TypeError, KeyError, IndexError):
            # If there's an issue with the existing ID format, create a fallback
            counter = random.randint(1, 999)
    
    # Format: D + YYYYMM + 3-digit counter
    return f"D{date_prefix}{counter:03d}"

def generate_audit_log_id():
    """
    Generates a unique Audit Log ID in the format AL{6-digit number}
    e.g., AL000001, AL000002, etc.
    """
    # Get the last audit log ID from the database
    last_log = db.audit_logs.find_one(sort=[("Audit_id", -1)])
    
    # If no logs exist yet, start with AL000001
    if not last_log:
        return "AL000001"
    
    try:
        # Extract the numeric part of the last log ID
        last_id_num = int(last_log["Audit_id"][2:])
        # Increment by 1
        new_id_num = last_id_num + 1
        return f"AL{new_id_num:06d}"
    except (ValueError, TypeError, KeyError):
        # If there's an issue with the existing ID format, create a fallback
        timestamp = datetime.datetime.now().strftime("%y%m%d%H%M%S")
        return f"AL{timestamp}"

def generate_access_control_id():
    """
    Generates a unique Access Control ID in the format AC{4-digit number}
    e.g., AC0001, AC0002, etc.
    """
    # Get the last access control ID from the database
    last_access = db.access_control.find_one(sort=[("Access_id", -1)])
    
    # If no records exist yet, start with AC0001
    if not last_access:
        return "AC0001"
    
    try:
        # Extract the numeric part of the last access ID
        last_id_num = int(last_access["Access_id"][2:])
        # Increment by 1
        new_id_num = last_id_num + 1
        return f"AC{new_id_num:04d}"
    except (ValueError, TypeError, KeyError):
        # If there's an issue with the existing ID format, create a fallback
        timestamp = datetime.datetime.now().strftime("%y%m%d%H%M")
        return f"AC{timestamp}"
