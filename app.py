import logging
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from models import db, User, QuizResponse
from sqlalchemy import func
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24)

db.init_app(app)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    with app.app_context():
        db.create_all()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/quiz', methods=['POST'])
def quiz():
    name = request.form.get('name')
    email = request.form.get('email')

    if not name or not email:
        return render_template('error.html', error_message="Name and email are required.")

    try:
        user = User(name=name, email=email)
        db.session.add(user)
        db.session.commit()
        return render_template('quiz.html', user_id=user.id)
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating user: {str(e)}")
        return render_template('error.html', error_message="An error occurred while starting the quiz. Please try again.")

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    try:
        data = request.json
        user_id = data.get('user_id')
        answers = data.get('answers')
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        quiz_response = QuizResponse(user_id=user_id, answers=answers)
        quiz_response.result_category = calculate_result_category(answers)
        db.session.add(quiz_response)
        db.session.commit()

        return jsonify({'message': 'Quiz submitted successfully', 'user_id': user_id})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting quiz: {str(e)}")
        return jsonify({'error': 'An error occurred while submitting the quiz'}), 500

@app.route('/results/<int:user_id>')
def results(user_id):
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('index'))

    quiz_response = QuizResponse.query.filter_by(user_id=user_id).first()
    if not quiz_response:
        return redirect(url_for('index'))

    answers = quiz_response.answers
    total_score = sum(ord(answer) - ord('A') for answer in answers)
    max_score = 3 * len(answers)
    percentage = (total_score / max_score) * 100

    result = quiz_response.result_category

    return render_template('results.html', result=result, percentage=percentage)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'secret':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Invalid credentials')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    try:
        total_users = User.query.count()
        total_quizzes = QuizResponse.query.count()
        
        category_distribution = db.session.query(
            QuizResponse.result_category,
            func.count(QuizResponse.id)
        ).group_by(QuizResponse.result_category).all()
        
        recent_results = db.session.query(QuizResponse).join(User).order_by(QuizResponse.created_at.desc()).limit(10).all()
        
        # Calculate average score
        average_score = db.session.query(func.avg(
            func.sum(func.ascii(func.substr(QuizResponse.answers, 1, 1)) - 65) +
            func.sum(func.ascii(func.substr(QuizResponse.answers, 2, 1)) - 65) +
            func.sum(func.ascii(func.substr(QuizResponse.answers, 3, 1)) - 65) +
            func.sum(func.ascii(func.substr(QuizResponse.answers, 4, 1)) - 65)
        )).scalar()

        if average_score is not None:
            average_score = (average_score / 12) * 100  # Convert to percentage
        else:
            average_score = 0

        # Get daily quiz submissions for the last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        daily_submissions = db.session.query(
            func.date(QuizResponse.created_at).label('date'),
            func.count(QuizResponse.id).label('count')
        ).filter(QuizResponse.created_at >= seven_days_ago).group_by(func.date(QuizResponse.created_at)).all()

        daily_submissions_dict = {str(day.date): day.count for day in daily_submissions}
        
        return render_template('admin_dashboard.html',
                               total_users=total_users,
                               total_quizzes=total_quizzes,
                               category_distribution=category_distribution,
                               recent_results=recent_results,
                               average_score=average_score,
                               daily_submissions=daily_submissions_dict)
    except Exception as e:
        logger.error(f"Error in admin dashboard: {str(e)}")
        return render_template('error.html', error_message="An error occurred while loading the admin dashboard. Please try again later."), 500

def calculate_result_category(answers):
    total_score = sum(ord(answer) - ord('A') for answer in answers)
    if total_score <= 3:
        return "Carefree Butterfly"
    elif total_score <= 6:
        return "Curious Kitten"
    elif total_score <= 9:
        return "Diligent Beaver"
    else:
        return "Wise Owl"

if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0', port=5000, debug=True)
