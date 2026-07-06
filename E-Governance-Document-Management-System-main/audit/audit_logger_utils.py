from datetime import datetime
from extensions import mongo 
from id_generator_utils import generate_audit_log_id

def log_action(user_id, document_id, action, performed_by):
    """
    Log an action performed on a document.
    
    Args:
        user_id: ID of the user who owns the document or performed the action
        document_id: ID of the document being acted upon
        action: Description of the action (e.g., "Viewed", "Uploaded", "Edited")
        performed_by: Role who performed the action ("User" or "Issuer")
    """
    # Generate a unique audit ID
    audit_id = generate_audit_log_id()
    
    # Create audit log entry
    audit_log = {
        "Audit_id": audit_id,
        "user_id": user_id,
        "document_id": document_id,
        "action": action,
        "timestamp": datetime.now().isoformat(),
        "performed_by": performed_by
    }
    
    # Insert audit log to database
    mongo.db.audit_logs.insert_one(audit_log)
    
    return audit_id
