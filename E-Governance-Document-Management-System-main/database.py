from flask_pymongo import PyMongo
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
import os
from dotenv import load_dotenv

# Initialize Flask-PyMongo extension
mongo = PyMongo()

def init_db(app):
    """Initialize database connection for Flask application"""
    load_dotenv()
    
    # Configure MongoDB URI
    app.config["MONGO_URI"] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/document_management_system')
    
    # Initialize Flask-PyMongo
    mongo.init_app(app)
    
    # Create indexes
    create_indexes(mongo.db)
    
    return mongo

def create_indexes(db):
    """Create database indexes for better performance"""
    # User collection
    db.users.create_index("User_id", unique=True)
    db.users.create_index("email", unique=True)
    
    # Issuer collection
    db.issuers.create_index("Issuer_id", unique=True)
    db.issuers.create_index("email", unique=True)
    
    # Document collection
    db.documents.create_index([("user_id", 1), ("document_type", 1)])
    db.documents.create_index("issuer_id")
    db.documents.create_index("approval.expiry_date")
    
    # Audit Log collection
    db.audit_logs.create_index([("user_id", 1), ("timestamp", -1)])
    db.audit_logs.create_index("document_id")
    
    # Access Control collection
    db.access_controls.create_index([("user_id", 1), ("document_id", 1)], unique=True)


# User Collection Operations
def create_user(user_data):
    """Create a new user in the database"""
    user_data['created_at'] = datetime.datetime.now()
    result = mongo.db.users.insert_one(user_data)
    return str(result.inserted_id)

def get_user_by_id(user_id):
    """Get user by ID"""
    try:
        return mongo.db.users.find_one({"_id": ObjectId(user_id)})
    except:
        return mongo.db.users.find_one({"User_id": user_id})

def get_user_by_email(email):
    """Get user by email"""
    return mongo.db.users.find_one({"email": email})

def update_user(user_id, update_data):
    """Update user information"""
    return mongo.db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )

# Issuer Collection Operations
def create_issuer(issuer_data):
    """Create a new issuer in the database"""
    issuer_data['created_at'] = datetime.datetime.now()
    result = mongo.db.issuers.insert_one(issuer_data)
    return str(result.inserted_id)

def get_issuer_by_id(issuer_id):
    """Get issuer by ID"""
    try:
        return mongo.db.issuers.find_one({"_id": ObjectId(issuer_id)})
    except:
        return mongo.db.issuers.find_one({"Issuer_id": issuer_id})

def get_issuer_by_email(email):
    """Get issuer by email"""
    return mongo.db.issuers.find_one({"email": email})

# Document Collection Operations
def create_document(document_data):
    """Create a new document record in the database"""
    document_data['created_at'] = datetime.datetime.now()
    result = mongo.db.documents.insert_one(document_data)
    return str(result.inserted_id)

def get_document_by_id(document_id):
    """Get document by ID"""
    try:
        return mongo.db.documents.find_one({"_id": ObjectId(document_id)})
    except:
        return mongo.db.documents.find_one({"_id": document_id})

def get_documents_by_user(user_id):
    """Get all documents belonging to a user"""
    return list(mongo.db.documents.find({"user_id": user_id}))

def get_documents_by_issuer(issuer_id):
    """Get all documents issued by an issuer"""
    return list(mongo.db.documents.find({"issuer_id": issuer_id}))

def update_document(document_id, update_data):
    """Update document information"""
    return mongo.db.documents.update_one(
        {"_id": ObjectId(document_id)},
        {"$set": update_data}
    )

def delete_document(document_id):
    """Delete a document"""
    return mongo.db.documents.delete_one({"_id": ObjectId(document_id)})

# Audit Log Collection Operations
def create_audit_log(log_data):
    """Create a new audit log entry"""
    log_data['timestamp'] = datetime.datetime.now()
    result = mongo.db.audit_logs.insert_one(log_data)
    return str(result.inserted_id)

def get_audit_logs_by_user(user_id):
    """Get all audit logs for a specific user"""
    return list(mongo.db.audit_logs.find({"user_id": user_id}))

def get_audit_logs_by_document(document_id):
    """Get all audit logs for a specific document"""
    return list(mongo.db.audit_logs.find({"document_id": document_id}))

def get_filtered_audit_logs(filter_criteria):
    """Get audit logs based on filter criteria"""
    return list(mongo.db.audit_logs.find(filter_criteria))

# Access Control Collection Operations
def create_access_control(access_data):
    """Create a new access control record"""
    access_data['created_at'] = datetime.datetime.now()
    result = mongo.db.access_controls.insert_one(access_data)
    return str(result.inserted_id)

def get_access_control(user_id, document_id):
    """Get access control for a user and document"""
    return mongo.db.access_controls.find_one({
        "user_id": user_id,
        "document_id": document_id
    })

def get_expiring_documents(days=7):
    """Get documents that will expire within the specified number of days"""
    today = datetime.datetime.now()
    expiry_date = today + datetime.timedelta(days=days)
    
    return list(mongo.db.documents.find({
        "approval.expiry_date": {
            "$ne": None,
            "$lte": expiry_date,
            "$gt": today
        }
    }))
