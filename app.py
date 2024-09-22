import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_mail import Mail, Message
from models import db, User, QuizResponse, QuizStatistics
from sqlalchemy import func
from datetime import datetime

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
mail = Mail(app)

def create_tables():
    with app.app_context():
        db.create_all()

def send_email_notification(user, result, tips):
    subject = "Your Financial Health Quiz Results"
    body = f"""
    Dear {user.name},

    Thank you for taking our Financial Health Quiz. Here are your results:

    {result}

    Here are some personalized financial tips for you:

    {' '.join(['- ' + tip for tip in tips])}

    We hope you found this quiz helpful. If you have any questions or would like to learn more about improving your financial health, please don't hesitate to contact us.

    Best regards,
    The Financial Health Quiz Team
    """
    
    msg = Message(subject=subject, recipients=[user.email], body=body)
    mail.send(msg)

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

    score = sum(ord(answer) - ord('A') for answer in answers)
    quiz_response = QuizResponse(user_id=user_id, answers=answers, score=score)
    db.session.add(quiz_response)

    # Update quiz statistics
    stats = QuizStatistics.query.first()
    if not stats:
        stats = QuizStatistics()
        db.session.add(stats)
    
    stats.total_quizzes += 1
    stats.average_score = ((stats.average_score * (stats.total_quizzes - 1)) + score) / stats.total_quizzes
    stats.last_updated = datetime.utcnow()

    db.session.commit()

    # Generate results and send email notification
    result, tips = generate_results(score, len(answers))
    send_email_notification(user, result, tips)

    return jsonify({'message': 'Quiz submitted successfully'})

def generate_results(total_score, num_questions):
    max_score = 4 * num_questions
    percentage = (total_score / max_score) * 100

    if percentage < 25:
        result = "Financial Hummingbird: You're quick and energetic with money, but it might be time to slow down and plan for the future!"
        tips = [
            "Start tracking your expenses to understand your spending habits.",
            "Set up a small emergency fund to cover unexpected costs.",
            "Learn about budgeting basics and try creating a simple budget.",
            "Consider setting up automatic savings to build good financial habits."
        ]
    elif percentage < 50:
        result = "Money Chameleon: You're adaptable with finances, but it's time to develop a consistent strategy!"
        tips = [
            "Increase your emergency fund to cover 3-6 months of expenses.",
            "Look into different savings accounts and their interest rates.",
            "Start learning about investing basics and consider low-risk options.",
            "Review your expenses and identify areas where you can cut back."
        ]
    elif percentage < 75:
        result = "Fiscal Fox: You're clever with your money management. Keep refining your financial skills!"
        tips = [
            "Diversify your investments to spread risk and potentially increase returns.",
            "Consider increasing your retirement contributions if possible.",
            "Look into additional income streams or side hustles.",
            "Start setting long-term financial goals and create plans to achieve them."
        ]
    else:
        result = "Financial Phoenix: You've mastered money management and are ready to soar to new financial heights!"
        tips = [
            "Consider advanced investment strategies or consult with a financial advisor.",
            "Look into estate planning and wealth transfer strategies.",
            "Explore ways to optimize your tax strategy.",
            "Consider philanthropic opportunities or setting up a charitable foundation."
        ]

    return result, tips

@app.route('/results/<int:user_id>')
def results(user_id):
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('index'))

    quiz_response = QuizResponse.query.filter_by(user_id=user_id).first()
    if not quiz_response:
        return redirect(url_for('index'))

    result, tips = generate_results(quiz_response.score, len(quiz_response.answers))
    percentage = (quiz_response.score / (4 * len(quiz_response.answers))) * 100

    return render_template('results.html', result=result, percentage=percentage, tips=tips)

@app.route('/admin')
def admin_dashboard():
    stats = QuizStatistics.query.first()
    if not stats:
        stats = QuizStatistics()
        db.session.add(stats)
        db.session.commit()

    recent_quizzes = QuizResponse.query.order_by(QuizResponse.created_at.desc()).limit(10).all()
    
    return render_template('admin_dashboard.html', stats=stats, recent_quizzes=recent_quizzes)

if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0', port=5000)
