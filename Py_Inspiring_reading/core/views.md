OLD VERSION OF VIEWS.PY 

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from .models import ReadingExam, Question, Choice, StudentResult


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # СРАЗУ логиним пользователя, чтобы ему не вводить пароль
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('dashboard')
        else:
            # Если ошибки, показываем их
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserCreationForm()

    return render(request, 'register.html', {'form': form})


@login_required
def dashboard(request):
    exams = ReadingExam.objects.all().order_by('-created_at')
    # Получаем ID экзаменов, которые студент уже сдал
    taken_exams_ids = StudentResult.objects.filter(student=request.user).values_list('exam_id', flat=True)

    # Получаем полные объекты результатов для отображения
    results_map = {r.exam_id: r for r in StudentResult.objects.filter(student=request.user)}

    # Подготавливаем данные для шаблона
    exam_data = []
    for exam in exams:
        is_taken = exam.id in taken_exams_ids
        result = results_map.get(exam.id)
        exam_data.append({
            'exam': exam,
            'is_taken': is_taken,
            'result': result
        })

    # Статистика
    user_results = StudentResult.objects.filter(student=request.user)
    total_taken = user_results.count()
    avg_score = 0
    if total_taken > 0:
        avg_score = sum([r.percentage for r in user_results]) / total_taken

    context = {
        'exam_data': exam_data,
        'total_taken': total_taken,
        'avg_score': round(avg_score, 1),
        'results': user_results  # Для списка истории
    }
    return render(request, 'dashboard.html', context)


@login_required
def take_exam(request, exam_id):
    exam = get_object_or_404(ReadingExam, id=exam_id)

    # ПРОВЕРКА: Если уже сдавал - выкидываем на дашборд
    if StudentResult.objects.filter(student=request.user, exam=exam).exists():
        messages.warning(request, "Вы уже сдавали этот экзамен. Пересдача запрещена.")
        return redirect('dashboard')

    return render(request, 'take_exam.html', {'exam': exam})


@login_required
def submit_exam(request, exam_id):
    if request.method != 'POST':
        return redirect('dashboard')

    exam = get_object_or_404(ReadingExam, id=exam_id)

    # Вторая проверка на сервере перед сохранением
    if StudentResult.objects.filter(student=request.user, exam=exam).exists():
        return redirect('dashboard')

    questions = exam.questions.all()
    score = 0
    total_questions = questions.count()

    for question in questions:
        selected_choice_id = request.POST.get(f'question_{question.id}')
        if selected_choice_id:
            choice = Choice.objects.filter(id=selected_choice_id).first()
            if choice and choice.is_correct:
                score += 1

    percentage = (score / total_questions) * 100 if total_questions > 0 else 0

    StudentResult.objects.create(
        student=request.user,
        exam=exam,
        score=score,
        total_questions=total_questions,
        percentage=percentage
    )

    messages.success(request, f'Тест завершен! Результат сохранен.')
    return redirect('dashboard')