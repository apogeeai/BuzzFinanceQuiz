from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class QuizResponse(db.Model):
    __tablename__ = 'quiz_responses'
    id = Column(Integer, primary_key=True)
    answers = Column(Text, nullable=False)
    result_category = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
