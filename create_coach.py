#!/usr/bin/env python3
from extensions import mongo, bcrypt
from bson.objectid import ObjectId
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_coach():
    """Create a coach user with proper password hashing"""
    logger.info("Creating coach user with proper hashing...")
    
    # Delete existing coaches
    mongo.db.users.delete_many({"role": "coach"})
    
    # Create coach with properly hashed password
    coach_data = {
        "username": "Coach Singh",
        "email": "coach@cricket.com",
        "password_hash": bcrypt.generate_password_hash("password123").decode('utf-8'),
        "role": "coach",
        "created_at": datetime.now()
    }
    
    coach_id = mongo.db.users.insert_one(coach_data).inserted_id
    logger.info(f"Coach created with ID: {coach_id}")
    
    # Save coach ID to file for reference
    with open('coach_id.txt', 'w') as f:
        f.write(str(coach_id))
    
    logger.info("Coach creation successful!")
    logger.info("You can login with:")
    logger.info("Email: coach@cricket.com")
    logger.info("Password: password123")
    
    return str(coach_id)

if __name__ == "__main__":
    create_coach()