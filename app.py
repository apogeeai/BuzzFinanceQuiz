import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

class QuizResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    answers = db.Column(db.Text, nullable=False)
    q1_answer = db.Column(db.String(1), nullable=False)
    q2_answer = db.Column(db.String(1), nullable=False)
    q3_answer = db.Column(db.String(1), nullable=False)
    q4_answer = db.Column(db.String(1), nullable=False)
    q5_answer = db.Column(db.String(1), nullable=False)
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
        try:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                user_id = existing_user.id
            else:
                user = User(name=name, email=email)
                db.session.add(user)
                db.session.commit()
                user_id = user.id
            return render_template('quiz.html', user_id=user_id)
        except Exception as e:
            db.session.rollback()
            print(f"Error occurred: {str(e)}")
            return render_template('index.html', error="An error occurred. Please try again.")
    return render_template('quiz.html')

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    data = request.json
    user_id = data.get('user_id')
    answers = data.get('answers')
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    quiz_response = QuizResponse(
        user_id=user_id,
        answers=answers,
        q1_answer=answers[0],
        q2_answer=answers[1],
        q3_answer=answers[2],
        q4_answer=answers[3],
        q5_answer=answers[4]
    )
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
        result = "Financial Butterfly"
        profile = "You're carefree with money, but it might be time to start thinking about the future!"
        tips = get_personalized_tips(quiz_response, "Butterfly")
    elif percentage < 50:
        result = "Curious Kitten"
        profile = "You're starting to explore financial responsibility. Keep learning and growing!"
        tips = get_personalized_tips(quiz_response, "Kitten")
    elif percentage < 75:
        result = "Diligent Beaver"
        profile = "You're on the right track with your finances. Keep up the good work!"
        tips = get_personalized_tips(quiz_response, "Beaver")
    else:
        result = "Wise Owl"
        profile = "You're a financial guru! Your future is looking bright and secure."
        tips = get_personalized_tips(quiz_response, "Owl")

    return render_template('results.html', result=result, profile=profile, tips=tips, percentage=percentage)

def get_personalized_tips(quiz_response, financial_type):
    tips = []
    
    # Tip based on paycheck reaction (Q1)
    if quiz_response.q1_answer in ['A', 'B']:
        tips.append("Consider creating a budget to better manage your income and expenses.")
    elif quiz_response.q1_answer == 'C':
        tips.append("Great job saving! Try to increase your savings rate by 1% each month.")
    else:
        tips.append("Your saving habits are excellent. Consider exploring investment options for long-term growth.")

    # Tip based on wallet status (Q2)
    if quiz_response.q2_answer in ['A', 'B']:
        tips.append("Start building an emergency fund to cover 3-6 months of expenses.")
    elif quiz_response.q2_answer == 'C':
        tips.append("Your finances are stable. Consider setting specific financial goals for the future.")
    else:
        tips.append("You're doing great! Look into ways to optimize your tax strategy.")

    # Tip based on budgeting habits (Q3)
    if quiz_response.q3_answer in ['A', 'B']:
        tips.append("Start tracking your expenses and create a simple budget using the 50/30/20 rule.")
    elif quiz_response.q3_answer == 'C':
        tips.append("Refine your budget by categorizing expenses and identifying areas for potential savings.")
    else:
        tips.append("Your budgeting skills are top-notch. Consider using advanced budgeting tools or apps.")

    # Tip based on retirement planning (Q4)
    if quiz_response.q4_answer in ['A', 'B']:
        tips.append("Start learning about retirement savings options like 401(k)s and IRAs.")
    elif quiz_response.q4_answer == 'C':
        tips.append("Increase your retirement contributions and diversify your retirement portfolio.")
    else:
        tips.append("Your retirement planning is solid. Consider estate planning and long-term care insurance.")

    # Tip based on financial style (Q5)
    if financial_type == "Butterfly":
        tips.append("Start small: set a goal to save a specific amount each week and stick to it.")
    elif financial_type == "Kitten":
        tips.append("Educate yourself: read personal finance books or take an online course to improve your financial literacy.")
    elif financial_type == "Beaver":
        tips.append("Keep building: consider exploring passive income streams to supplement your earnings.")
    else:  # Owl
        tips.append("Share your knowledge: consider mentoring others or starting a financial blog to help others learn from your experience.")

    return tips

if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0', port=5000)
