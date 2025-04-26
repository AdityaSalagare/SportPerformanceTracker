#!/usr/bin/env python3
from extensions import mongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cricket player names
player_names = [
    "Virat Kohli", "Rohit Sharma", "Jasprit Bumrah", "MS Dhoni", 
    "Ravindra Jadeja", "KL Rahul", "Hardik Pandya", "Rishabh Pant"
]

def create_athletes():
    """Create athlete users"""
    logger.info("Creating athletes...")
    athlete_ids = []
    
    for name in player_names:
        email = name.lower().replace(" ", ".") + "@cricket.com"
        athlete_data = {
            "username": name,
            "email": email,
            "password_hash": generate_password_hash("password123"),
            "role": "athlete",
            "created_at": datetime.now()
        }
        athlete_id = str(mongo.db.users.insert_one(athlete_data).inserted_id)
        athlete_ids.append(athlete_id)
        logger.info(f"Athlete '{name}' created with ID: {athlete_id}")
    
    # Save athlete IDs for next step
    with open('athlete_ids.txt', 'w') as f:
        f.write(json.dumps(athlete_ids))
    
    return athlete_ids

def main():
    """Create athletes"""
    try:
        # Create athletes
        athlete_ids = create_athletes()
        logger.info(f"Created {len(athlete_ids)} athletes!")
        
    except Exception as e:
        logger.error(f"Error creating athletes: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()