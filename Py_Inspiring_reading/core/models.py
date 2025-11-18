from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class ReadingExam(models.Model):
    title = models.CharField("Название теста", max_length=200)
    description = models.TextField("Описание", blank=True)
    passage_text = models.TextField("Текст для чтения (Passage)")
    time_limit_minutes = models.IntegerField("Время (минуты)", default=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_question_types_summary(self):
        """Возвращает сводку по типам вопросов"""
        questions = self.questions.all()
        summary = {}
        for q in questions:
            type_display = q.get_question_type_display()
            summary[type_display] = summary.get(type_display, 0) + 1
        return summary

    class Meta:
        verbose_name = "Экзамен (Reading)"
        verbose_name_plural = "Экзамены"


class Question(models.Model):
    QUESTION_TYPES = [
        ('single_choice', 'Multiple Choice (один ответ)'),
        ('multiple_choice', 'Multiple Choice (несколько ответов)'),
        ('matching', 'Matching (соответствие)'),
        ('fill_blank', 'Fill-in-the-blank (заполнение пропусков)'),
        ('true_false_ng', 'True/False/Not Given'),
        ('sentence_completion', 'Sentence completion'),
    ]

    exam = models.ForeignKey(ReadingExam, related_name='questions', on_delete=models.CASCADE)
    question_type = models.CharField(
        "Тип вопроса",
        max_length=20,
        choices=QUESTION_TYPES,
        default='single_choice'
    )
    text = models.CharField("Текст вопроса", max_length=500)
    order = models.IntegerField("Порядковый номер", default=1)

    # Для Fill-in-the-blank и Sentence completion
    correct_answer_text = models.CharField(
        "Правильный ответ (текст)",
        max_length=200,
        blank=True,
        help_text="Для fill-in-the-blank и sentence completion. Можно через запятую для нескольких вариантов"
    )

    # Для Matching
    matching_pairs = models.JSONField(
        "Пары для Matching",
        blank=True,
        null=True,
        help_text='Формат: [{"left": "A", "right": "1"}, {"left": "B", "right": "2"}]'
    )

    def __str__(self):
        return f"{self.exam.title} - Q{self.order} ({self.get_question_type_display()})"

    class Meta:
        ordering = ['order']
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"


class Choice(models.Model):
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    text = models.CharField("Вариант ответа", max_length=200)
    is_correct = models.BooleanField("Это правильный ответ?", default=False)
    order = models.IntegerField("Порядок", default=1)

    def __str__(self):
        return self.text

    class Meta:
        ordering = ['order']


class StudentResult(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    exam = models.ForeignKey(ReadingExam, on_delete=models.CASCADE)
    score = models.IntegerField("Баллы")
    total_questions = models.IntegerField("Всего вопросов")
    percentage = models.FloatField("Процент")
    completed_at = models.DateTimeField(default=timezone.now)

    # Детали ответов (для review)
    answers_detail = models.JSONField(
        "Детали ответов",
        blank=True,
        null=True,
        help_text="JSON с информацией о каждом ответе"
    )

    def __str__(self):
        return f"{self.student.username} - {self.exam.title}"

    class Meta:
        ordering = ['-completed_at']
        verbose_name = "Результат студента"
        verbose_name_plural = "Результаты студентов"
        unique_together = ['student', 'exam']


class ExamSession(models.Model):
    """Для отслеживания времени начала экзамена"""
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    exam = models.ForeignKey(ReadingExam, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def is_expired(self):
        elapsed = timezone.now() - self.started_at
        return elapsed.total_seconds() > (self.exam.time_limit_minutes * 60)

    def __str__(self):
        return f"{self.student.username} - {self.exam.title} ({self.started_at})"

    class Meta:
        unique_together = ['student', 'exam']
        verbose_name = "Сессия экзамена"
        verbose_name_plural = "Сессии экзаменов"