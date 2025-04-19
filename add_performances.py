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
    """Record performances for athletes"""
    logger.info("Recording performance data...")
    
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
    
    # Define date range (last 3 months)
    end_date = datetime.now()
    
    # Metric ranges based on role
    metric_ranges = {
        "batsman": {
            "batting_average": (30, 60),
            "strike_rate": (120, 180),
            "runs_scored": (30, 120)
        },
        "bowler": {
            "bowling_average": (15, 30),
            "economy_rate": (4, 8),
            "bowling_speed": (130, 150),
            "wickets_taken": (1, 5)
        },
        "all_rounder": {
            "batting_average": (25, 45),
            "bowling_average": (20, 35),
            "runs_scored": (20, 80),
            "wickets_taken": (1, 3)
        },
        "wicket_keeper": {
            "batting_average": (25, 50),
            "strike_rate": (110, 150),
            "runs_scored": (20, 60)
        },
        "captain": {
            "batting_average": (35, 60),
            "strike_rate": (110, 160),
            "runs_scored": (40, 100)
        }
    }
    
    # All athletes get these generic metrics
    generic_metrics = ["batting_average", "bowling_average"]
    
    performance_count = 0
    
    # Record performances
    for athlete_id, team_assignments in assignments.items():
        for team_id, role in team_assignments:
            # Determine metrics to record based on role
            metrics_to_record = generic_metrics.copy()
            
            # Add role-specific metrics
            if role in metric_ranges:
                for metric in metric_ranges[role]:
                    if metric not in metrics_to_record:
                        metrics_to_record.append(metric)
            
            # Create performance records
            for metric_name in metrics_to_record:
                # Determine value range
                min_val = 0
                max_val = 100
                
                # Use role-specific ranges if available
                if role in metric_ranges and metric_name in metric_ranges[role]:
                    min_val, max_val = metric_ranges[role][metric_name]
                
                # Create 3 records to show progression
                for i in range(3):
                    # Dates: 60, 30, and 10 days ago
                    days_ago = 60 - (i * 25)
                    record_date = end_date - timedelta(days=days_ago)
                    
                    # Determine value with progression
                    if metric_name in ["bowling_average", "economy_rate"]:
                        # Lower is better
                        base_value = random.uniform(min_val, max_val)
                        improvement = 0.95 ** i  # 5% improvement
                        value = base_value * improvement
                    else:
                        # Higher is better
                        base_value = random.uniform(min_val, max_val * 0.7)
                        improvement = 1.1 ** i  # 10% improvement
                        value = base_value * improvement
                    
                    # Round values appropriately
                    if metric_name in ["wickets_taken", "runs_scored"]:
                        value = round(value)
                    else:
                        value = round(value, 2)
                    
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
                    
                    mongo.db.performances.insert_one(perf_data)
                    performance_count += 1
                    
                    if performance_count % 10 == 0:
                        logger.info(f"Recorded {performance_count} performances...")
    
    logger.info(f"Total performances recorded: {performance_count}")
    return performance_count

def main():
    """Record performances"""
    try:
        # Record performances
        performance_count = record_performances()
        logger.info("Performance data successfully recorded!")
        logger.info("Login with coach@cricket.com / password123 to view the data")
        
    except Exception as e:
        logger.error(f"Error recording performances: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()