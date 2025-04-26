#!/usr/bin/env python3
from extensions import mongo
from bson.objectid import ObjectId
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Player roles
roles = ["batsman", "bowler", "all_rounder", "wicket_keeper", "captain"]

def assign_athletes_to_teams():
    """Assign athletes to teams with specific roles"""
    logger.info("Assigning athletes to teams...")
    
    # Load data from previous steps
    with open('coach_id.txt', 'r') as f:
        coach_id = f.read().strip()
    
    with open('team_ids.txt', 'r') as f:
        team_ids = json.loads(f.read())
    
    with open('athlete_ids.txt', 'r') as f:
        athlete_ids = json.loads(f.read())
    
    # Distribute athletes evenly across teams
    athletes_per_team = len(athlete_ids) // len(team_ids)
    remaining = len(athlete_ids) % len(team_ids)
    
    start_idx = 0
    assignments = {}
    
    for i, team_id in enumerate(team_ids):
        count = athletes_per_team + (1 if i < remaining else 0)
        team_athletes = athlete_ids[start_idx:start_idx + count]
        start_idx += count
        
        for athlete_id in team_athletes:
            # Assign a role based on position in the team
            idx = team_athletes.index(athlete_id)
            role = roles[idx % len(roles)]
            
            # Add athlete to team
            mongo.db.teams.update_one(
                {"_id": ObjectId(team_id)},
                {
                    "$push": {
                        "athletes": athlete_id,
                        "athlete_details": {
                            "athlete_id": athlete_id,
                            "role": role,
                            "added_at": datetime.now()
                        }
                    }
                }
            )
            
            # Store assignment for future reference
            if athlete_id not in assignments:
                assignments[athlete_id] = []
            assignments[athlete_id].append((team_id, role))
            
            logger.info(f"Added athlete {athlete_id} to team {team_id} as {role}")
    
    # Save assignments for next step
    with open('assignments.txt', 'w') as f:
        f.write(json.dumps(assignments))
    
    return assignments

def main():
    """Assign athletes to teams"""
    try:
        # Assign athletes to teams
        assignments = assign_athletes_to_teams()
        logger.info("Athletes successfully assigned to teams!")
        
    except Exception as e:
        logger.error(f"Error assigning athletes: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()