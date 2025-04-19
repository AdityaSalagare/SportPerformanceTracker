#!/usr/bin/env python3
from app import mongo
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import json
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def record_performances():
    """Record a minimal set of performances for athletes"""
    logger.info("Recording minimal performance data...")
    
    # Load data from previous steps
    with open('coach_id.txt', 'r') as f:
        coach_id = f.read().strip()
    
    with open('assignments.txt', 'r') as f:
        assignments_str = f.read()
        # Convert string keys to actual keys
        assignments_dict = json.loads(assignments_str)
        assignments = {}
        for k, v in assignments_dict.items():
            assignments[k] = v
    
    # Just record a few key metrics for each athlete
    key_metrics = {
        "batsman": ["batting_average"],
        "bowler": ["bowling_average"],
        "all_rounder": ["batting_average", "bowling_average"],
        "wicket_keeper": ["batting_average"],
        "captain": ["batting_average"]
    }
    
    # Create a single performance record for each athlete's key metrics
    performance_count = 0
    
    for athlete_id, team_assignments in assignments.items():
        for team_id, role in team_assignments:
            # Get metrics for this role
            metrics = key_metrics.get(role, ["batting_average"])
            
            for metric_name in metrics:
                # Generate a value appropriate for the metric
                if metric_name == "batting_average":
                    if role == "batsman":
                        value = random.uniform(35, 55)  # Higher for batsmen
                    else:
                        value = random.uniform(20, 40)
                elif metric_name == "bowling_average":
                    if role == "bowler":
                        value = random.uniform(15, 30)  # Lower for bowlers (good)
                    else:
                        value = random.uniform(25, 40)
                else:
                    value = random.uniform(30, 70)
                
                # Round to 2 decimal places
                value = round(value, 2)
                
                # Record date (recent)
                record_date = datetime.now() - timedelta(days=random.randint(1, 30))
                
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
    
    logger.info(f"Total performances recorded: {performance_count}")
    return performance_count

def main():
    """Record minimal performances"""
    try:
        # Record performances
        performance_count = record_performances()
        logger.info("Minimal performance data successfully recorded!")
        logger.info("Login with coach@cricket.com / password123 to view the data")
        
    except Exception as e:
        logger.error(f"Error recording performances: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()