from flask import Flask, render_template, request, jsonify
import logging
import os
from models import db, QuizResponse

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

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    try:
        data = request.json
        answers = data.get('answers')
        
        if not answers:
            return jsonify({'error': 'Answers are required'}), 400

        result_category = calculate_result_category(answers)
        quiz_response = QuizResponse(answers=answers, result_category=result_category)
        db.session.add(quiz_response)
        db.session.commit()

        total_score = sum(ord(answer) - ord('A') for answer in answers)
        max_score = 3 * len(answers)
        percentage = (total_score / max_score) * 100
        
        tips = get_tips_for_category(result_category)

        return jsonify({
            'message': 'Quiz submitted successfully',
            'result': result_category,
            'percentage': percentage,
            'tips': tips
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error submitting quiz: {str(e)}")
        return jsonify({'error': 'An error occurred while submitting the quiz'}), 500

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
