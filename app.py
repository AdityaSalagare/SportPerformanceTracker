import os
import logging
from flask import Flask, render_template, redirect, url_for, flash, session, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import json
from datetime import datetime
from bson import ObjectId
import pymongo
from pymongo.errors import ConnectionFailure
from extensions import mongo, bcrypt
# Configure logging
logging.getLogger("werkzeug").setLevel(logging.WARNING)
from flask_wtf.csrf import CSRFProtect

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)
# Create Flask app
app = Flask(__name__)
app.json_encoder = CustomJSONEncoder
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

mongo_uri = "mongodb+srv://atsalagare2:atsalagare2@cluster0.rd1gzln.mongodb.net/evaluator?retryWrites=true&w=majority&appName=Cluster0"
app.config["MONGO_URI"] = mongo_uri

try:
    client = pymongo.MongoClient(mongo_uri)
    client.admin.command('ping')
    logging.info("MongoDB connection successful")
except ConnectionFailure as e:
    logging.error(f"MongoDB connection failed: {e}")

mongo.init_app(app)
bcrypt.init_app(app)
CORS(app)
csrf = CSRFProtect(app)
# Import routes AFTER extensions are initialized
from routes.auth_routes import auth_bp
from routes.coach_routes import coach_bp
from routes.athlete_routes import athlete_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(coach_bp)
app.register_blueprint(athlete_bp)

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Convert MongoDB data to JSON serializable format
def parse_json(data):
    from bson import json_util
    return json.loads(json_util.dumps(data))

# Context processor for global template variables
@app.context_processor
def utility_processor():
    def is_coach():
        return session.get('role') == 'coach'
    
    def is_athlete():
        return session.get('role') == 'athlete'
    
    def get_user_id():
        return session.get('user_id')
    
    def get_username():
        return session.get('username')
        
    return dict(
        is_coach=is_coach, 
        is_athlete=is_athlete, 
        get_user_id=get_user_id,
        get_username=get_username
    )

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('index.html', error="Server error occurred"), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
