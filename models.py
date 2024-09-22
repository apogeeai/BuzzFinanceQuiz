from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    quiz_responses = relationship('QuizResponse', back_populates='user')

class QuizResponse(db.Model):
    __tablename__ = 'quiz_responses'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    answers = Column(Text, nullable=False)
    score = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship('User', back_populates='quiz_responses')

class QuizStatistics(db.Model):
    __tablename__ = 'quiz_statistics'
    id = Column(Integer, primary_key=True)
    total_quizzes = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow)
