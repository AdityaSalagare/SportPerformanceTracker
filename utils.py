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

def evaluate_athlete(athlete_id, team_id=None):
    """
    Evaluate an athlete's performance and produce a score out of 100.
    This function analyzes historical data to determine the athlete's performance level.
    
    Args:
        athlete_id (str): The ID of the athlete to evaluate
        team_id (str, optional): If provided, evaluate for a specific team
        
    Returns:
        dict: Evaluation results with score and recommendations
    """
    # Get athlete details
    athlete = mongo.db.users.find_one({'_id': ObjectId(athlete_id)})
    if not athlete:
        return {'error': 'Athlete not found'}
    
    # Get all teams the athlete belongs to if team_id not specified
    team_query = {'_id': ObjectId(team_id)} if team_id else {'athletes': athlete_id}
    teams = list(mongo.db.teams.find(team_query))
    
    if not teams:
        return {
            'score': 0,
            'summary': 'No team data available for evaluation',
            'recommendations': ['Add athlete to a team to enable evaluation'],
            'metrics': {},
            'strengths': [],
            'weaknesses': []
        }
    
    all_scores = {}
    metric_details = {}
    metric_weights = {}
    strengths = []
    weaknesses = []
    team_metrics = {}
    
    # Process all teams or the specified team
    for team in teams:
        # Get role information for this athlete on this team (if exists)
        team_id = str(team['_id'])
        athlete_role = None
        
        # Look for athlete role info in team data
        for athlete_data in team.get('athlete_details', []):
            if athlete_data.get('athlete_id') == athlete_id:
                athlete_role = athlete_data.get('role')
                break
        
        # Get team metrics
        metrics = team.get('metrics', [])
        # Store metrics by team
        team_metrics[team_id] = metrics
        
        # Assign weights based on role and metric importance
        for metric in metrics:
            metric_name = metric['name']
            
            # Default weight is 1.0
            weight = 1.0
            
            # Adjust weight based on role if available
            if athlete_role == 'batsman':
                if metric_name in ['batting_average', 'strike_rate', 'runs_scored']:
                    weight = 2.0
                elif metric_name in ['centuries', 'half_centuries']:
                    weight = 1.5
            elif athlete_role == 'bowler':
                if metric_name in ['bowling_average', 'economy_rate', 'wickets_taken']:
                    weight = 2.0
                elif metric_name in ['bowling_speed', 'dot_balls_percentage']:
                    weight = 1.5
            elif athlete_role == 'all_rounder':
                # All-rounders have balanced weights
                if metric_name in ['batting_average', 'bowling_average']:
                    weight = 1.5
            
            # Store weight for this metric
            if team_id not in metric_weights:
                metric_weights[team_id] = {}
            metric_weights[team_id][metric_name] = weight
    
    # Process performance data for each team
    for team_id, metrics in team_metrics.items():
        # Get performances for this athlete in this team
        performances = list(mongo.db.performances.find({
            'athlete_id': athlete_id,
            'team_id': team_id
        }).sort('recorded_at', -1))
        
        if not performances:
            continue
        
        # Group performances by metric
        perf_by_metric = {}
        for perf in performances:
            metric_name = perf['metric_name']
            if metric_name not in perf_by_metric:
                perf_by_metric[metric_name] = []
            perf_by_metric[metric_name].append(perf)
        
        # Calculate score for each metric
        team_scores = {}
        
        for metric in metrics:
            metric_name = metric['name']
            min_value = metric.get('min_value', 0)
            max_value = metric.get('max_value', 100)
            unit = metric.get('unit', '')
            
            # Skip if no performances for this metric
            if metric_name not in perf_by_metric:
                continue
            
            # Get latest performance
            latest_perf = sorted(perf_by_metric[metric_name], key=lambda p: p['recorded_at'], reverse=True)[0]
            current_value = latest_perf['value']
            
            # Get all performances for this metric in the team for context
            team_performances = list(mongo.db.performances.find({
                'team_id': team_id,
                'metric_name': metric_name
            }))
            
            # Calculate team average
            team_values = [p['value'] for p in team_performances]
            team_avg = sum(team_values) / len(team_values) if team_values else 0
            
            # Calculate percentile ranking (higher is better)
            percentile = get_athlete_percentile(athlete_id, team_id, metric_name)
            
            # Normalize to score out of 100 based on metric type
            score = 0
            
            # Metrics where higher is better (batting avg, runs, etc)
            higher_better = [
                'batting_average', 'strike_rate', 'runs_scored', 'centuries', 
                'half_centuries', 'boundaries', 'sixes', 'wickets_taken',
                'bowling_speed', 'dot_balls_percentage', 'maidens'
            ]
            
            # Metrics where lower is better (economy rate, bowling avg)
            lower_better = [
                'economy_rate', 'bowling_average', 'extras_conceded'
            ]
            
            if metric_name in higher_better:
                # For metrics where higher is better
                if max_value > min_value:
                    score = min(100, max(0, ((current_value - min_value) / (max_value - min_value)) * 100))
                else:
                    # Use percentile if min/max not properly defined
                    score = 100 - percentile if percentile is not None else 50
            elif metric_name in lower_better:
                # For metrics where lower is better, inverse the score
                if max_value > min_value:
                    score = min(100, max(0, ((max_value - current_value) / (max_value - min_value)) * 100))
                else:
                    # Use percentile if min/max not properly defined
                    score = percentile if percentile is not None else 50
            else:
                # Default to percentile for other metrics
                score = 100 - percentile if percentile is not None else 50
            
            # Apply weighting factor
            weighted_score = score * metric_weights.get(team_id, {}).get(metric_name, 1.0)
            
            # Store scores and details
            team_scores[metric_name] = weighted_score
            
            # Store metric details for reporting
            metric_details[metric_name] = {
                'name': metric_name,
                'value': current_value,
                'unit': unit,
                'team_avg': team_avg,
                'percentile': percentile,
                'score': score,
                'weighted_score': weighted_score,
                'trend': "improving" if len(perf_by_metric[metric_name]) > 1 and 
                         perf_by_metric[metric_name][0]['value'] > perf_by_metric[metric_name][-1]['value'] else "stable"
            }
            
            # Determine strengths and weaknesses
            if score >= 75:
                strengths.append(metric_name)
            elif score <= 40:
                weaknesses.append(metric_name)
        
        # Store average score for this team
        if team_scores:
            all_scores[team_id] = sum(team_scores.values()) / len(team_scores)
    
    # Calculate overall score across all teams
    overall_score = round(sum(all_scores.values()) / len(all_scores)) if all_scores else 0
    
    # Generate recommendations based on weaknesses
    recommendations = []
    for weakness in weaknesses:
        if weakness == 'batting_average':
            recommendations.append('Focus on batting technique and shot selection')
        elif weakness == 'bowling_average' or weakness == 'economy_rate':
            recommendations.append('Work on bowling accuracy and variation')
        elif weakness == 'bowling_speed':
            recommendations.append('Incorporate strength training to improve bowling speed')
        elif weakness == 'strike_rate':
            recommendations.append('Practice aggressive batting and shot-making')
        elif weakness == 'fielding_accuracy':
            recommendations.append('Dedicate more practice time to fielding drills')
        else:
            recommendations.append(f'Improve {weakness.replace("_", " ")}')
    
    # Generate summary based on overall score
    if overall_score >= 85:
        summary = "Outstanding performer and key team asset"
    elif overall_score >= 70:
        summary = "Strong performer with consistent contributions"
    elif overall_score >= 50:
        summary = "Average performer with potential for improvement"
    elif overall_score >= 30:
        summary = "Below average performer requiring focused development"
    else:
        summary = "Needs significant improvement in multiple areas"
    
    # Return comprehensive evaluation
    return {
        'score': overall_score,
        'summary': summary,
        'recommendations': recommendations[:3],  # Top 3 recommendations
        'metrics': metric_details,
        'strengths': strengths,
        'weaknesses': weaknesses,
        'team_scores': all_scores
    }

def export_team_data_to_excel(team_id):
    """
    Export team performance data to Excel format.
    
    Args:
        team_id (str): The ID of the team
        
    Returns:
        BytesIO: In-memory Excel file
    """
    team = mongo.db.teams.find_one({'_id': ObjectId(team_id)})
    if not team:
        return None
    
    # Create Excel writer
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Get team metrics
        metrics = team.get('metrics', [])
        metric_names = [m['name'] for m in metrics]
        
        # Get team athletes
        athlete_ids = team.get('athletes', [])
        athletes = []
        for athlete_id in athlete_ids:
            athlete = mongo.db.users.find_one({'_id': ObjectId(athlete_id)})
            if athlete:
                athletes.append({
                    'id': str(athlete['_id']),
                    'name': athlete['username'],
                    # Get role if available
                    'role': next((ad['role'] for ad in team.get('athlete_details', []) 
                                if ad.get('athlete_id') == str(athlete['_id'])), 'Unknown')
                })
        
        # Sheet 1: Team Overview
        team_data = {
            'Team Name': [team['name']],
            'Sport': [team['sport']],
            'Number of Athletes': [len(athletes)],
            'Created Date': [team.get('created_at', datetime.now()).strftime('%Y-%m-%d')],
            'Description': [team.get('description', '')]
        }
        df_team = pd.DataFrame(team_data)
        df_team.to_excel(writer, sheet_name='Team Overview', index=False)
        
        # Sheet 2: Athletes
        athlete_data = []
        for athlete in athletes:
            evaluation = evaluate_athlete(athlete['id'], team_id)
            row = {
                'Name': athlete['name'],
                'Role': athlete['role'],
                'Performance Score': evaluation['score'],
                'Evaluation': evaluation['summary'],
                'Key Strengths': ', '.join(evaluation['strengths'][:3]),
                'Areas for Improvement': ', '.join(evaluation['weaknesses'][:3])
            }
            athlete_data.append(row)
        
        df_athletes = pd.DataFrame(athlete_data)
        df_athletes.to_excel(writer, sheet_name='Athletes', index=False)
        
        # Sheet 3: Performance Metrics
        metrics_df = pd.DataFrame([{
            'Metric Name': m['name'],
            'Description': m.get('description', ''),
            'Unit': m.get('unit', ''),
            'Min Value': m.get('min_value', ''),
            'Max Value': m.get('max_value', '')
        } for m in metrics])
        metrics_df.to_excel(writer, sheet_name='Metrics', index=False)
        
        # Sheet 4: Historical Performance Data
        performances = list(mongo.db.performances.find({
            'team_id': team_id
        }).sort('recorded_at', -1))
        
        if performances:
            perf_data = []
            for p in performances:
                athlete = next((a for a in athletes if a['id'] == p['athlete_id']), None)
                perf_data.append({
                    'Date': p['recorded_at'].strftime('%Y-%m-%d'),
                    'Athlete': athlete['name'] if athlete else 'Unknown',
                    'Role': athlete['role'] if athlete else 'Unknown',
                    'Metric': p['metric_name'],
                    'Value': p['value'],
                    'Notes': p.get('notes', '')
                })
            
            df_performances = pd.DataFrame(perf_data)
            df_performances.to_excel(writer, sheet_name='Performance History', index=False)
            
            # Sheet 5: Metric Summaries (one metric per sheet)
            for metric_name in metric_names:
                # Filter performances for this metric
                metric_perfs = [p for p in performances if p['metric_name'] == metric_name]
                if not metric_perfs:
                    continue
                
                # Group by athlete
                athlete_perfs = {}
                for p in metric_perfs:
                    athlete_id = p['athlete_id']
                    if athlete_id not in athlete_perfs:
                        athlete_perfs[athlete_id] = []
                    athlete_perfs[athlete_id].append(p)
                
                # Create summary data
                summary_data = []
                for athlete_id, perfs in athlete_perfs.items():
                    athlete = next((a for a in athletes if a['id'] == athlete_id), None)
                    # Get latest, min, max and avg values
                    values = [p['value'] for p in perfs]
                    latest = sorted(perfs, key=lambda p: p['recorded_at'], reverse=True)[0]['value']
                    
                    summary_data.append({
                        'Athlete': athlete['name'] if athlete else 'Unknown',
                        'Role': athlete['role'] if athlete else 'Unknown',
                        'Latest Value': latest,
                        'Average': sum(values) / len(values),
                        'Min': min(values),
                        'Max': max(values),
                        'Measurements': len(values)
                    })
                
                df_summary = pd.DataFrame(summary_data)
                safe_name = metric_name.replace(' ', '_')[:25]  # Excel sheet names have limits
                df_summary.to_excel(writer, sheet_name=f'Metric_{safe_name}', index=False)
    
    # Reset pointer and return
    output.seek(0)
    return output

def export_athlete_data_to_excel(athlete_id):
    """
    Export athlete performance data to Excel format.
    
    Args:
        athlete_id (str): The ID of the athlete
        
    Returns:
        BytesIO: In-memory Excel file
    """
    athlete = mongo.db.users.find_one({'_id': ObjectId(athlete_id)})
    if not athlete:
        return None
    
    # Create Excel writer
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Get teams the athlete belongs to
        teams = list(mongo.db.teams.find({'athletes': athlete_id}))
        
        # Sheet 1: Athlete Overview
        athlete_data = {
            'Name': [athlete['username']],
            'Email': [athlete['email']],
            'Role': ['Athlete'],
            'Number of Teams': [len(teams)],
            'Created Date': [athlete.get('created_at', datetime.now()).strftime('%Y-%m-%d')]
        }
        df_athlete = pd.DataFrame(athlete_data)
        df_athlete.to_excel(writer, sheet_name='Athlete Overview', index=False)
        
        # Sheet 2: Teams
        if teams:
            team_data = []
            for team in teams:
                # Get role if available
                role = next((ad['role'] for ad in team.get('athlete_details', []) 
                          if ad.get('athlete_id') == str(athlete['_id'])), 'Unknown')
                
                # Get performances for this athlete in this team
                performances = list(mongo.db.performances.find({
                    'athlete_id': athlete_id,
                    'team_id': str(team['_id'])
                }))
                
                team_data.append({
                    'Team Name': team['name'],
                    'Sport': team['sport'],
                    'Role': role,
                    'Number of Metrics': len(team.get('metrics', [])),
                    'Total Performances': len(performances)
                })
            
            df_teams = pd.DataFrame(team_data)
            df_teams.to_excel(writer, sheet_name='Teams', index=False)
        
        # Sheet 3: Performance Evaluation
        evaluation = evaluate_athlete(athlete_id)
        eval_data = {
            'Overall Score': [evaluation['score']],
            'Summary': [evaluation['summary']],
            'Key Strengths': [', '.join(evaluation['strengths'][:3])],
            'Areas for Improvement': [', '.join(evaluation['weaknesses'][:3])],
            'Recommendations': ['\n'.join(evaluation['recommendations'])]
        }
        
        # Add team-specific scores
        for team_id, score in evaluation.get('team_scores', {}).items():
            team = next((t for t in teams if str(t['_id']) == team_id), None)
            if team:
                eval_data[f'Score in {team["name"]}'] = [score]
        
        df_evaluation = pd.DataFrame(eval_data)
        df_evaluation.to_excel(writer, sheet_name='Performance Evaluation', index=False)
        
        # Sheet 4: All Performance Data
        performances = list(mongo.db.performances.find({
            'athlete_id': athlete_id
        }).sort('recorded_at', -1))
        
        if performances:
            perf_data = []
            for p in performances:
                team = next((t for t in teams if str(t['_id']) == p['team_id']), None)
                perf_data.append({
                    'Date': p['recorded_at'].strftime('%Y-%m-%d'),
                    'Team': team['name'] if team else 'Unknown',
                    'Metric': p['metric_name'],
                    'Value': p['value'],
                    'Notes': p.get('notes', '')
                })
            
            df_performances = pd.DataFrame(perf_data)
            df_performances.to_excel(writer, sheet_name='Performance History', index=False)
            
            # Sheet 5: Metric Progress Over Time
            # Group by team and metric
            team_metric_perfs = {}
            for p in performances:
                key = (p['team_id'], p['metric_name'])
                if key not in team_metric_perfs:
                    team_metric_perfs[key] = []
                team_metric_perfs[key].append(p)
            
            progress_data = []
            for (team_id, metric_name), perfs in team_metric_perfs.items():
                team = next((t for t in teams if str(t['_id']) == team_id), None)
                
                # Sort by date
                sorted_perfs = sorted(perfs, key=lambda p: p['recorded_at'])
                
                # Calculate progress
                if len(sorted_perfs) >= 2:
                    first_value = sorted_perfs[0]['value']
                    last_value = sorted_perfs[-1]['value']
                    change = last_value - first_value
                    change_pct = (change / first_value) * 100 if first_value != 0 else 0
                    
                    progress_data.append({
                        'Team': team['name'] if team else 'Unknown',
                        'Metric': metric_name,
                        'First Measurement': sorted_perfs[0]['recorded_at'].strftime('%Y-%m-%d'),
                        'First Value': first_value,
                        'Latest Measurement': sorted_perfs[-1]['recorded_at'].strftime('%Y-%m-%d'),
                        'Latest Value': last_value,
                        'Change': change,
                        'Change %': f"{change_pct:.2f}%",
                        'Measurements': len(sorted_perfs)
                    })
            
            if progress_data:
                df_progress = pd.DataFrame(progress_data)
                df_progress.to_excel(writer, sheet_name='Metric Progress', index=False)
    
    # Reset pointer and return
    output.seek(0)
    return output
