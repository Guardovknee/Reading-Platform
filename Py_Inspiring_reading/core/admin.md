from django.contrib import admin
from .models import ReadingExam, Question, Choice, StudentResult

# Inline позволяет добавлять варианты ответов прямо внутри вопроса
class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4  # По умолчанию 4 варианта

# Inline позволяет добавлять вопросы прямо внутри Экзамена
class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    inlines = [ChoiceInline] # (Примечание: Django admin вложенные inlines не поддерживает из коробки просто так,
                             # поэтому мы сделаем проще: Вопросы отдельно, Ответы внутри вопросов,
                             # ИЛИ просто сделаем удобный интерфейс для вопросов).

# Улучшим: Сделаем редактирование Вопрос+Ответы на одной странице
class ChoiceInlineForQuestion(admin.TabularInline):
    model = Choice
    extra = 4

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'exam', 'order']
    list_filter = ['exam']
    inlines = [ChoiceInlineForQuestion]

# Для экзамена сделаем просто список вопросов
class QuestionInlineForExam(admin.TabularInline):
    model = Question
    fields = ['text', 'order']
    extra = 1
    show_change_link = True # Ссылка чтобы редактировать вопрос и добавить ответы

@admin.register(ReadingExam)
class ReadingExamAdmin(admin.ModelAdmin):
    list_display = ['title', 'time_limit_minutes', 'created_at']
    inlines = [QuestionInlineForExam]

@admin.register(StudentResult)
class StudentResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'score', 'total_questions', 'percentage', 'completed_at']
    readonly_fields = ['student', 'exam', 'score', 'total_questions', 'percentage', 'completed_at']