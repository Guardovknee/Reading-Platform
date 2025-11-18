from django.contrib import admin
from django import forms
from .models import ReadingExam, Question, Choice, StudentResult, ExamSession


class ChoiceInlineForQuestion(admin.TabularInline):
    model = Choice
    extra = 4
    fields = ['text', 'is_correct', 'order']


class QuestionAdminForm(forms.ModelForm):
    """Кастомная форма для динамического отображения полей"""

    class Meta:
        model = Question
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем helptext в зависимости от типа
        self.fields['correct_answer_text'].help_text = (
            "📝 Для Fill-in-the-blank и Sentence completion. "
            "Можно указать несколько вариантов через запятую (например: answer, Answer, ANSWER)"
        )
        self.fields['matching_pairs'].help_text = (
            '🔗 Только для Matching. Формат JSON: '
            '[{"left": "Вопрос 1", "right": "Ответ A"}, {"left": "Вопрос 2", "right": "Ответ B"}]'
        )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    form = QuestionAdminForm
    list_display = ['text', 'exam', 'question_type', 'order', 'colored_type']
    list_filter = ['exam', 'question_type']
    search_fields = ['text', 'exam__title']
    inlines = [ChoiceInlineForQuestion]

    fieldsets = (
        ('Основная информация', {
            'fields': ('exam', 'question_type', 'text', 'order')
        }),
        ('Настройки для Multiple Choice', {
            'fields': (),
            'description': '⬇️ Используйте таблицу "Choices" ниже для добавления вариантов ответов'
        }),
        ('Настройки для Fill-in-the-blank / Sentence completion', {
            'fields': ('correct_answer_text',),
            'classes': ('collapse',),
        }),
        ('Настройки для Matching', {
            'fields': ('matching_pairs',),
            'classes': ('collapse',),
        }),
    )

    def colored_type(self, obj):
        colors = {
            'single_choice': '#4CAF50',
            'multiple_choice': '#2196F3',
            'matching': '#FF9800',
            'fill_blank': '#9C27B0',
            'true_false_ng': '#F44336',
            'sentence_completion': '#00BCD4',
        }
        color = colors.get(obj.question_type, '#757575')
        return f'<span style="background:{color}; color:white; padding:3px 10px; border-radius:5px; font-size:11px; font-weight:bold;">{obj.get_question_type_display()}</span>'

    colored_type.short_description = 'Тип'
    colored_type.allow_tags = True

    def get_inline_instances(self, request, obj=None):
        """Показывать Choices только для Multiple Choice вопросов"""
        if obj and obj.question_type in ['single_choice', 'multiple_choice', 'true_false_ng']:
            return super().get_inline_instances(request, obj)
        return []


class QuestionInlineForExam(admin.TabularInline):
    model = Question
    fields = ['order', 'question_type', 'text', 'edit_link']
    readonly_fields = ['edit_link']
    extra = 1
    show_change_link = True

    def edit_link(self, obj):
        if obj.pk:
            return f'<a href="/admin/core/question/{obj.pk}/change/" target="_blank">✏️ Редактировать подробно</a>'
        return '-'

    edit_link.short_description = 'Действия'
    edit_link.allow_tags = True


@admin.register(ReadingExam)
class ReadingExamAdmin(admin.ModelAdmin):
    list_display = ['title', 'time_limit_minutes', 'question_count', 'types_summary', 'created_at']
    inlines = [QuestionInlineForExam]
    search_fields = ['title', 'description']

    def question_count(self, obj):
        count = obj.questions.count()
        return f"📝 {count} вопрос(ов)"

    question_count.short_description = 'Количество вопросов'

    def types_summary(self, obj):
        summary = obj.get_question_types_summary()
        if not summary:
            return "Нет вопросов"

        icons = {
            'Multiple Choice (один ответ)': '🔘',
            'Multiple Choice (несколько ответов)': '☑️',
            'Matching (соответствие)': '🔗',
            'Fill-in-the-blank (заполнение пропусков)': '📝',
            'True/False/Not Given': '✓✗',
            'Sentence completion': '📄',
        }

        result = []
        for q_type, count in summary.items():
            icon = icons.get(q_type, '❓')
            result.append(f"{icon} {count}")

        return " | ".join(result)

    types_summary.short_description = 'Типы вопросов'


@admin.register(StudentResult)
class StudentResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'score', 'total_questions', 'percentage_display', 'completed_at']
    list_filter = ['exam', 'completed_at']
    search_fields = ['student__username', 'exam__title']
    readonly_fields = ['student', 'exam', 'score', 'total_questions', 'percentage', 'completed_at', 'answers_detail']
    date_hierarchy = 'completed_at'

    def percentage_display(self, obj):
        if obj.percentage >= 80:
            color = '#4CAF50'
            emoji = '🌟'
        elif obj.percentage >= 50:
            color = '#FF9800'
            emoji = '👍'
        else:
            color = '#F44336'
            emoji = '📚'
        return f'<span style="background:{color}; color:white; padding:5px 12px; border-radius:8px; font-weight:bold;">{emoji} {obj.percentage:.1f}%</span>'

    percentage_display.short_description = 'Процент'
    percentage_display.allow_tags = True


@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'started_at', 'is_active', 'is_expired']
    list_filter = ['is_active', 'started_at']
    search_fields = ['student__username', 'exam__title']
    readonly_fields = ['started_at']

    def is_expired(self, obj):
        if obj.is_expired():
            return '⏰ Истекло'
        return '✅ Активно'

    is_expired.short_description = 'Статус'