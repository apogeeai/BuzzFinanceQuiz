import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import func
from datetime import datetime
from flask_mail import Mail, Message

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
mail = Mail()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

db.init_app(app)
mail.init_app(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class QuizResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    answers = db.Column(db.Text, nullable=False)
    result_category = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('quiz_responses', lazy=True))

def create_tables():
    with app.app_context():
        db.drop_all()  # Drop all existing tables
        db.create_all()  # Create new tables with updated schema

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

    total_score = sum(ord(answer) - ord('A') for answer in answers)
    max_score = 4 * len(answers)
    percentage = (total_score / max_score) * 100

    if percentage < 25:
        result_category = "The Blissful Butterfly"
    elif percentage < 50:
        result_category = "The Curious Cat"
    elif percentage < 75:
        result_category = "The Savvy Shark"
    elif percentage < 90:
        result_category = "The Wise Whale"
    else:
        result_category = "The Busy Bat"

    quiz_response = QuizResponse(user_id=user_id, answers=answers, result_category=result_category)
    db.session.add(quiz_response)
    db.session.commit()

    # Send email notification with financial tips
    send_email_notification(user, result_category)

    return jsonify({'message': 'Quiz submitted successfully'})

@app.route('/results/<int:user_id>')
def results(user_id):
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('index'))

    quiz_response = QuizResponse.query.filter_by(user_id=user_id).first()
    if not quiz_response:
        return redirect(url_for('index'))

    result = quiz_response.result_category
    answers = quiz_response.answers
    total_score = sum(ord(answer) - ord('A') for answer in answers)
    max_score = 4 * len(answers)
    percentage = (total_score / max_score) * 100

    tips = get_tips(result)

    return render_template('results.html', result=result, percentage=percentage, tips=tips)

def get_tips(result_category):
    tips = {
        "The Blissful Butterfly": [
            "Start tracking your expenses to understand your spending habits.",
            "Set up a small emergency fund to cover unexpected costs.",
            "Learn about budgeting basics and try creating a simple budget.",
            "Consider setting up automatic savings to build good financial habits."
        ],
        "The Curious Cat": [
            "Increase your emergency fund to cover 3-6 months of expenses.",
            "Look into different savings accounts and their interest rates.",
            "Start learning about investing basics and consider low-risk options.",
            "Review your expenses and identify areas where you can cut back."
        ],
        "The Savvy Shark": [
            "Diversify your investments to spread risk and potentially increase returns.",
            "Consider increasing your retirement contributions if possible.",
            "Look into additional income streams or side hustles.",
            "Start setting long-term financial goals and create plans to achieve them."
        ],
        "The Wise Whale": [
            "Consider advanced investment strategies or consult with a financial advisor.",
            "Look into estate planning and wealth transfer strategies.",
            "Explore ways to optimize your tax strategy.",
            "Consider philanthropic opportunities or setting up a charitable foundation."
        ],
        "The Busy Bat": [
            "Explore complex investment vehicles like hedge funds or private equity.",
            "Consider mentoring others on financial management.",
            "Look into starting your own business or becoming an angel investor.",
            "Develop a comprehensive wealth preservation and growth strategy."
        ]
    }
    return tips.get(result_category, [])

def send_email_notification(user, result_category):
    subject = "Your Financial Health Quiz Results"
    tips = get_tips(result_category)
    body = f"""
    Hello {user.name},

    Thank you for taking our Financial Health Quiz! Based on your responses, your financial personality is:

    {result_category}

    Here are some personalized financial tips for you:

    {' '.join(['- ' + tip for tip in tips])}

    We hope these tips help you on your journey to better financial health. If you have any questions or would like more information, please don't hesitate to reach out.

    Best regards,
    The Financial Health Quiz Team
    """

    msg = Message(subject=subject, recipients=[user.email], body=body)
    mail.send(msg)

@app.route('/admin')
def admin_dashboard():
    total_users = User.query.count()
    total_quizzes = QuizResponse.query.count()
    
    category_counts = db.session.query(
        QuizResponse.result_category,
        func.count(QuizResponse.id).label('count')
    ).group_by(QuizResponse.result_category).all()

    category_data = {category: count for category, count in category_counts}

    daily_stats = db.session.query(
        func.date(QuizResponse.created_at).label('date'),
        func.count('*').label('count')
    ).group_by(func.date(QuizResponse.created_at)).order_by(func.date(QuizResponse.created_at)).all()

    daily_data = {str(date): count for date, count in daily_stats}

    return render_template('admin.html', total_users=total_users, total_quizzes=total_quizzes, category_data=category_data, daily_data=daily_data)

if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0', port=5000)
