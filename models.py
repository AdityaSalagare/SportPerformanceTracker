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
            "password": password_hash,
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
            "metrics": []
        }
        result = mongo.db.teams.insert_one(team_data)
        return str(result.inserted_id)
    
    @staticmethod
    def get_teams_by_coach(coach_id):
        return list(mongo.db.teams.find({"coach_id": coach_id}))
    
    @staticmethod
    def get_team_by_id(team_id):
        return mongo.db.teams.find_one({"_id": ObjectId(team_id)})
    
    @staticmethod
    def add_athlete_to_team(team_id, athlete_id):
        team = mongo.db.teams.find_one({"_id": ObjectId(team_id)})
        if team and athlete_id not in team.get('athletes', []):
            mongo.db.teams.update_one(
                {"_id": ObjectId(team_id)},
                {"$push": {"athletes": athlete_id}}
            )
            return True
        return False
        
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
