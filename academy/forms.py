from django import forms
from ckeditor_uploader.widgets import CKEditorUploadingWidget

from .models import Course, Lesson, LessonContent, Psychologist, TestOption, TestQuestion


class PsychologistProfileForm(forms.ModelForm):
    class Meta:
        model = Psychologist
        fields = ("first_name", "last_name", "photo", "specialization", "bio")
        labels = {
            "first_name": "Имя",
            "last_name": "Фамилия",
            "photo": "Фото",
            "specialization": "Специализация",
            "bio": "О себе",
        }
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 5}),
            "photo": forms.FileInput(attrs={"accept": "image/*"}),
        }


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ("title", "short_description", "is_published", "is_private")
        labels = {
            "title": "Название курса",
            "short_description": "Короткое описание",
            "is_published": "Опубликован (доступен всем)",
            "is_private": "Закрытый (только по ссылке)",
        }
        help_texts = {
            "is_published": "Нельзя включить вместе с «Закрытый».",
            "is_private": "Нельзя включить вместе с «Опубликован».",
        }

    def clean(self):
        cleaned = super().clean()
        is_published = cleaned.get("is_published")
        is_private = cleaned.get("is_private")
        if is_published and is_private:
            raise forms.ValidationError(
                "Курс не может быть одновременно опубликованным и закрытым по ссылке. "
                "Выберите один вариант доступа."
            )
        return cleaned


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ("title", "order", "is_private")
        labels = {
            "title": "Название урока",
            "order": "Порядок",
            "is_private": "Закрытый урок (только по ссылке)",
        }


class LessonContentForm(forms.ModelForm):
    class Meta:
        model = LessonContent
        fields = ("content_type", "title", "order", "article_body", "video_url", "video_file", "video_preview")
        labels = {
            "content_type": "Тип материала",
            "title": "Заголовок блока",
            "order": "Порядок",
            "article_body": "Текст статьи",
            "video_url": "Ссылка на видео",
            "video_file": "Файл видео",
            "video_preview": "Превью (картинка/файл)",
        }
        widgets = {
            "article_body": CKEditorUploadingWidget(config_name="article_editor"),
            "video_file": forms.FileInput(),
            "video_preview": forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["content_type"].choices = [
            (LessonContent.ARTICLE, "Статья"),
            (LessonContent.VIDEO, "Видео"),
            (LessonContent.TEST, "Тест"),
            (LessonContent.GAME, "Игра"),
        ]

    def clean(self):
        cleaned = super().clean()
        content_type = cleaned.get("content_type")
        article_body = (cleaned.get("article_body") or "").strip()
        video_url = (cleaned.get("video_url") or "").strip()
        video_file = cleaned.get("video_file")

        if content_type == LessonContent.ARTICLE and not article_body:
            self.add_error("article_body", "Для статьи нужен текст.")
        if content_type == LessonContent.VIDEO and not video_url and not video_file:
            self.add_error("video_url", "Для видео укажите ссылку или загрузите файл.")
            self.add_error("video_file", "Для видео укажите ссылку или загрузите файл.")
        return cleaned


class TestQuestionForm(forms.ModelForm):
    class Meta:
        model = TestQuestion
        fields = ("question_text", "image", "question_type", "order")
        labels = {
            "question_text": "Текст вопроса",
            "image": "Картинка к вопросу",
            "question_type": "Тип вопроса",
            "order": "Порядок",
        }
        widgets = {
            "question_text": forms.Textarea(attrs={"rows": 3}),
        }


class TestOptionForm(forms.ModelForm):
    class Meta:
        model = TestOption
        fields = ("option_text", "is_correct", "score")
        labels = {
            "option_text": "Вариант ответа",
            "is_correct": "Правильный вариант",
            "score": "Баллы (дополнительно)",
        }

