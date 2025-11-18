OLD VERSION OF MODELS.PY 

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

    class Meta:
        verbose_name = "Экзамен (Reading)"
        verbose_name_plural = "Экзамены"


class Question(models.Model):
    exam = models.ForeignKey(ReadingExam, related_name='questions', on_delete=models.CASCADE)
    text = models.CharField("Текст вопроса", max_length=500)
    order = models.IntegerField("Порядковый номер", default=1)

    def __str__(self):
        return f"{self.exam.title} - Q{self.order}"

    class Meta:
        ordering = ['order']
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"


class Choice(models.Model):
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    text = models.CharField("Вариант ответа", max_length=200)
    is_correct = models.BooleanField("Это правильный ответ?", default=False)

    def __str__(self):
        return self.text


class StudentResult(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    exam = models.ForeignKey(ReadingExam, on_delete=models.CASCADE)
    score = models.IntegerField("Баллы")
    total_questions = models.IntegerField("Всего вопросов")
    percentage = models.FloatField("Процент")
    completed_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.student.username} - {self.exam.title}"

    class Meta:
        ordering = ['-completed_at']
        verbose_name = "Результат студента"
        verbose_name_plural = "Результаты студентов"
        # ВАЖНО: Эта строка запрещает дубликаты (пересдачу) на уровне базы данных
        unique_together = ['student', 'exam']