from app import mongo
from datetime import datetime
import json
from bson import json_util
from bson.objectid import ObjectId

class User:
    @staticmethod
    def find_by_email(email):
        return mongo.db.users.find_one({"email": email})
    
    @staticmethod
    def find_by_id(user_id):
        return mongo.db.users.find_one({"_id": ObjectId(user_id)})
    
    @staticmethod
    def create_user(username, email, password_hash, role):
        user_data = {
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "created_at": datetime.now()
        }
        result = mongo.db.users.insert_one(user_data)
        return str(result.inserted_id)

class Team:
    @staticmethod
    def create_team(name, coach_id, sport, description=""):
        team_data = {
            "name": name,
            "coach_id": coach_id,
            "sport": sport,
            "description": description,
            "created_at": datetime.now(),
            "athletes": [],
            "metrics": [],
            "athlete_details": []  # For storing roles and additional player info
        }
        result = mongo.db.teams.insert_one(team_data)
        return str(result.inserted_id)
    
    @staticmethod
    def get_teams_by_coach(coach_id):
        """Get teams by coach ID, or all teams if no teams found for the coach"""
        teams = list(mongo.db.teams.find({"coach_id": coach_id}))
        if not teams:
            logging.warning(f"No teams found for coach ID: {coach_id}, showing all teams")
            teams = list(mongo.db.teams.find())
        return teams
    
    @staticmethod
    def get_team_by_id(team_id):
        return mongo.db.teams.find_one({"_id": ObjectId(team_id)})
    
    @staticmethod
    def add_athlete_to_team(team_id, athlete_id, role=None):
        team = mongo.db.teams.find_one({"_id": ObjectId(team_id)})
        if team and athlete_id not in team.get('athletes', []):
            # Add athlete to team
            mongo.db.teams.update_one(
                {"_id": ObjectId(team_id)},
                {"$push": {"athletes": athlete_id}}
            )
            
            # If role is provided, add athlete details
            if role:
                athlete_detail = {
                    "athlete_id": athlete_id,
                    "role": role,
                    "added_at": datetime.now()
                }
                mongo.db.teams.update_one(
                    {"_id": ObjectId(team_id)},
                    {"$push": {"athlete_details": athlete_detail}}
                )
            return True
        return False
    
    @staticmethod
    def update_athlete_role(team_id, athlete_id, role):
        """Update an athlete's role within a team"""
        # Check if athlete is already in team with a role
        team = mongo.db.teams.find_one({
            "_id": ObjectId(team_id),
            "athlete_details.athlete_id": athlete_id
        })
        
        if team:
            # Update existing role
            mongo.db.teams.update_one(
                {
                    "_id": ObjectId(team_id), 
                    "athlete_details.athlete_id": athlete_id
                },
                {"$set": {"athlete_details.$.role": role}}
            )
        else:
            # Check if athlete is in the team without role details
            team = mongo.db.teams.find_one({
                "_id": ObjectId(team_id),
                "athletes": athlete_id
            })
            
            if team:
                # Add new role details
                athlete_detail = {
                    "athlete_id": athlete_id,
                    "role": role,
                    "added_at": datetime.now()
                }
                mongo.db.teams.update_one(
                    {"_id": ObjectId(team_id)},
                    {"$push": {"athlete_details": athlete_detail}}
                )
        
        return True
        
    @staticmethod
    def add_metric_to_team(team_id, metric_name, metric_description, metric_unit, min_value=0, max_value=100):
        metric = {
            "name": metric_name,
            "description": metric_description,
            "unit": metric_unit,
            "min_value": min_value,
            "max_value": max_value,
            "created_at": datetime.now()
        }
        mongo.db.teams.update_one(
            {"_id": ObjectId(team_id)},
            {"$push": {"metrics": metric}}
        )
        return True
    
    @staticmethod
    def add_cricket_metrics(team_id):
        """Add standard cricket metrics to a team"""
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
            {
                "name": "centuries",
                "description": "Number of innings with 100+ runs",
                "unit": "count",
                "min_value": 0,
                "max_value": 50,
                "created_at": datetime.now()
            },
            {
                "name": "half_centuries",
                "description": "Number of innings with 50-99 runs",
                "unit": "count",
                "min_value": 0,
                "max_value": 100,
                "created_at": datetime.now()
            },
            {
                "name": "boundaries",
                "description": "Number of 4s hit",
                "unit": "count",
                "min_value": 0,
                "max_value": 50,
                "created_at": datetime.now()
            },
            {
                "name": "sixes",
                "description": "Number of 6s hit",
                "unit": "count",
                "min_value": 0,
                "max_value": 30,
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
            },
            {
                "name": "dot_balls_percentage",
                "description": "Percentage of deliveries with no runs scored",
                "unit": "%",
                "min_value": 0,
                "max_value": 100,
                "created_at": datetime.now()
            },
            {
                "name": "maidens",
                "description": "Number of overs with no runs conceded",
                "unit": "count",
                "min_value": 0,
                "max_value": 10,
                "created_at": datetime.now()
            },
            {
                "name": "extras_conceded",
                "description": "Number of extra runs conceded (wides, no-balls)",
                "unit": "runs",
                "min_value": 0,
                "max_value": 30,
                "created_at": datetime.now()
            },
            
            # Fielding metrics
            {
                "name": "catches_taken",
                "description": "Number of catches taken",
                "unit": "count",
                "min_value": 0,
                "max_value": 10,
                "created_at": datetime.now()
            },
            {
                "name": "run_outs",
                "description": "Number of run outs executed",
                "unit": "count",
                "min_value": 0,
                "max_value": 5,
                "created_at": datetime.now()
            },
            {
                "name": "fielding_accuracy",
                "description": "Accuracy of throws and fielding",
                "unit": "%",
                "min_value": 0,
                "max_value": 100,
                "created_at": datetime.now()
            }
        ]
        
        # Add all cricket metrics to the team
        mongo.db.teams.update_one(
            {"_id": ObjectId(team_id)},
            {"$push": {"metrics": {"$each": cricket_metrics}}}
        )
        
        return True
    
    @staticmethod
    def get_athlete_role(team_id, athlete_id):
        """Get an athlete's role within a team"""
        team = mongo.db.teams.find_one({"_id": ObjectId(team_id)})
        if not team:
            return None
        
        for athlete_detail in team.get('athlete_details', []):
            if athlete_detail.get('athlete_id') == athlete_id:
                return athlete_detail.get('role')
        
        return None
    
    @staticmethod
    def get_team_roles():
        """Get list of cricket player roles"""
        return [
            "batsman", 
            "bowler", 
            "all_rounder", 
            "wicket_keeper", 
            "captain"
        ]

class Performance:
    @staticmethod
    def record_performance(athlete_id, team_id, metric_name, value, recorded_by, notes=""):
        performance_data = {
            "athlete_id": athlete_id,
            "team_id": team_id,
            "metric_name": metric_name,
            "value": value,
            "recorded_by": recorded_by,
            "notes": notes,
            "recorded_at": datetime.now()
        }
        result = mongo.db.performances.insert_one(performance_data)
        return str(result.inserted_id)
    
    @staticmethod
    def get_athlete_performances(athlete_id, team_id=None):
        query = {"athlete_id": athlete_id}
        if team_id:
            query["team_id"] = team_id
        return list(mongo.db.performances.find(query).sort("recorded_at", -1))
    
    @staticmethod
    def get_team_performances(team_id):
        return list(mongo.db.performances.find({"team_id": team_id}).sort("recorded_at", -1))
    
    @staticmethod
    def get_metric_performances(team_id, metric_name):
        return list(mongo.db.performances.find(
            {"team_id": team_id, "metric_name": metric_name}
        ).sort("recorded_at", -1))

class Notification:
    @staticmethod
    def create_notification(user_id, message, notification_type, related_id=None):
        notification_data = {
            "user_id": user_id,
            "message": message,
            "type": notification_type,
            "related_id": related_id,
            "read": False,
            "created_at": datetime.now()
        }
        result = mongo.db.notifications.insert_one(notification_data)
        return str(result.inserted_id)
    
    @staticmethod
    def get_user_notifications(user_id, limit=10):
        return list(mongo.db.notifications.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(limit))
    
    @staticmethod
    def mark_as_read(notification_id):
        mongo.db.notifications.update_one(
            {"_id": ObjectId(notification_id)},
            {"$set": {"read": True}}
        )
        return True
