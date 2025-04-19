from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify, send_file, Response
from app import mongo
from models import Team, User, Performance, Notification
from forms import TeamForm, MetricForm, AthleteForm, PerformanceForm, ReportForm
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import pandas as pd
import io
import base64
from functools import wraps
import json
from bson import json_util
import logging
from utils import evaluate_athlete, export_team_data_to_excel, export_athlete_data_to_excel

coach_bp = Blueprint('coach', __name__, url_prefix='/coach')

# Decorator to check if user is a coach
def coach_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'coach':
            flash('You must be logged in as a coach to access this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Coach Dashboard
@coach_bp.route('/dashboard')
@coach_required
def dashboard():
    coach_id = session.get('user_id')
    teams = Team.get_teams_by_coach(coach_id)
    
    # Get notification count
    notifications = mongo.db.notifications.count_documents({
        'user_id': coach_id,
        'read': False
    })
    
    # Performance summary
    recent_performances = list(mongo.db.performances.find({
        'recorded_by': coach_id
    }).sort('recorded_at', -1).limit(5))
    
    # Athletes count
    athlete_count = mongo.db.users.count_documents({'role': 'athlete'})
    
    return render_template('coach/dashboard.html', 
                           teams=teams, 
                           notifications=notifications,
                           recent_performances=recent_performances,
                           athlete_count=athlete_count)

# Manage Teams
@coach_bp.route('/teams', methods=['GET', 'POST'])
@coach_required
def manage_teams():
    form = TeamForm()
    coach_id = session.get('user_id')
    
    if form.validate_on_submit():
        team_id = Team.create_team(
            name=form.name.data,
            coach_id=coach_id,
            sport=form.sport.data,
            description=form.description.data
        )
        flash(f'Team {form.name.data} has been created!', 'success')
        return redirect(url_for('coach.manage_teams'))
    
    teams = Team.get_teams_by_coach(coach_id)
    return render_template('coach/manage_teams.html', form=form, teams=teams)

# Team Details
@coach_bp.route('/team/<team_id>')
@coach_required
def team_detail(team_id):
    team = Team.get_team_by_id(team_id)
    if not team:
        flash('Team not found', 'danger')
        return redirect(url_for('coach.manage_teams'))
    
    # Get athletes in team
    athlete_ids = team.get('athletes', [])
    athletes = list(mongo.db.users.find({'_id': {'$in': [ObjectId(aid) for aid in athlete_ids]}}))
    
    # Get performances for this team
    performances = Performance.get_team_performances(team_id)
    
    return render_template('coach/team_detail.html', 
                           team=team, 
                           athletes=athletes, 
                           performances=performances)

# Manage Metrics
@coach_bp.route('/team/<team_id>/metrics', methods=['GET', 'POST'])
@coach_required
def manage_metrics(team_id):
    team = Team.get_team_by_id(team_id)
    if not team:
        flash('Team not found', 'danger')
        return redirect(url_for('coach.manage_teams'))
    
    form = MetricForm()
    if form.validate_on_submit():
        Team.add_metric_to_team(
            team_id=team_id,
            metric_name=form.name.data,
            metric_description=form.description.data,
            metric_unit=form.unit.data,
            min_value=form.min_value.data,
            max_value=form.max_value.data
        )
        flash(f'Metric {form.name.data} has been added!', 'success')
        return redirect(url_for('coach.manage_metrics', team_id=team_id))
    
    metrics = team.get('metrics', [])
    return render_template('coach/manage_metrics.html', 
                           team=team, 
                           form=form, 
                           metrics=metrics)

# Add Athlete to Team
@coach_bp.route('/team/<team_id>/add_athlete', methods=['GET', 'POST'])
@coach_required
def add_athlete(team_id):
    team = Team.get_team_by_id(team_id)
    if not team:
        flash('Team not found', 'danger')
        return redirect(url_for('coach.manage_teams'))
    
    form = AthleteForm()
    # Get all athletes (for dropdown)
    athletes = list(mongo.db.users.find({'role': 'athlete'}))
    athlete_list = [(str(a['_id']), a['username']) for a in athletes]
    form.athlete_id.choices = athlete_list
    
    if form.validate_on_submit():
        athlete_id = form.athlete_id.data
        result = Team.add_athlete_to_team(team_id, athlete_id)
        if result:
            # Create notification for athlete
            Notification.create_notification(
                user_id=athlete_id,
                message=f"You have been added to the team '{team['name']}'",
                notification_type="team_addition",
                related_id=team_id
            )
            flash('Athlete added to team successfully!', 'success')
        else:
            flash('Failed to add athlete to team', 'danger')
        return redirect(url_for('coach.team_detail', team_id=team_id))
    
    return render_template('coach/add_athlete.html', 
                           team=team, 
                           form=form)

# Record Performance
@coach_bp.route('/team/<team_id>/record_performance', methods=['GET', 'POST'])
@coach_required
def record_performance(team_id):
    team = Team.get_team_by_id(team_id)
    if not team:
        flash('Team not found', 'danger')
        return redirect(url_for('coach.manage_teams'))
    
    form = PerformanceForm()
    
    # Get athletes for this team
    athlete_ids = team.get('athletes', [])
    athletes = list(mongo.db.users.find({'_id': {'$in': [ObjectId(aid) for aid in athlete_ids]}}))
    form.athlete_id.choices = [(str(a['_id']), a['username']) for a in athletes]
    
    # Get metrics for this team
    metrics = team.get('metrics', [])
    form.metric_name.choices = [(m['name'], m['name']) for m in metrics]
    
    if form.validate_on_submit():
        performance_id = Performance.record_performance(
            athlete_id=form.athlete_id.data,
            team_id=team_id,
            metric_name=form.metric_name.data,
            value=form.value.data,
            recorded_by=session.get('user_id'),
            notes=form.notes.data
        )
        
        # Create notification for athlete
        Notification.create_notification(
            user_id=form.athlete_id.data,
            message=f"New performance recorded for '{form.metric_name.data}'",
            notification_type="performance_update",
            related_id=performance_id
        )
        
        flash('Performance recorded successfully!', 'success')
        return redirect(url_for('coach.team_detail', team_id=team_id))
    
    return render_template('coach/record_performance.html', 
                           team=team, 
                           form=form, 
                           metrics=metrics)

# Athlete Detail
@coach_bp.route('/athlete/<athlete_id>')
@coach_required
def athlete_detail(athlete_id):
    athlete = User.find_by_id(athlete_id)
    if not athlete:
        flash('Athlete not found', 'danger')
        return redirect(url_for('coach.dashboard'))
    
    # Get performances for this athlete
    performances = Performance.get_athlete_performances(athlete_id)
    
    # Get teams this athlete belongs to
    teams = list(mongo.db.teams.find({'athletes': athlete_id}))
    
    return render_template('coach/athlete_detail.html', 
                           athlete=athlete, 
                           performances=performances, 
                           teams=teams)

# Reports
@coach_bp.route('/reports', methods=['GET', 'POST'])
@coach_required
def reports():
    form = ReportForm()
    coach_id = session.get('user_id')
    
    # Get teams for dropdown
    teams = Team.get_teams_by_coach(coach_id)
    form.team_id.choices = [(str(t['_id']), t['name']) for t in teams]
    
    if form.validate_on_submit():
        team_id = form.team_id.data
        report_type = form.report_type.data
        date_from = form.date_from.data or datetime.now() - timedelta(days=30)
        date_to = form.date_to.data or datetime.now()
        
        # Generate report data
        team = Team.get_team_by_id(team_id)
        if report_type == 'team_performance':
            performances = list(mongo.db.performances.find({
                'team_id': team_id,
                'recorded_at': {'$gte': date_from, '$lte': date_to}
            }).sort('recorded_at', 1))
            
            # Convert to DataFrame for easier processing
            if performances:
                data = []
                for p in performances:
                    athlete = User.find_by_id(p['athlete_id'])
                    data.append({
                        'Date': p['recorded_at'].strftime('%Y-%m-%d'),
                        'Athlete': athlete['username'],
                        'Metric': p['metric_name'],
                        'Value': p['value'],
                        'Notes': p['notes']
                    })
                
                df = pd.DataFrame(data)
                csv_data = df.to_csv(index=False)
                return render_template('coach/report_result.html', 
                                    team=team,
                                    report_type=report_type,
                                    date_from=date_from,
                                    date_to=date_to,
                                    csv_data=base64.b64encode(csv_data.encode()).decode(),
                                    performances=performances)
        
        elif report_type == 'athlete_comparison':
            # Get athletes in team
            athlete_ids = team.get('athletes', [])
            athletes = list(mongo.db.users.find({'_id': {'$in': [ObjectId(aid) for aid in athlete_ids]}}))
            
            # Get metrics for this team
            metrics = team.get('metrics', [])
            
            comparison_data = {}
            for metric in metrics:
                metric_name = metric['name']
                comparison_data[metric_name] = {}
                
                for athlete in athletes:
                    athlete_id = str(athlete['_id'])
                    athlete_name = athlete['username']
                    
                    # Get latest performance for this metric and athlete
                    perf = mongo.db.performances.find_one({
                        'team_id': team_id,
                        'athlete_id': athlete_id,
                        'metric_name': metric_name,
                        'recorded_at': {'$gte': date_from, '$lte': date_to}
                    }, sort=[('recorded_at', -1)])
                    
                    if perf:
                        comparison_data[metric_name][athlete_name] = perf['value']
                    else:
                        comparison_data[metric_name][athlete_name] = 'N/A'
            
            return render_template('coach/report_result.html', 
                                team=team,
                                report_type=report_type,
                                date_from=date_from,
                                date_to=date_to,
                                comparison_data=comparison_data,
                                athletes=athletes,
                                metrics=metrics)
    
    return render_template('coach/reports.html', form=form, teams=teams)

# Add Cricket Metrics
@coach_bp.route('/team/<team_id>/add_cricket_metrics')
@coach_required
def add_cricket_metrics(team_id):
    team = Team.get_team_by_id(team_id)
    if not team:
        flash('Team not found', 'danger')
        return redirect(url_for('coach.manage_teams'))
    
    # Add cricket metrics
    Team.add_cricket_metrics(team_id)
    flash('Cricket metrics have been added to the team!', 'success')
    return redirect(url_for('coach.manage_metrics', team_id=team_id))

# Update athlete role (ajax endpoint)
@coach_bp.route('/api/update_athlete_role', methods=['POST'])
@coach_required
def update_athlete_role():
    data = request.json
    team_id = data.get('team_id')
    athlete_id = data.get('athlete_id')
    role = data.get('role')
    
    if not team_id or not athlete_id or not role:
        return jsonify({'success': False, 'message': 'Missing required data'})
    
    # Update role
    Team.update_athlete_role(team_id, athlete_id, role)
    return jsonify({'success': True})

# Athlete Evaluation
@coach_bp.route('/athlete/<athlete_id>/evaluate', methods=['GET'])
@coach_required
def evaluate_athlete_view(athlete_id):
    athlete = User.find_by_id(athlete_id)
    if not athlete:
        flash('Athlete not found', 'danger')
        return redirect(url_for('coach.dashboard'))
    
    # Get teams this athlete belongs to
    teams = list(mongo.db.teams.find({'athletes': athlete_id}))
    
    # Get team_id from query parameter if available
    team_id = request.args.get('team_id')
    
    # Run evaluation
    evaluation = evaluate_athlete(athlete_id, team_id)
    
    return render_template('coach/athlete_evaluation.html', 
                          athlete=athlete,
                          teams=teams,
                          evaluation=evaluation,
                          current_team_id=team_id)

# Team Excel Export
@coach_bp.route('/team/<team_id>/export_excel')
@coach_required
def export_team_excel(team_id):
    team = Team.get_team_by_id(team_id)
    if not team:
        flash('Team not found', 'danger')
        return redirect(url_for('coach.manage_teams'))
    
    # Generate Excel file
    excel_bytes = export_team_data_to_excel(team_id)
    if not excel_bytes:
        flash('Failed to generate Excel report', 'danger')
        return redirect(url_for('coach.team_detail', team_id=team_id))
    
    # Send file
    filename = f"{team['name'].replace(' ', '_')}_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return send_file(
        excel_bytes,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# Athlete Excel Export
@coach_bp.route('/athlete/<athlete_id>/export_excel')
@coach_required
def export_athlete_excel(athlete_id):
    athlete = User.find_by_id(athlete_id)
    if not athlete:
        flash('Athlete not found', 'danger')
        return redirect(url_for('coach.dashboard'))
    
    # Generate Excel file
    excel_bytes = export_athlete_data_to_excel(athlete_id)
    if not excel_bytes:
        flash('Failed to generate Excel report', 'danger')
        return redirect(url_for('coach.athlete_detail', athlete_id=athlete_id))
    
    # Send file
    filename = f"{athlete['username'].replace(' ', '_')}_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return send_file(
        excel_bytes,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# AJAX endpoint for chart data
@coach_bp.route('/api/performance_data/<team_id>/<metric_name>')
@coach_required
def performance_data(team_id, metric_name):
    performances = Performance.get_metric_performances(team_id, metric_name)
    data = []
    
    for p in performances:
        athlete = User.find_by_id(p['athlete_id'])
        data.append({
            'date': p['recorded_at'].strftime('%Y-%m-%d'),
            'athlete': athlete['username'],
            'value': p['value']
        })
    
    return jsonify(data)

# AJAX endpoint for athlete score data
@coach_bp.route('/api/athlete_evaluation/<athlete_id>')
@coach_required
def athlete_evaluation_data(athlete_id):
    team_id = request.args.get('team_id')
    evaluation = evaluate_athlete(athlete_id, team_id)
    return jsonify(evaluation)

# Notifications
@coach_bp.route('/notifications')
@coach_required
def notifications():
    coach_id = session.get('user_id')
    notifications = Notification.get_user_notifications(coach_id)
    
    return render_template('coach/notifications.html', notifications=notifications)

# Mark notification as read
@coach_bp.route('/notifications/mark_read/<notification_id>')
@coach_required
def mark_notification_read(notification_id):
    Notification.mark_as_read(notification_id)
    return redirect(url_for('coach.notifications'))
