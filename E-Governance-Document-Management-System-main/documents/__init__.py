from flask import Flask , Blueprint
from flask_pymongo import PyMongo
import os
documents_bp = Blueprint('documents', __name__, url_prefix='/documents')

# Import routes AFTER creating blueprint to avoid circular imports
from . import routes
app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/e_governance_dms"

app.register_blueprint(documents_bp)
# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}

# Upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
mongo = PyMongo(app)