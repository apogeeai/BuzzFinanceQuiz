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
    if quiz_response.q1_answer == 'A':
        tips.append("Start by setting aside 10% of your paycheck for savings before spending on non-essentials.")
    elif quiz_response.q1_answer == 'B':
        tips.append("Create a detailed budget to understand where your money is going and identify areas to cut back.")
    elif quiz_response.q1_answer == 'C':
        tips.append("Great job saving! Consider automating your savings to make it even easier.")
    else:
        tips.append("Your saving habits are excellent. Look into high-yield savings accounts or investment options for better returns.")

    # Tip based on wallet status (Q2)
    if quiz_response.q2_answer == 'A':
        tips.append("Start building an emergency fund with small, regular contributions. Aim for $1,000 initially.")
    elif quiz_response.q2_answer == 'B':
        tips.append("Increase your emergency fund to cover 3-6 months of expenses. Consider a side hustle for extra income.")
    elif quiz_response.q2_answer == 'C':
        tips.append("You're on the right track. Set specific financial goals, like saving for a down payment or a dream vacation.")
    else:
        tips.append("Great job managing your finances! Consider diversifying your investments or exploring tax-advantaged accounts.")

    # Tip based on budgeting habits (Q3)
    if quiz_response.q3_answer == 'A':
        tips.append("Start with a simple budget using the 50/30/20 rule: 50% for needs, 30% for wants, and 20% for savings and debt repayment.")
    elif quiz_response.q3_answer == 'B':
        tips.append("Try using a budgeting app to track your expenses and stick to your budget more easily.")
    elif quiz_response.q3_answer == 'C':
        tips.append("Look for ways to optimize your budget further, such as negotiating bills or finding cheaper alternatives for regular expenses.")
    else:
        tips.append("Your budgeting skills are top-notch. Consider helping others by sharing your budgeting tips or volunteering for financial literacy programs.")

    # Tip based on retirement planning (Q4)
    if quiz_response.q4_answer == 'A':
        tips.append("Start learning about retirement savings options. Even small contributions to a 401(k) or IRA can grow significantly over time.")
    elif quiz_response.q4_answer == 'B':
        tips.append("If your employer offers a 401(k) match, try to contribute enough to get the full match - it's free money!")
    elif quiz_response.q4_answer == 'C':
        tips.append("Consider increasing your retirement contributions by 1% each year. Look into diversifying your retirement portfolio.")
    else:
        tips.append("You're well-prepared for retirement. Consider estate planning and long-term care insurance to protect your assets.")

    # Tip based on financial style (Q5)
    if financial_type == "Butterfly":
        tips.append("Challenge yourself to a 'no-spend week' each month to boost your savings and become more mindful of your spending habits.")
    elif financial_type == "Kitten":
        tips.append("Set a specific financial goal for the next 3 months, like saving a certain amount or paying off a specific debt. Track your progress weekly.")
    elif financial_type == "Beaver":
        tips.append("Consider exploring passive income streams, such as dividend-paying stocks or rental properties, to supplement your earnings.")
    else:  # Owl
        tips.append("Share your financial wisdom by mentoring others or starting a blog. Teaching others can also reinforce good financial habits for yourself.")

    return tips

if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0', port=5000)
