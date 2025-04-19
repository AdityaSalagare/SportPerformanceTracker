#!/usr/bin/env python3
from app import mongo
from bson.objectid import ObjectId
from models import User, Team, Performance, Notification
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cricket player names
player_names = [
    "Virat Kohli", "Rohit Sharma", "Jasprit Bumrah", "MS Dhoni", "Ravindra Jadeja",
    "KL Rahul", "Hardik Pandya", "Rishabh Pant", "Ravichandran Ashwin", "Shikhar Dhawan",
    "Bhuvneshwar Kumar", "Yuzvendra Chahal", "Mohammed Shami", "Shreyas Iyer", "Prithvi Shaw",
    "Ishan Kishan", "Shardul Thakur", "Washington Sundar", "Deepak Chahar", "Suryakumar Yadav",
    "T Natarajan", "Kuldeep Yadav", "Mayank Agarwal"
]

# Player roles
roles = ["batsman", "bowler", "all_rounder", "wicket_keeper", "captain"]

# Team names
team_names = ["Mumbai Strikers", "Delhi Capitals", "Chennai Kings", "Rajasthan Royals", "Punjab Knights"]

def clean_database():
    """Clear previous data"""
    logger.info("Cleaning database...")
    mongo.db.users.delete_many({})
    mongo.db.teams.delete_many({})
    mongo.db.performances.delete_many({})
    mongo.db.notifications.delete_many({})
    logger.info("Database cleaned")

def create_coach():
    """Create a coach user"""
    logger.info("Creating coach user...")
    coach_data = {
        "username": "Coach Singh",
        "email": "coach@cricket.com",
        "password_hash": generate_password_hash("password123"),
        "role": "coach",
        "created_at": datetime.now()
    }
    coach_id = mongo.db.users.insert_one(coach_data).inserted_id
    logger.info(f"Coach created with ID: {coach_id}")
    return str(coach_id)

def create_teams(coach_id):
    """Create cricket teams"""
    logger.info("Creating teams...")
    team_ids = []
    for team_name in team_names:
        team_id = Team.create_team(
            name=team_name,
            coach_id=coach_id,
            sport="Cricket",
            description=f"{team_name} - A premier cricket team"
        )
        logger.info(f"Team '{team_name}' created with ID: {team_id}")
        team_ids.append(team_id)
        
        # Add cricket metrics to team
        Team.add_cricket_metrics(team_id)
        logger.info(f"Added cricket metrics to team '{team_name}'")
    
    return team_ids

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
        athlete_id = mongo.db.users.insert_one(athlete_data).inserted_id
        logger.info(f"Athlete '{name}' created with ID: {athlete_id}")
        athlete_ids.append(str(athlete_id))
    
    return athlete_ids

def assign_athletes_to_teams(team_ids, athlete_ids):
    """Assign athletes to teams with specific roles"""
    logger.info("Assigning athletes to teams...")
    
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
            # Assign a role based on position in the team (roughly distribute roles)
            idx = team_athletes.index(athlete_id)
            role = roles[idx % len(roles)]
            
            Team.add_athlete_to_team(team_id, athlete_id, role)
            logger.info(f"Added athlete {athlete_id} to team {team_id} as {role}")
            
            # Store assignment for future reference
            if athlete_id not in assignments:
                assignments[athlete_id] = []
            assignments[athlete_id].append((team_id, role))
    
    return assignments

def record_performances(assignments, coach_id):
    """Record performances for athletes"""
    logger.info("Recording performance data...")
    
    # Define date range for performance data (last 6 months)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    # Pre-defined metric ranges based on role
    metric_ranges = {
        "batsman": {
            "batting_average": (25, 60),
            "strike_rate": (100, 180),
            "runs_scored": (20, 120),
            "centuries": (0, 2),
            "half_centuries": (0, 5),
            "boundaries": (2, 12),
            "sixes": (0, 6)
        },
        "bowler": {
            "bowling_average": (15, 35),
            "economy_rate": (4, 9),
            "bowling_speed": (120, 150),
            "wickets_taken": (0, 5),
            "dot_balls_percentage": (40, 70),
            "maidens": (0, 2),
            "extras_conceded": (0, 8)
        },
        "all_rounder": {
            "batting_average": (20, 45),
            "bowling_average": (20, 40),
            "runs_scored": (15, 80),
            "wickets_taken": (0, 3),
            "strike_rate": (90, 160),
            "economy_rate": (5, 10)
        },
        "wicket_keeper": {
            "batting_average": (20, 50),
            "strike_rate": (90, 150),
            "runs_scored": (15, 60),
            "catches_taken": (0, 4),
            "run_outs": (0, 2)
        },
        "captain": {
            "batting_average": (30, 60),
            "strike_rate": (100, 160),
            "bowling_average": (20, 40),
            "runs_scored": (25, 100)
        }
    }
    
    # Common fielding metrics for all roles
    fielding_metrics = {
        "catches_taken": (0, 3),
        "run_outs": (0, 2),
        "fielding_accuracy": (60, 95)
    }
    
    # Generate performance records
    for athlete_id, team_assignments in assignments.items():
        for team_id, role in team_assignments:
            # Determine which metrics to record based on role
            metrics_to_record = {}
            if role in metric_ranges:
                metrics_to_record.update(metric_ranges[role])
            
            # Add fielding metrics for everyone
            metrics_to_record.update(fielding_metrics)
            
            # Create 5-10 performance records over time for each athlete
            num_records = random.randint(5, 10)
            dates = []
            for _ in range(num_records):
                days_ago = random.randint(0, 180)
                record_date = end_date - timedelta(days=days_ago)
                dates.append(record_date)
            
            # Sort dates to ensure progression
            dates.sort()
            
            # For each metric, create performance records with natural progression
            for metric_name, value_range in metrics_to_record.items():
                min_val, max_val = value_range
                
                # Starting point for progressive values
                base_value = random.uniform(min_val, (min_val + max_val) / 2)
                
                # Maximum possible improvement (as a percentage of base value)
                max_improvement = random.uniform(0.1, 0.4)  # 10% to 40% improvement
                
                # Create records with progressive performance
                for i, record_date in enumerate(dates):
                    # Progessive improvement with some random fluctuation
                    progress = (i / len(dates)) * max_improvement
                    fluctuation = random.uniform(-0.05, 0.1)  # -5% to +10% fluctuation
                    
                    # For metrics where lower is better, we reduce the value
                    if metric_name in ["bowling_average", "economy_rate", "extras_conceded"]:
                        # For these metrics, we want to decrease values
                        improvement = 1 - progress
                        value = base_value * (improvement + fluctuation)
                        value = max(min_val, min(value, max_val))
                    else:
                        # For metrics where higher is better
                        improvement = 1 + progress
                        value = base_value * (improvement + fluctuation)
                        value = max(min_val, min(value, max_val))
                    
                    # Round specific metrics
                    if metric_name in ["centuries", "half_centuries", "wickets_taken", "maidens", "catches_taken", "run_outs"]:
                        value = round(value)
                    elif metric_name in ["runs_scored", "boundaries", "sixes", "extras_conceded"]:
                        value = round(value)
                    else:
                        # Round to 2 decimal places for other metrics
                        value = round(value, 2)
                    
                    # Record the performance
                    performance_id = Performance.record_performance(
                        athlete_id=athlete_id,
                        team_id=team_id,
                        metric_name=metric_name,
                        value=value,
                        recorded_by=coach_id,
                        notes=f"Recorded on {record_date.strftime('%Y-%m-%d')}"
                    )
                    
                    # Set the recorded date explicitly to maintain the timeline
                    mongo.db.performances.update_one(
                        {"_id": ObjectId(performance_id)},
                        {"$set": {"recorded_at": record_date}}
                    )
            
            logger.info(f"Recorded {num_records} performance metrics for athlete {athlete_id} in team {team_id}")

def main():
    """Main function to populate the database"""
    try:
        # Clear previous data
        clean_database()
        
        # Create coach
        coach_id = create_coach()
        
        # Create teams
        team_ids = create_teams(coach_id)
        
        # Create athletes
        athlete_ids = create_athletes()
        
        # Assign athletes to teams
        assignments = assign_athletes_to_teams(team_ids, athlete_ids)
        
        # Record performances
        record_performances(assignments, coach_id)
        
        logger.info("Database successfully populated with cricket player data!")
        logger.info(f"Created {len(athlete_ids)} athletes across {len(team_ids)} teams")
        logger.info("You can now login as Coach Singh (email: coach@cricket.com, password: password123)")
        
    except Exception as e:
        logger.error(f"Error populating database: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()