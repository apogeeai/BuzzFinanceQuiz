from flask import Flask, render_template, request, redirect, url_for, jsonify
import logging
import os
from models import db, User, QuizResponse

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    with app.app_context():
        db.create_all()

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
