#OLD VERSION OF TAKE_EXAM 

{% extends 'base.html' %}

{% block title %}{{ exam.title }}{% endblock %}

{% block content %}
<form method="post" action="{% url 'submit_exam' exam.id %}" id="examForm">
    {% csrf_token %}

    <div class="row">
        <!-- Left: Passage Text -->
        <div class="col-md-6">
            <div class="card shadow-sm">
                <div class="card-header bg-white d-flex justify-content-between align-items-center py-3">
                    <h5 class="m-0 fw-bold"><i class="fa-solid fa-align-left me-2"></i>Reading Passage</h5>
                    <div class="badge bg-danger fs-6" id="timer">
                        <i class="fa-regular fa-clock me-1"></i> <span id="timeRemaining">{{ exam.time_limit_minutes }}:00</span>
                    </div>
                </div>
                <div class="passage-text">
                    {{ exam.passage_text|linebreaks }}
                </div>
            </div>
        </div>

        <!-- Right: Questions -->
        <div class="col-md-6">
            <div class="card shadow-sm h-100">
                <div class="card-header bg-white py-3">
                    <h5 class="m-0 fw-bold">Questions</h5>
                </div>
                <div class="question-area">
                    {% for question in exam.questions.all %}
                    <div class="mb-4 p-3 border rounded bg-light">
                        <p class="fw-bold mb-2">{{ forloop.counter }}. {{ question.text }}</p>

                        <div class="d-flex flex-column gap-2">
                            {% for choice in question.choices.all %}
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="question_{{ question.id }}" id="choice_{{ choice.id }}" value="{{ choice.id }}">
                                <label class="form-check-label" for="choice_{{ choice.id }}">
                                    {{ choice.text }}
                                </label>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    {% endfor %}

                    <div class="d-grid gap-2 mt-4">
                        <button type="submit" class="btn btn-success btn-lg" onclick="return confirm('Are you sure you want to submit?')">
                            Submit Answers
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</form>

<script>
    // Simple Timer
    let timeLimit = {{ exam.time_limit_minutes }};
    let timeLeft = timeLimit * 60; // seconds

    const timerDisplay = document.getElementById('timeRemaining');

    const timerInterval = setInterval(() => {
        const minutes = Math.floor(timeLeft / 60);
        let seconds = timeLeft % 60;

        seconds = seconds < 10 ? '0' + seconds : seconds;

        timerDisplay.textContent = `${minutes}:${seconds}`;

        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            alert("Time is up! Submitting your test.");
            document.getElementById('examForm').submit();
        }

        timeLeft--;
    }, 1000);
</script>
{% endblock %}