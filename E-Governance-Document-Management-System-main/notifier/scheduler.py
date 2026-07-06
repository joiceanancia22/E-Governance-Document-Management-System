from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import database as db
from datetime import datetime
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_scheduler():
    """Initialize the background scheduler"""
    scheduler = BackgroundScheduler()
    
    # Add job for checking expiring documents
    scheduler.add_job(
        check_expiring_documents,
        CronTrigger(hour=9, minute=0),  # Run every day at 9:00 AM
        id='check_expiring_documents',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started")
    return scheduler

def check_expiring_documents():
    """Check for documents that will expire in the next 7 days"""
    logger.info("Checking for expiring documents")
    
    # Get documents expiring in the next 7 days
    expiring_documents = db.get_expiring_documents(days=7)
    
    if not expiring_documents:
        logger.info("No expiring documents found")
        return
    
    logger.info(f"Found {len(expiring_documents)} expiring documents")
    
    # Process each expiring document
    for document in expiring_documents:
        try:
            # Get user information
            user = db.get_user_by_id(document['user_id'])
            
            if not user:
                logger.warning(f"User not found for document {document['_id']}")
                continue
            
            # Send email notification
            send_expiry_notification(user, document)
            
            # Create audit log for notification
            log_data = {
                "user_id": document['user_id'],
                "document_id": document['_id'],
                "action": "Expiry Notification Sent",
                "performed_by": "System"
            }
            db.create_audit_log(log_data)
            
            logger.info(f"Notification sent for document {document['_id']}")
        except Exception as e:
            logger.error(f"Error processing document {document['_id']}: {str(e)}")

def send_expiry_notification(user, document):
    """Send email notification about document expiry"""
    try:
        # Get email settings from environment variables
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_username = os.environ.get('SMTP_USERNAME', 'your-email@gmail.com')
        smtp_password = os.environ.get('SMTP_PASSWORD', 'your-password')
        sender_email = os.environ.get('SENDER_EMAIL', 'document-system@example.com')
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = user['email']
        msg['Subject'] = f"Document Expiry Notification: {document['document_name']}"
        
        # Calculate days to expiry
        expiry_date = document['approval']['expiry_date']
        days_to_expiry = (expiry_date - datetime.now()).days
        
        # Create message body
        body = f"""
        Dear {user['name']},
        
        This is to inform you that your document "{document['document_name']}" will expire in {days_to_expiry} days on {expiry_date.strftime('%Y-%m-%d')}.
        
        Please take necessary action to renew the document if required.
        
        Thank you,
        Document Management System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        logger.info(f"Email notification sent to {user['email']}")
    except Exception as e:
        logger.error(f"Error sending email notification: {str(e)}")

def send_sms_notification(user, document):
    """Send SMS notification about document expiry"""
    # This is a placeholder for SMS notification implementation
    # To implement SMS notifications, you can use services like Twilio, AWS SNS, etc.
    logger.info(f"SMS notification would be sent to {user['contact_number']}")
