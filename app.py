import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import func
import logging

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

class QuizResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    answers = db.Column(db.Text, nullable=False)
    user = db.relationship('User', backref=db.backref('quiz_responses', lazy=True))

def create_tables():
    with app.app_context():
        db.create_all()

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

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    data = request.json
    user_id = data.get('user_id')
    answers = data.get('answers')
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    quiz_response = QuizResponse(user_id=user_id, answers=answers)
    db.session.add(quiz_response)
    db.session.commit()

    return jsonify({'message': 'Quiz submitted successfully'})

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
    max_score = 4 * len(answers)
    percentage = (total_score / max_score) * 100

    if percentage < 25:
        result = "Financial Butterfly: You're carefree with money, but it might be time to start thinking about the future!"
        tips = [
            "Start tracking your expenses to understand your spending habits.",
            "Set up a small emergency fund to cover unexpected costs.",
            "Learn about budgeting basics and try creating a simple budget.",
            "Consider setting up automatic savings to build good financial habits."
        ]
    elif percentage < 50:
        result = "Curious Kitten: You're starting to explore financial responsibility. Keep learning and growing!"
        tips = [
            "Increase your emergency fund to cover 3-6 months of expenses.",
            "Look into different savings accounts and their interest rates.",
            "Start learning about investing basics and consider low-risk options.",
            "Review your expenses and identify areas where you can cut back."
        ]
    elif percentage < 75:
        result = "Diligent Beaver: You're on the right track with your finances. Keep up the good work!"
        tips = [
            "Diversify your investments to spread risk and potentially increase returns.",
            "Consider increasing your retirement contributions if possible.",
            "Look into additional income streams or side hustles.",
            "Start setting long-term financial goals and create plans to achieve them."
        ]
    else:
        result = "Wise Owl: You're a financial guru! Your future is looking bright and secure."
        tips = [
            "Consider advanced investment strategies or consult with a financial advisor.",
            "Look into estate planning and wealth transfer strategies.",
            "Explore ways to optimize your tax strategy.",
            "Consider philanthropic opportunities or setting up a charitable foundation."
        ]

    return render_template('results.html', result=result, percentage=percentage, tips=tips)

@app.route('/admin')
def admin_dashboard():
    try:
        app.logger.info("Accessing admin dashboard")
        app.logger.debug(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        total_users = User.query.count()
        app.logger.info(f"Total users: {total_users}")
        
        total_quizzes = QuizResponse.query.count()
        app.logger.info(f"Total quizzes: {total_quizzes}")
        
        avg_score = db.session.query(func.avg(
            func.sum(func.cast(func.ascii(func.substr(QuizResponse.answers, 1, 1)) - 65, db.Integer)) +
            func.sum(func.cast(func.ascii(func.substr(QuizResponse.answers, 2, 1)) - 65, db.Integer)) +
            func.sum(func.cast(func.ascii(func.substr(QuizResponse.answers, 3, 1)) - 65, db.Integer)) +
            func.sum(func.cast(func.ascii(func.substr(QuizResponse.answers, 4, 1)) - 65, db.Integer)) +
            func.sum(func.cast(func.ascii(func.substr(QuizResponse.answers, 5, 1)) - 65, db.Integer))
        ) / 20 * 100).scalar()
        app.logger.info(f"Average score: {avg_score}")

        recent_quizzes = db.session.query(User.name, User.email, QuizResponse.answers).\
            join(QuizResponse, User.id == QuizResponse.user_id).\
            order_by(QuizResponse.id.desc()).\
            limit(10).all()
        app.logger.info(f"Recent quizzes: {recent_quizzes}")

        return render_template('admin.html', total_users=total_users, total_quizzes=total_quizzes,
                               avg_score=avg_score, recent_quizzes=recent_quizzes)
    except Exception as e:
        app.logger.error(f"Error in admin dashboard: {str(e)}")
        return "An error occurred while loading the admin dashboard", 500

if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0', port=8080, debug=True)
