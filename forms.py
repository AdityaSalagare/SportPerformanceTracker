from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, FloatField, DateField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from datetime import datetime

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('coach', 'Coach'), ('athlete', 'Athlete')], validators=[DataRequired()])
    submit = SubmitField('Register')

class TeamForm(FlaskForm):
    name = StringField('Team Name', validators=[DataRequired(), Length(max=50)])
    sport = StringField('Sport', validators=[DataRequired(), Length(max=50)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Create Team')

class MetricForm(FlaskForm):
    name = StringField('Metric Name', validators=[DataRequired(), Length(max=50)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=200)])
    unit = StringField('Unit (e.g., seconds, kg, points)', validators=[DataRequired(), Length(max=20)])
    min_value = FloatField('Minimum Value', validators=[Optional()])
    max_value = FloatField('Maximum Value', validators=[Optional()])
    submit = SubmitField('Add Metric')

class AthleteForm(FlaskForm):
    athlete_id = SelectField('Athlete', validators=[DataRequired()])
    submit = SubmitField('Add to Team')

class PerformanceForm(FlaskForm):
    athlete_id = SelectField('Athlete', validators=[DataRequired()])
    metric_name = SelectField('Metric', validators=[DataRequired()])
    value = FloatField('Value', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=200)])
    submit = SubmitField('Record Performance')

class ReportForm(FlaskForm):
    team_id = SelectField('Team', validators=[DataRequired()])
    report_type = SelectField('Report Type', 
                              choices=[
                                  ('team_performance', 'Team Performance'),
                                  ('athlete_comparison', 'Athlete Comparison')
                              ], 
                              validators=[DataRequired()])
    date_from = DateField('From Date', format='%Y-%m-%d', validators=[Optional()])
    date_to = DateField('To Date', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Generate Report')
