import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from functools import wraps
from datetime import datetime

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
db.init_app(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

class QuizResponse(db.Model):
    __tablename__ = 'quiz_response'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    answers = db.Column(db.Text, nullable=False)
    result_category = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship('User', backref=db.backref('quiz_responses', lazy=True))

def create_tables():
    with app.app_context():
        db.create_all()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session or not session['admin_logged_in']:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        user = User(name=name, email=email)
        db.session.add(user)
        db.session.commit()
        return render_template('quiz.html', user_id=user.id)
    return render_template('quiz.html')

def calculate_result_category(answers):
    total_score = sum(ord(answer) - ord('A') for answer in answers)
    max_score = 3 * len(answers)  # Changed from 4 to 3 as we now have 4 questions
    percentage = (total_score / max_score) * 100
    
    if percentage < 33:  # Adjusted thresholds
        return "Carefree Butterfly"
    elif percentage < 66:
        return "Curious Kitten"
    elif percentage < 85:
        return "Diligent Beaver"
    else:
        return "Wise Owl"

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    try:
        data = request.json
        user_id = data.get('user_id')
        answers = data.get('answers')
        
        print(f"Debug: Received user_id: {user_id}, answers: {answers}")
        
        user = User.query.get(user_id)
        if not user:
            print(f"Debug: User not found for user_id: {user_id}")
            return jsonify({'error': 'User not found'}), 404

        quiz_response = QuizResponse(user_id=user_id, answers=answers)
        quiz_response.result_category = calculate_result_category(answers)
        db.session.add(quiz_response)
        db.session.commit()
        
        print(f"Debug: Quiz response saved successfully for user_id: {user_id}")

        response = jsonify({'message': 'Quiz submitted successfully', 'user_id': user_id})
        print(f"Debug: Returning response: {response.get_data(as_text=True)}")
        return response
    except Exception as e:
        print(f"Debug: Error in submit_quiz: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

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
    max_score = 3 * len(answers)  # Changed from 4 to 3 as we now have 4 questions
    percentage = (total_score / max_score) * 100

    result = quiz_response.result_category
    tips = get_tips_for_category(result)

    return render_template('results.html', result=result, percentage=percentage, tips=tips)

def get_tips_for_category(category):
    tips = {
        "Carefree Butterfly": [
            "Start tracking your expenses to understand your spending habits.",
            "Set up a small emergency fund to cover unexpected costs.",
            "Learn about budgeting basics and try creating a simple budget.",
            "Consider setting up automatic savings to build good financial habits."
        ],
        "Curious Kitten": [
            "Increase your emergency fund to cover 3-6 months of expenses.",
            "Look into different savings accounts and their interest rates.",
            "Start learning about investing basics and consider low-risk options.",
            "Review your expenses and identify areas where you can cut back."
        ],
        "Diligent Beaver": [
            "Diversify your investments to spread risk and potentially increase returns.",
            "Consider increasing your retirement contributions if possible.",
            "Look into additional income streams or side hustles.",
            "Start setting long-term financial goals and create plans to achieve them."
        ],
        "Wise Owl": [
            "Consider advanced investment strategies or consult with a financial advisor.",
            "Look into estate planning and wealth transfer strategies.",
            "Explore ways to optimize your tax strategy.",
            "Consider philanthropic opportunities or setting up a charitable foundation."
        ]
    }
    return tips.get(category, [])

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'secret':  # Replace with secure authentication
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
        app.logger.info("Accessing admin dashboard")
        total_users = User.query.count()
        app.logger.info(f"Total users: {total_users}")
        total_quizzes = QuizResponse.query.count()
        app.logger.info(f"Total quizzes: {total_quizzes}")
        
        category_distribution = db.session.query(
            QuizResponse.result_category,
            db.func.count(QuizResponse.id)
        ).group_by(QuizResponse.result_category).all()
        app.logger.info(f"Category distribution: {category_distribution}")
        
        recent_results = db.session.query(QuizResponse).join(User).order_by(QuizResponse.created_at.desc()).limit(10).all()
        app.logger.info(f"Recent results count: {len(recent_results)}")
        
        success_message = request.args.get('success_message')
        
        return render_template('admin_dashboard.html',
                               total_users=total_users,
                               total_quizzes=total_quizzes,
                               category_distribution=category_distribution,
                               recent_results=recent_results,
                               success_message=success_message)
    except Exception as e:
        app.logger.error(f"Error in admin_dashboard: {str(e)}")
        return render_template('error.html', error_message="An error occurred while loading the admin dashboard."), 500

@app.route('/admin/clear_results', methods=['POST'])
@admin_required
def clear_results():
    try:
        QuizResponse.query.delete()
        db.session.commit()
        return redirect(url_for('admin_dashboard', success_message="All quiz results have been cleared successfully."))
    except Exception as e:
        db.session.rollback()
        return render_template('error.html', error_message="An error occurred while clearing the results."), 500

if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0', port=5000, debug=True)
