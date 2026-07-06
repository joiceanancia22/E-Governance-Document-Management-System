import datetime
import random
import string
from extensions import mongo 

def generate_user_id():
    """
    Generates a unique User ID in the format U{4-digit number}
    e.g., U1001, U1002, etc.
    """
    # Get the last user ID from the database
    last_user = mongo.db.users.find_one(sort=[("User_id", -1)])
    
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
    last_issuer = mongo.db.issuers.find_one(
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

def generate_document_id(user_id, document_type):
    """
    Generates a unique Document ID in the format D{YMD}{User-specific counter}
    e.g., D202503001, D202503002, etc.
    """
    # Current date in YYYYMM format
    date_prefix = datetime.datetime.now().strftime("%Y%m")
    
    # Get the last document ID from the database for this user
    last_document = mongo.db.documents.find_one(
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
    last_log = mongo.db.audit_logs.find_one(sort=[("Audit_id", -1)])
    
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
    last_access = mongo.db.access_control.find_one(sort=[("Access_id", -1)])
    
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
