#!/usr/bin/env python3
from extensions import mongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cricket metrics
cricket_metrics = [
    # Batting metrics
    {
        "name": "batting_average",
        "description": "Average runs scored per dismissal",
        "unit": "runs",
        "min_value": 0,
        "max_value": 100,
        "created_at": datetime.now()
    },
    {
        "name": "strike_rate",
        "description": "Runs scored per 100 balls faced",
        "unit": "",
        "min_value": 0,
        "max_value": 200,
        "created_at": datetime.now()
    },
    {
        "name": "runs_scored",
        "description": "Total runs scored in match/session",
        "unit": "runs",
        "min_value": 0,
        "max_value": 500,
        "created_at": datetime.now()
    },
    # Bowling metrics
    {
        "name": "bowling_average",
        "description": "Runs conceded per wicket taken",
        "unit": "",
        "min_value": 0,
        "max_value": 100,
        "created_at": datetime.now()
    },
    {
        "name": "economy_rate",
        "description": "Runs conceded per over",
        "unit": "runs/over",
        "min_value": 0,
        "max_value": 15,
        "created_at": datetime.now()
    },
    {
        "name": "bowling_speed",
        "description": "Speed of delivery",
        "unit": "km/h",
        "min_value": 80,
        "max_value": 160,
        "created_at": datetime.now()
    },
    {
        "name": "wickets_taken",
        "description": "Number of wickets taken",
        "unit": "count",
        "min_value": 0,
        "max_value": 10,
        "created_at": datetime.now()
    }
]

def clean_database():
    """Clear previous data"""
    logger.info("Cleaning database...")
    mongo.db.users.delete_many({})
    mongo.db.teams.delete_many({})
    mongo.db.performances.delete_many({})
    mongo.db.notifications.delete_many({})
    logger.info("Database cleaned")

def create_coach():
    """Create coach user"""
    logger.info("Creating coach user...")
    coach_data = {
        "username": "Coach Singh",
        "email": "coach@cricket.com",
        "password_hash": generate_password_hash("password123"),
        "role": "coach",
        "created_at": datetime.now()
    }
    coach_id = str(mongo.db.users.insert_one(coach_data).inserted_id)
    logger.info(f"Coach created with ID: {coach_id}")
    
    # Save coach ID to file for next step
    with open('coach_id.txt', 'w') as f:
        f.write(coach_id)
    
    return coach_id

def create_teams(coach_id):
    """Create cricket teams"""
    team_names = ["Mumbai Strikers", "Delhi Capitals"]
    logger.info("Creating teams...")
    team_ids = []
    
    for team_name in team_names:
        team_data = {
            "name": team_name,
            "coach_id": coach_id,
            "sport": "Cricket",
            "description": f"{team_name} - A premier cricket team",
            "created_at": datetime.now(),
            "athletes": [],
            "metrics": cricket_metrics,
            "athlete_details": []
        }
        team_id = str(mongo.db.teams.insert_one(team_data).inserted_id)
        team_ids.append(team_id)
        logger.info(f"Team '{team_name}' created with ID: {team_id}")
    
    # Save team IDs to file for next step
    with open('team_ids.txt', 'w') as f:
        f.write(json.dumps(team_ids))
    
    return team_ids

def main():
    """Create coach and teams"""
    try:
        # Clean database
        clean_database()
        
        # Create coach
        coach_id = create_coach()
        
        # Create teams
        team_ids = create_teams(coach_id)
        
        logger.info(f"Created coach and {len(team_ids)} teams!")
        
    except Exception as e:
        logger.error(f"Error creating coach and teams: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()