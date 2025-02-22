from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    notes = db.relationship('Note')



Base = declarative_base()

class Stats(Base,db.Model):
    __tablename__ = 'stats'

    id = db.Column(db.Integer, primary_key=True)
    total_dribble_count = db.Column(db.Integer)
    travel_detected_count = db.Column(db.Integer)
    total_step_count = db.Column(db.Integer)
