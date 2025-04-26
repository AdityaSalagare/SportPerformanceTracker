#!/usr/bin/env python3
from extensions import mongo
from bson.objectid import ObjectId
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database():
    """Check the current state of the database"""
    logger.info("Checking database status...")
    
    # Count users by role
    coach_count = mongo.db.users.count_documents({"role": "coach"})
    athlete_count = mongo.db.users.count_documents({"role": "athlete"})
    logger.info(f"Users: {coach_count} coaches, {athlete_count} athletes")
    
    # Get coaches
    coaches = list(mongo.db.users.find({"role": "coach"}))
    for coach in coaches:
        logger.info(f"Coach: {coach['username']} ({coach['email']})")
    
    # Get athletes
    athletes = list(mongo.db.users.find({"role": "athlete"}))
    for athlete in athletes:
        logger.info(f"Athlete: {athlete['username']} ({athlete['email']})")
    
    # Count teams
    team_count = mongo.db.teams.count_documents({})
    logger.info(f"Teams: {team_count}")
    
    # Get team details
    teams = list(mongo.db.teams.find())
    for team in teams:
        athlete_ids = team.get('athletes', [])
        logger.info(f"Team: {team['name']} with {len(athlete_ids)} athletes")
        
        # Show team members and roles
        athlete_details = team.get('athlete_details', [])
        for detail in athlete_details:
            athlete_id = detail.get('athlete_id')
            role = detail.get('role')
            athlete = mongo.db.users.find_one({"_id": ObjectId(athlete_id)})
            if athlete:
                logger.info(f"  - {athlete['username']} as {role}")
    
    # Count performance records
    perf_count = mongo.db.performances.count_documents({})
    logger.info(f"Performance records: {perf_count}")
    
    # Show performance metrics used
    metrics = mongo.db.performances.distinct("metric_name")
    logger.info(f"Metrics recorded: {', '.join(metrics)}")
    
    # Count performances per athlete
    for athlete in athletes:
        athlete_id = str(athlete['_id'])
        count = mongo.db.performances.count_documents({"athlete_id": athlete_id})
        logger.info(f"Performances for {athlete['username']}: {count}")
    
    logger.info("Database check complete!")

def main():
    """Main function to check database"""
    try:
        check_database()
        logger.info("You can login with coach@cricket.com / password123")
        
    except Exception as e:
        logger.error(f"Error checking database: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()