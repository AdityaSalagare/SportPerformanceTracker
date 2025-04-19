#!/usr/bin/env python3
from app import mongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cricket player names (shorter list)
player_names = [
    "Virat Kohli", "Rohit Sharma", "Jasprit Bumrah", "MS Dhoni", "Ravindra Jadeja",
    "KL Rahul", "Hardik Pandya", "Rishabh Pant", "Ravichandran Ashwin", "Shikhar Dhawan",
    "Bhuvneshwar Kumar", "Yuzvendra Chahal", "Mohammed Shami", "Shreyas Iyer", "Prithvi Shaw",
    "Ishan Kishan", "Shardul Thakur", "Washington Sundar", "Deepak Chahar", "Suryakumar Yadav",
    "T Natarajan", "Kuldeep Yadav", "Mayank Agarwal"
][:12]  # Using just 12 players for faster processing

# Player roles
roles = ["batsman", "bowler", "all_rounder", "wicket_keeper", "captain"]

# Team names (fewer teams)
team_names = ["Mumbai Strikers", "Delhi Capitals"]

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

def create_users_and_teams():
    """Create users and teams in a more optimized way"""
    # Create coach
    logger.info("Creating coach...")
    coach_data = {
        "username": "Coach Singh",
        "email": "coach@cricket.com",
        "password_hash": generate_password_hash("password123"),
        "role": "coach",
        "created_at": datetime.now()
    }
    coach_id = str(mongo.db.users.insert_one(coach_data).inserted_id)
    logger.info(f"Coach created with ID: {coach_id}")
    
    # Create teams
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
    
    # Create athletes
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
    
    return coach_id, team_ids, athlete_ids

def assign_athletes_and_record_performances(coach_id, team_ids, athlete_ids):
    """Assign athletes to teams and record performances"""
    logger.info("Assigning athletes and recording performances...")
    
    # Distribute athletes evenly
    athletes_per_team = len(athlete_ids) // len(team_ids)
    
    # Store assignments
    assignments = {}
    
    for team_idx, team_id in enumerate(team_ids):
        # Get athletes for this team
        start_idx = team_idx * athletes_per_team
        end_idx = start_idx + athletes_per_team if team_idx < len(team_ids) - 1 else len(athlete_ids)
        team_athletes = athlete_ids[start_idx:end_idx]
        
        team_update_operations = []
        performance_records = []
        
        for idx, athlete_id in enumerate(team_athletes):
            # Assign role
            role = roles[idx % len(roles)]
            
            # Update team with athlete and role
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
            
            # Store for reference
            if athlete_id not in assignments:
                assignments[athlete_id] = []
            assignments[athlete_id].append((team_id, role))
            
            logger.info(f"Added athlete {athlete_id} to team {team_id} as {role}")
            
            # Record performances for this athlete (simplified)
            # We'll record 3 performances per metric for each athlete
            for metric in cricket_metrics:
                metric_name = metric["name"]
                min_val = metric["min_value"]
                max_val = metric["max_value"]
                
                # Adjust ranges based on role
                if role == "batsman" and metric_name in ["batting_average", "strike_rate", "runs_scored"]:
                    min_val = min_val * 1.2  # Better batting stats for batsmen
                elif role == "bowler" and metric_name in ["bowling_average", "economy_rate", "bowling_speed", "wickets_taken"]:
                    if metric_name in ["bowling_average", "economy_rate"]:
                        max_val = max_val * 0.8  # Lower is better for these
                    else:
                        min_val = min_val * 1.2  # Better bowling stats for bowlers
                
                # Record 3 performances over time
                for i in range(3):
                    # Date calculations - 1st, 2nd, and 3rd month prior
                    record_date = datetime.now() - timedelta(days=30 * (3-i))
                    
                    # Calculate progressive value
                    if metric_name in ["bowling_average", "economy_rate"]:
                        # Lower is better for these metrics
                        base = random.uniform(min_val, max_val)
                        improvement = 0.95 ** i  # Decrease by 5% each time
                        value = base * improvement
                    else:
                        # Higher is better for these metrics
                        base = random.uniform(min_val, max_val * 0.7)
                        improvement = 1.1 ** i  # Increase by 10% each time
                        value = base * improvement
                    
                    # Round specific metrics
                    if metric_name in ["wickets_taken", "runs_scored"]:
                        value = round(value)
                    else:
                        value = round(value, 2)
                    
                    # Create performance record
                    performance_data = {
                        "athlete_id": athlete_id,
                        "team_id": team_id,
                        "metric_name": metric_name,
                        "value": value,
                        "recorded_by": coach_id,
                        "notes": f"Recorded on {record_date.strftime('%Y-%m-%d')}",
                        "recorded_at": record_date
                    }
                    
                    mongo.db.performances.insert_one(performance_data)
    
    logger.info("Performance records created successfully")
    return assignments

def main():
    """Main function to populate the database"""
    try:
        # Clear previous data
        clean_database()
        
        # Create users and teams
        coach_id, team_ids, athlete_ids = create_users_and_teams()
        
        # Assign athletes and record performances
        assignments = assign_athletes_and_record_performances(coach_id, team_ids, athlete_ids)
        
        logger.info("Database successfully populated with cricket player data!")
        logger.info(f"Created {len(athlete_ids)} athletes across {len(team_ids)} teams")
        logger.info("You can now login as Coach Singh (email: coach@cricket.com, password: password123)")
        
    except Exception as e:
        logger.error(f"Error populating database: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()