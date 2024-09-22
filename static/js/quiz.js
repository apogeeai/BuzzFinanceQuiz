document.addEventListener('DOMContentLoaded', () => {
    const quizContainer = document.getElementById('quiz-container');
    if (!quizContainer) return;

    const questionContainer = document.getElementById('question-container');
    const optionsContainer = document.getElementById('options-container');
    const nextBtn = document.getElementById('next-btn');

    const questions = [
        {
            question: "What's your go-to reaction when you receive your paycheck?",
            options: [
                "Time to treat myself! Let's splurge!",
                "Phew, at least I can cover my bills.",
                "Set aside some savings, then enjoy the rest.",
                "Investing and saving come first; spending is secondary."
            ]
        },
        {
            question: "If your wallet could talk, what would it say?",
            options: [
                "Help! I'm empty!",
                "I'm hanging in there.",
                "Feeling healthy and growing.",
                "I'm overflowing with organized cash."
            ]
        },
        {
            question: "How do you feel about budgeting?",
            options: [
                "Budgeting? What's that?",
                "I tried once but it didn't stick.",
                "I have a basic budget I follow.",
                "I track every penny meticulously."
            ]
        },
        {
            question: "When friends talk about retirement plans, you think:",
            options: [
                "That's ages away! Why bother now?",
                "Maybe I should look into that sometime.",
                "I've started saving but could do more.",
                "I'm confident in my retirement strategy."
            ]
        },
        {
            question: "Choose the animal that best represents your financial style:",
            options: [
                "A carefree butterfly",
                "A curious kitten",
                "A diligent beaver",
                "A wise owl"
            ]
        }
    ];

    let currentQuestion = 0;
    const answers = [];

    function displayQuestion() {
        const question = questions[currentQuestion];
        questionContainer.textContent = question.question;
        optionsContainer.innerHTML = '';
        
        question.options.forEach((option, index) => {
            const button = document.createElement('button');
            button.textContent = option;
            button.classList.add('w-full', 'text-left', 'p-2', 'border', 'rounded-md', 'hover:bg-blue-100', 'transition', 'duration-300');
            button.addEventListener('click', () => selectOption(index));
            optionsContainer.appendChild(button);
        });

        nextBtn.style.display = 'none';
    }

    function selectOption(index) {
        answers[currentQuestion] = String.fromCharCode(65 + index);
        nextBtn.style.display = 'block';
        
        const buttons = optionsContainer.getElementsByTagName('button');
        for (let i = 0; i < buttons.length; i++) {
            buttons[i].classList.remove('bg-blue-200');
        }
        buttons[index].classList.add('bg-blue-200');
    }

    nextBtn.addEventListener('click', () => {
        currentQuestion++;
        if (currentQuestion < questions.length) {
            displayQuestion();
        } else {
            submitQuiz();
        }
    });

    function submitQuiz() {
        const userId = quizContainer.dataset.userId;
        fetch('/submit_quiz', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                answers: answers.join('')
            }),
        })
        .then(response => {
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Network response was not ok: ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            window.location.href = `/results/${data.user_id}`;
        })
        .catch((error) => {
            console.error('Error:', error);
            alert(`An error occurred while submitting the quiz: ${error.message}`);
        });
    }

    displayQuestion();
});
