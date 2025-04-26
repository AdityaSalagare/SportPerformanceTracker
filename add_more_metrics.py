#!/usr/bin/env python3
from extensions import mongo
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import json
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_more_metrics():
    """Add additional metrics for evaluation purposes"""
    logger.info("Adding more performance metrics...")
    
    # Load data from previous steps
    with open('coach_id.txt', 'r') as f:
        coach_id = f.read().strip()
    
    with open('assignments.txt', 'r') as f:
        assignments_str = f.read()
        assignments_dict = json.loads(assignments_str)
        assignments = {}
        for k, v in assignments_dict.items():
            assignments[k] = v
    
    # Additional metrics based on role
    additional_metrics = {
        "batsman": [
            {"name": "strike_rate", "min": 110, "max": 180},
            {"name": "runs_scored", "min": 30, "max": 120},
            {"name": "boundaries", "min": 3, "max": 12}
        ],
        "bowler": [
            {"name": "economy_rate", "min": 4, "max": 8},
            {"name": "bowling_speed", "min": 130, "max": 150},
            {"name": "wickets_taken", "min": 1, "max": 5}
        ],
        "all_rounder": [
            {"name": "strike_rate", "min": 100, "max": 160},
            {"name": "economy_rate", "min": 5, "max": 9},
            {"name": "wickets_taken", "min": 1, "max": 3}
        ],
        "wicket_keeper": [
            {"name": "strike_rate", "min": 110, "max": 170},
            {"name": "catches_taken", "min": 1, "max": 4}
        ],
        "captain": [
            {"name": "strike_rate", "min": 120, "max": 170},
            {"name": "runs_scored", "min": 40, "max": 120}
        ]
    }
    
    performance_count = 0
    
    # Add metrics for each athlete
    for athlete_id, team_assignments in assignments.items():
        for team_id, role in team_assignments:
            # Get additional metrics for this role
            metrics = additional_metrics.get(role, [])
            
            # Add a single performance for each additional metric
            for metric_info in metrics:
                metric_name = metric_info["name"]
                min_val = metric_info["min"]
                max_val = metric_info["max"]
                
                # Generate a suitable value
                value = random.uniform(min_val, max_val)
                
                # Round values appropriately
                if metric_name in ["wickets_taken", "runs_scored", "boundaries", "catches_taken"]:
                    value = round(value)
                else:
                    value = round(value, 2)
                
                # Random recent date
                record_date = datetime.now() - timedelta(days=random.randint(1, 20))
                
                # Create performance record
                perf_data = {
                    "athlete_id": athlete_id,
                    "team_id": team_id,
                    "metric_name": metric_name,
                    "value": value,
                    "recorded_by": coach_id,
                    "notes": f"Recorded on {record_date.strftime('%Y-%m-%d')}",
                    "recorded_at": record_date
                }
                
                # Add to database
                mongo.db.performances.insert_one(perf_data)
                performance_count += 1
                
    logger.info(f"Added {performance_count} additional metrics")
    return performance_count

def main():
    """Add more metrics for better evaluation"""
    try:
        metric_count = add_more_metrics()
        logger.info("Additional metrics successfully added!")
        logger.info("Login with coach@cricket.com / password123 to evaluate athletes")
        
    except Exception as e:
        logger.error(f"Error adding metrics: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()