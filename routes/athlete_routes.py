from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from app import mongo
from models import Team, User, Performance, Notification
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from functools import wraps
import json
from bson import json_util
import logging

athlete_bp = Blueprint('athlete', __name__, url_prefix='/athlete')

# Decorator to check if user is an athlete
def athlete_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'athlete':
            flash('You must be logged in as an athlete to access this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Athlete Dashboard
@athlete_bp.route('/dashboard')
@athlete_required
def dashboard():
    athlete_id = session.get('user_id')
    
    # Get teams the athlete belongs to
    teams = list(mongo.db.teams.find({'athletes': athlete_id}))
    
    # Get recent performances
    performances = Performance.get_athlete_performances(athlete_id)
    
    # Get unread notifications
    notifications = Notification.get_user_notifications(athlete_id)
    unread_count = sum(1 for n in notifications if not n.get('read', False))
    
    return render_template('athlete/dashboard.html', 
                           teams=teams, 
                           performances=performances, 
                           notification_count=unread_count)

# Team Stats
@athlete_bp.route('/team/<team_id>')
@athlete_required
def team_stats(team_id):
    athlete_id = session.get('user_id')
    team = Team.get_team_by_id(team_id)
    
    if not team:
        flash('Team not found', 'danger')
        return redirect(url_for('athlete.dashboard'))
    
    # Check if athlete belongs to this team
    if athlete_id not in team.get('athletes', []):
        flash('You are not a member of this team', 'danger')
        return redirect(url_for('athlete.dashboard'))
    
    # Get all athletes in the team
    athlete_ids = team.get('athletes', [])
    teammates = list(mongo.db.users.find({'_id': {'$in': [ObjectId(aid) for aid in athlete_ids]}}))
    
    # Get team performances
    performances = Performance.get_team_performances(team_id)
    
    # Get metrics
    metrics = team.get('metrics', [])
    
    return render_template('athlete/team_stats.html', 
                           team=team, 
                           teammates=teammates, 
                           performances=performances, 
                           metrics=metrics)

# Athlete Profile
@athlete_bp.route('/profile')
@athlete_required
def profile():
    athlete_id = session.get('user_id')
    athlete = User.find_by_id(athlete_id)
    
    # Get teams the athlete belongs to
    teams = list(mongo.db.teams.find({'athletes': athlete_id}))
    
    # Get all performances
    performances = Performance.get_athlete_performances(athlete_id)
    
    # Group performances by metric
    metrics_performance = {}
    for p in performances:
        metric = p['metric_name']
        if metric not in metrics_performance:
            metrics_performance[metric] = []
        metrics_performance[metric].append(p)
    
    return render_template('athlete/profile.html', 
                           athlete=athlete, 
                           teams=teams, 
                           metrics_performance=metrics_performance)

# Compare with Teammates
@athlete_bp.route('/compare/<team_id>/<metric_name>')
@athlete_required
def compare(team_id, metric_name):
    athlete_id = session.get('user_id')
    team = Team.get_team_by_id(team_id)
    
    if not team:
        flash('Team not found', 'danger')
        return redirect(url_for('athlete.dashboard'))
    
    # Check if athlete belongs to this team
    if athlete_id not in team.get('athletes', []):
        flash('You are not a member of this team', 'danger')
        return redirect(url_for('athlete.dashboard'))
    
    # Find the metric details
    metric = None
    for m in team.get('metrics', []):
        if m['name'] == metric_name:
            metric = m
            break
    
    if not metric:
        flash('Metric not found', 'danger')
        return redirect(url_for('athlete.team_stats', team_id=team_id))
    
    # Get all athletes in the team
    athlete_ids = team.get('athletes', [])
    teammates = list(mongo.db.users.find({'_id': {'$in': [ObjectId(aid) for aid in athlete_ids]}}))
    
    # Get latest performance for each athlete for this metric
    comparison_data = []
    for teammate in teammates:
        teammate_id = str(teammate['_id'])
        latest_perf = mongo.db.performances.find_one({
            'team_id': team_id,
            'athlete_id': teammate_id,
            'metric_name': metric_name
        }, sort=[('recorded_at', -1)])
        
        if latest_perf:
            comparison_data.append({
                'athlete': teammate['username'],
                'value': latest_perf['value'],
                'date': latest_perf['recorded_at'],
                'is_current_user': teammate_id == athlete_id
            })
    
    # Sort by value (descending)
    comparison_data.sort(key=lambda x: x['value'], reverse=True)
    
    return render_template('athlete/compare.html', 
                           team=team, 
                           metric=metric, 
                           comparison_data=comparison_data)

# Performance History (for one metric)
@athlete_bp.route('/history/<team_id>/<metric_name>')
@athlete_required
def performance_history(team_id, metric_name):
    athlete_id = session.get('user_id')
    team = Team.get_team_by_id(team_id)
    
    if not team:
        flash('Team not found', 'danger')
        return redirect(url_for('athlete.dashboard'))
    
    # Check if athlete belongs to this team
    if athlete_id not in team.get('athletes', []):
        flash('You are not a member of this team', 'danger')
        return redirect(url_for('athlete.dashboard'))
    
    # Find the metric details
    metric = None
    for m in team.get('metrics', []):
        if m['name'] == metric_name:
            metric = m
            break
    
    if not metric:
        flash('Metric not found', 'danger')
        return redirect(url_for('athlete.team_stats', team_id=team_id))
    
    # Get all performances for this athlete and metric
    performances = list(mongo.db.performances.find({
        'team_id': team_id,
        'athlete_id': athlete_id,
        'metric_name': metric_name
    }).sort('recorded_at', 1))
    
    return render_template('athlete/history.html', 
                           team=team, 
                           metric=metric, 
                           performances=performances)

# Notifications
@athlete_bp.route('/notifications')
@athlete_required
def notifications():
    athlete_id = session.get('user_id')
    notifications = Notification.get_user_notifications(athlete_id)
    
    return render_template('athlete/notifications.html', notifications=notifications)

# Mark notification as read
@athlete_bp.route('/notifications/mark_read/<notification_id>')
@athlete_required
def mark_notification_read(notification_id):
    Notification.mark_as_read(notification_id)
    return redirect(url_for('athlete.notifications'))

# AJAX endpoint for chart data
@athlete_bp.route('/api/my_performance/<team_id>/<metric_name>')
@athlete_required
def my_performance_data(team_id, metric_name):
    athlete_id = session.get('user_id')
    
    # Get all performances for this metric and athlete
    performances = list(mongo.db.performances.find({
        'team_id': team_id,
        'athlete_id': athlete_id,
        'metric_name': metric_name
    }).sort('recorded_at', 1))
    
    data = []
    for p in performances:
        data.append({
            'date': p['recorded_at'].strftime('%Y-%m-%d'),
            'value': p['value']
        })
    
    return jsonify(data)
