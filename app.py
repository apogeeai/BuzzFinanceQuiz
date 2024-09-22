import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import func
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from flask.cli import click

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class QuizResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    answers = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('quiz_responses', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
        
        user = User.query.filter_by(email=email).first()
        if user:
            if user.name != name:
                user.name = name
                db.session.commit()
        else:
            user = User(name=name, email=email)
            db.session.add(user)
            db.session.commit()
        
        quiz_response = QuizResponse(user_id=user.id, answers="")
        db.session.add(quiz_response)
        db.session.commit()
        
        return render_template('quiz.html', user_id=user.id, quiz_response_id=quiz_response.id)
    return render_template('quiz.html')

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    data = request.json
    quiz_response_id = data.get('quiz_response_id')
    answers = data.get('answers')
    
    quiz_response = QuizResponse.query.get(quiz_response_id)
    if not quiz_response:
        return jsonify({'error': 'Quiz response not found'}), 404

    quiz_response.answers = answers
    db.session.commit()

    return jsonify({'message': 'Quiz submitted successfully'})

@app.route('/results/<int:quiz_response_id>')
def results(quiz_response_id):
    quiz_response = QuizResponse.query.get(quiz_response_id)
    if not quiz_response:
        return redirect(url_for('index'))

    user = User.query.get(quiz_response.user_id)
    if not user:
        return redirect(url_for('index'))

    answers = quiz_response.answers
    total_score = sum(ord(answer) - ord('A') for answer in answers)
    max_score = 4 * len(answers)
    percentage = (total_score / max_score) * 100

    if percentage < 20:
        result = "Blissful Butterfly: You're carefree with money, but it might be time to start thinking about the future!"
        tips = [
            "Start tracking your expenses to understand your spending habits.",
            "Set up a small emergency fund to cover unexpected costs.",
            "Learn about budgeting basics and try creating a simple budget.",
            "Consider setting up automatic savings to build good financial habits."
        ]
    elif percentage < 40:
        result = "Curious Cat: You're starting to explore financial responsibility. Keep learning and growing!"
        tips = [
            "Increase your emergency fund to cover 3-6 months of expenses.",
            "Look into different savings accounts and their interest rates.",
            "Start learning about investing basics and consider low-risk options.",
            "Review your expenses and identify areas where you can cut back."
        ]
    elif percentage < 60:
        result = "Busy Beaver: You're on the right track with your finances. Keep up the good work!"
        tips = [
            "Diversify your investments to spread risk and potentially increase returns.",
            "Consider increasing your retirement contributions if possible.",
            "Look into additional income streams or side hustles.",
            "Start setting long-term financial goals and create plans to achieve them."
        ]
    elif percentage < 80:
        result = "Diligent Dolphin: You're swimming smoothly through financial waters. Keep up the excellent work!"
        tips = [
            "Consider advanced investment strategies or consult with a financial advisor.",
            "Look into estate planning and wealth transfer strategies.",
            "Explore ways to optimize your tax strategy.",
            "Consider philanthropic opportunities or setting up a charitable foundation."
        ]
    else:
        result = "Wise Wolf: You're a financial mastermind! Your future is looking exceptionally bright and secure."
        tips = [
            "Explore complex investment vehicles like hedge funds or private equity.",
            "Consider mentoring others or writing about your financial wisdom.",
            "Look into creating passive income streams for long-term wealth.",
            "Investigate international investment opportunities for further diversification."
        ]

    return render_template('results.html', result=result, percentage=percentage, tips=tips)

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('index'))

    total_users = User.query.count()
    total_quizzes = QuizResponse.query.count()
    
    avg_score = db.session.query(func.avg(
        func.sum(func.ascii(func.substr(QuizResponse.answers, 1, 1)) - 65) +
        func.sum(func.ascii(func.substr(QuizResponse.answers, 2, 1)) - 65) +
        func.sum(func.ascii(func.substr(QuizResponse.answers, 3, 1)) - 65) +
        func.sum(func.ascii(func.substr(QuizResponse.answers, 4, 1)) - 65) +
        func.sum(func.ascii(func.substr(QuizResponse.answers, 5, 1)) - 65)
    )).scalar()
    
    if avg_score is not None:
        avg_percentage = (avg_score / (4 * 5)) * 100
    else:
        avg_percentage = 0

    result_distribution = {
        "Blissful Butterfly": 0,
        "Curious Cat": 0,
        "Busy Beaver": 0,
        "Diligent Dolphin": 0,
        "Wise Wolf": 0
    }

    recent_responses = []
    quiz_responses = QuizResponse.query.order_by(QuizResponse.created_at.desc()).limit(10).all()
    for response in quiz_responses:
        total_score = sum(ord(answer) - ord('A') for answer in response.answers)
        max_score = 4 * len(response.answers)
        percentage = (total_score / max_score) * 100

        if percentage < 20:
            result = "Blissful Butterfly"
            result_distribution["Blissful Butterfly"] += 1
        elif percentage < 40:
            result = "Curious Cat"
            result_distribution["Curious Cat"] += 1
        elif percentage < 60:
            result = "Busy Beaver"
            result_distribution["Busy Beaver"] += 1
        elif percentage < 80:
            result = "Diligent Dolphin"
            result_distribution["Diligent Dolphin"] += 1
        else:
            result = "Wise Wolf"
            result_distribution["Wise Wolf"] += 1

        recent_responses.append({
            "user": response.user,
            "score": round(percentage, 2),
            "result": result
        })

    return render_template('admin_dashboard.html',
                           total_users=total_users,
                           total_quizzes=total_quizzes,
                           avg_percentage=avg_percentage,
                           result_distribution=result_distribution,
                           recent_responses=recent_responses)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user and user.is_admin:
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.cli.command("create-admin")
@click.argument("email")
def create_admin(email):
    user = User.query.filter_by(email=email).first()
    if user:
        user.is_admin = True
        db.session.commit()
        print(f"User {email} has been granted admin privileges.")
    else:
        new_admin = User(email=email, name="Admin", is_admin=True)
        db.session.add(new_admin)
        db.session.commit()
        print(f"New admin user created with email: {email}")

if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0', port=5000)
