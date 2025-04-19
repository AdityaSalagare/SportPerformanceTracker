#!/usr/bin/env python3
from app import mongo
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import json
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_historical_data():
    """Add historical performance data for trends"""
    logger.info("Adding historical performance data...")
    
    # Load data from previous steps
    with open('coach_id.txt', 'r') as f:
        coach_id = f.read().strip()
    
    with open('assignments.txt', 'r') as f:
        assignments_str = f.read()
        assignments_dict = json.loads(assignments_str)
        assignments = {}
        for k, v in assignments_dict.items():
            assignments[k] = v
    
    # Get existing performances to create history for
    performances = list(mongo.db.performances.find())
    
    # We'll add 2 historical records for each existing performance (older dates, lower values)
    historical_count = 0
    
    for performance in performances:
        # Extract key data
        athlete_id = performance['athlete_id']
        team_id = performance['team_id']
        metric_name = performance['metric_name']
        current_value = performance['value']
        current_date = performance['recorded_at']
        
        # Determine if this is a metric where lower is better
        lower_is_better = metric_name in ['bowling_average', 'economy_rate']
        
        # Create 2 historical records
        for i in range(2):
            # Historical date (2-6 months ago)
            days_ago = random.randint(60, 180)
            record_date = current_date - timedelta(days=days_ago)
            
            # Historical value (showing improvement over time)
            if lower_is_better:
                # For metrics where lower is better, historical values were higher
                improvement_factor = random.uniform(1.05, 1.2)  # 5-20% worse
                historical_value = current_value * improvement_factor
            else:
                # For metrics where higher is better, historical values were lower
                improvement_factor = random.uniform(0.7, 0.9)  # 10-30% lower
                historical_value = current_value * improvement_factor
            
            # Round values appropriately
            if metric_name in ["wickets_taken", "runs_scored", "boundaries", "catches_taken"]:
                historical_value = max(0, round(historical_value))
            else:
                historical_value = round(historical_value, 2)
            
            # Create historical performance record
            historical_data = {
                "athlete_id": athlete_id,
                "team_id": team_id,
                "metric_name": metric_name,
                "value": historical_value,
                "recorded_by": coach_id,
                "notes": f"Historical record from {record_date.strftime('%Y-%m-%d')}",
                "recorded_at": record_date
            }
            
            # Add to database
            mongo.db.performances.insert_one(historical_data)
            historical_count += 1
            
            # Log progress periodically
            if historical_count % 10 == 0:
                logger.info(f"Added {historical_count} historical records...")
    
    logger.info(f"Added {historical_count} historical performance records")
    return historical_count

def main():
    """Add historical data for better evaluation"""
    try:
        historical_count = add_historical_data()
        logger.info("Historical data successfully added!")
        logger.info("Login with coach@cricket.com / password123 to evaluate athletes")
        
    except Exception as e:
        logger.error(f"Error adding historical data: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()