from datetime import datetime
import pandas as pd
import io
from app import mongo
from bson.objectid import ObjectId
import json
from bson import json_util

def parse_json(data):
    """Convert MongoDB data to JSON serializable format"""
    return json.loads(json_util.dumps(data))

def generate_performance_report(team_id, date_from=None, date_to=None):
    """Generate performance report data for a team"""
    if not date_from:
        date_from = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if not date_to:
        date_to = datetime.now()
    
    # Query performances for the team within date range
    query = {
        'team_id': team_id,
        'recorded_at': {'$gte': date_from, '$lte': date_to}
    }
    
    performances = list(mongo.db.performances.find(query).sort('recorded_at', 1))
    
    if not performances:
        return None
    
    # Process data for CSV export
    data = []
    for p in performances:
        athlete = mongo.db.users.find_one({'_id': ObjectId(p['athlete_id'])})
        data.append({
            'Date': p['recorded_at'].strftime('%Y-%m-%d'),
            'Athlete': athlete['username'] if athlete else 'Unknown',
            'Metric': p['metric_name'],
            'Value': p['value'],
            'Notes': p.get('notes', '')
        })
    
    return pd.DataFrame(data)

def calculate_team_averages(team_id):
    """Calculate average performance for each metric in the team"""
    team = mongo.db.teams.find_one({'_id': ObjectId(team_id)})
    if not team:
        return {}
    
    metrics = team.get('metrics', [])
    results = {}
    
    for metric in metrics:
        metric_name = metric['name']
        performances = list(mongo.db.performances.find({
            'team_id': team_id,
            'metric_name': metric_name
        }))
        
        if performances:
            values = [p['value'] for p in performances]
            results[metric_name] = {
                'avg': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'unit': metric['unit']
            }
    
    return results

def get_athlete_percentile(athlete_id, team_id, metric_name):
    """Calculate percentile of athlete within team for a specific metric"""
    # Get all performances for this metric in the team
    all_performances = {}
    performances = list(mongo.db.performances.find({
        'team_id': team_id,
        'metric_name': metric_name
    }))
    
    # Group latest performance by athlete
    for p in performances:
        athlete_id_key = p['athlete_id']
        if athlete_id_key not in all_performances or p['recorded_at'] > all_performances[athlete_id_key]['recorded_at']:
            all_performances[athlete_id_key] = p
    
    if not all_performances:
        return None
    
    # Get values and sort
    values = [p['value'] for p in all_performances.values()]
    values.sort()
    
    # Get latest performance for our athlete
    athlete_performance = all_performances.get(athlete_id)
    if not athlete_performance:
        return None
    
    # Calculate percentile
    athlete_value = athlete_performance['value']
    rank = values.index(athlete_value)
    percentile = (rank / len(values)) * 100
    
    return percentile

def detect_performance_milestones(performances, threshold_pct=10):
    """Detect significant improvements in performance"""
    if not performances or len(performances) < 2:
        return []
    
    # Sort by date
    sorted_perfs = sorted(performances, key=lambda p: p['recorded_at'])
    
    milestones = []
    prev_value = sorted_perfs[0]['value']
    
    for p in sorted_perfs[1:]:
        current_value = p['value']
        change_pct = ((current_value - prev_value) / prev_value) * 100
        
        if abs(change_pct) >= threshold_pct:
            milestones.append({
                'date': p['recorded_at'],
                'metric': p['metric_name'],
                'old_value': prev_value,
                'new_value': current_value,
                'change_pct': change_pct
            })
        
        prev_value = current_value
    
    return milestones
