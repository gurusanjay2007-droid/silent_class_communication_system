from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class Institution(db.Model):
    __tablename__ = 'institutions'
    id = db.Column(db.String(20), primary_key=True) # Generated ID
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    
    users = db.relationship('User', backref='institution', lazy=True)
    periods = db.relationship('Period', backref='institution', lazy=True)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.String(20), db.ForeignKey('institutions.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'student' or 'staff'
    username = db.Column(db.String(100), unique=True, nullable=False) # Used for login
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    
    # Student specific fields
    reg_no = db.Column(db.String(50), nullable=True) # Could be used as login for student
    dob = db.Column(db.Date, nullable=True)
    department = db.Column(db.String(100), nullable=True)
    year_of_study = db.Column(db.String(20), nullable=True)
    student_class = db.Column(db.String(50), nullable=True)
    
    # Staff specific fields
    staff_id_str = db.Column(db.String(50), nullable=True) # Used for staff login
    degree_completed = db.Column(db.String(100), nullable=True)
    subject_handled = db.Column(db.String(100), nullable=True)
    
    # Periods hosted by staff
    hosted_periods = db.relationship('Period', backref='staff', lazy=True)

class Period(db.Model):
    __tablename__ = 'periods'
    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.String(20), db.ForeignKey('institutions.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    year = db.Column(db.String(20), nullable=False)
    student_class = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    doubts = db.relationship('Doubt', backref='period', lazy=True)

class Doubt(db.Model):
    __tablename__ = 'doubts'
    id = db.Column(db.Integer, primary_key=True)
    period_id = db.Column(db.Integer, db.ForeignKey('periods.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending') # 'pending', 'cleared', 'removed'
    removed_reason = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
