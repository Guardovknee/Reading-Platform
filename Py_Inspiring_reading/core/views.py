from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from .models import ReadingExam, Question, Choice, StudentResult, ExamSession
import json


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('dashboard')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserCreationForm()

    return render(request, 'register.html', {'form': form})


@login_required
def dashboard(request):
    exams = ReadingExam.objects.prefetch_related('questions').all().order_by('-created_at')
    taken_exams_ids = StudentResult.objects.filter(student=request.user).values_list('exam_id', flat=True)
    results_map = {r.exam_id: r for r in StudentResult.objects.filter(student=request.user)}

    exam_data = []
    for exam in exams:
        is_taken = exam.id in taken_exams_ids
        result = results_map.get(exam.id)

        # Получаем сводку по типам вопросов
        types_summary = exam.get_question_types_summary()

        exam_data.append({
            'exam': exam,
            'is_taken': is_taken,
            'result': result,
            'types_summary': types_summary,
            'question_count': exam.questions.count()
        })

    user_results = StudentResult.objects.filter(student=request.user)
    total_taken = user_results.count()
    avg_score = 0
    if total_taken > 0:
        avg_score = sum([r.percentage for r in user_results]) / total_taken

    context = {
        'exam_data': exam_data,
        'total_taken': total_taken,
        'avg_score': round(avg_score, 1),
        'results': user_results
    }
    return render(request, 'dashboard.html', context)


@login_required
def take_exam(request, exam_id):
    exam = get_object_or_404(ReadingExam, id=exam_id)

    # Проверка: если уже сдавал
    if StudentResult.objects.filter(student=request.user, exam=exam).exists():
        messages.warning(request, "Вы уже сдавали этот экзамен. Пересдача запрещена.")
        return redirect('dashboard')

    # Создаем или получаем сессию
    session, created = ExamSession.objects.get_or_create(
        student=request.user,
        exam=exam,
        defaults={'is_active': True}
    )

    # Проверяем, не истекло ли время
    if session.is_expired():
        messages.error(request, "Время на прохождение теста истекло!")
        session.is_active = False
        session.save()
        return redirect('dashboard')

    return render(request, 'take_exam.html', {'exam': exam, 'session': session})


@login_required
def submit_exam(request, exam_id):
    if request.method != 'POST':
        return redirect('dashboard')

    exam = get_object_or_404(ReadingExam, id=exam_id)

    # Проверка сессии
    try:
        session = ExamSession.objects.get(student=request.user, exam=exam, is_active=True)
        if session.is_expired():
            messages.error(request, "Время истекло! Результаты не засчитаны.")
            session.is_active = False
            session.save()
            return redirect('dashboard')
    except ExamSession.DoesNotExist:
        messages.error(request, "Сессия экзамена не найдена.")
        return redirect('dashboard')

    # Проверка на повторную сдачу
    if StudentResult.objects.filter(student=request.user, exam=exam).exists():
        messages.warning(request, "Вы уже сдавали этот экзамен.")
        return redirect('dashboard')

    questions = exam.questions.all()
    score = 0
    total_questions = questions.count()
    answers_detail = []

    for question in questions:
        is_correct = False
        user_answer = None

        if question.question_type == 'single_choice':
            # Один правильный ответ
            selected_choice_id = request.POST.get(f'question_{question.id}')
            if selected_choice_id:
                choice = Choice.objects.filter(id=selected_choice_id).first()
                if choice:
                    user_answer = choice.text
                    if choice.is_correct:
                        is_correct = True
                        score += 1

        elif question.question_type == 'multiple_choice':
            # Несколько правильных ответов
            selected_choices = request.POST.getlist(f'question_{question.id}')
            correct_choices = set(question.choices.filter(is_correct=True).values_list('id', flat=True))
            selected_set = set([int(c) for c in selected_choices if c.isdigit()])

            user_answer = ", ".join([Choice.objects.get(id=int(c)).text for c in selected_choices if c.isdigit()])

            if selected_set == correct_choices:
                is_correct = True
                score += 1

        elif question.question_type == 'true_false_ng':
            # True/False/Not Given
            selected_choice_id = request.POST.get(f'question_{question.id}')
            if selected_choice_id:
                choice = Choice.objects.filter(id=selected_choice_id).first()
                if choice:
                    user_answer = choice.text
                    if choice.is_correct:
                        is_correct = True
                        score += 1

        elif question.question_type in ['fill_blank', 'sentence_completion']:
            # Заполнение пропусков
            user_text = request.POST.get(f'question_{question.id}', '').strip()
            user_answer = user_text

            # Проверяем на совпадение (можно несколько вариантов через запятую)
            correct_variants = [v.strip().lower() for v in question.correct_answer_text.split(',')]
            if user_text.lower() in correct_variants:
                is_correct = True
                score += 1

        elif question.question_type == 'matching':
            # Matching (соответствие)
            if question.matching_pairs:
                all_correct = True
                user_matches = []

                for idx, pair in enumerate(question.matching_pairs):
                    user_right = request.POST.get(f'question_{question.id}_match_{idx}', '').strip()
                    user_matches.append(f"{pair['left']} → {user_right}")

                    if user_right.lower() != pair['right'].lower():
                        all_correct = False

                user_answer = "; ".join(user_matches)

                if all_correct:
                    is_correct = True
                    score += 1

        # Сохраняем детали ответа
        answers_detail.append({
            'question_id': question.id,
            'question_text': question.text,
            'question_type': question.question_type,
            'user_answer': user_answer,
            'is_correct': is_correct
        })

    percentage = (score / total_questions) * 100 if total_questions > 0 else 0

    # Сохраняем результат
    StudentResult.objects.create(
        student=request.user,
        exam=exam,
        score=score,
        total_questions=total_questions,
        percentage=percentage,
        answers_detail=answers_detail
    )

    # Закрываем сессию
    session.is_active = False
    session.save()

    messages.success(request, f'Тест завершен! Ваш результат: {score}/{total_questions} ({percentage:.1f}%)')
    return redirect('dashboard')