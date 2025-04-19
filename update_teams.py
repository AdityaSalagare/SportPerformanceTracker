#!/usr/bin/env python3
from app import mongo
from bson.objectid import ObjectId
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_team_coach_ids():
    """Update all teams to use the current coach ID"""
    # Get the current coach from coach_id.txt
    try:
        with open('coach_id.txt', 'r') as f:
            coach_id = f.read().strip()
            logger.info(f"Using coach ID from file: {coach_id}")
    except FileNotFoundError:
        # Find any coach in the database
        coach = mongo.db.users.find_one({"role": "coach"})
        if not coach:
            logger.error("No coach found in the database")
            return False
        coach_id = str(coach['_id'])
        logger.info(f"Using coach ID from database: {coach_id}")
    
    # Update all teams to use this coach_id
    result = mongo.db.teams.update_many(
        {}, 
        {"$set": {"coach_id": coach_id}}
    )
    
    logger.info(f"Updated {result.modified_count} teams to use coach ID: {coach_id}")
    
    # Verify the update
    teams = list(mongo.db.teams.find({"coach_id": coach_id}))
    logger.info(f"Found {len(teams)} teams for coach ID: {coach_id}")
    
    for team in teams:
        logger.info(f"Team: {team['name']} (ID: {team['_id']})")
    
    return True

if __name__ == "__main__":
    logger.info("Updating team coach IDs...")
    update_team_coach_ids()
    logger.info("Done!")