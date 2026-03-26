from django.contrib import admin
from .models import (
    ChildContentResult,
    ChildProfile,
    Course,
    GameCharacter,
    GameLocation,
    GameScenario,
    GameStep,
    GameStepOption,
    Lesson,
    LessonContent,
    Psychologist,
    TestOption,
    TestQuestion,
)


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "psychologist", "is_published", "is_private", "created_at")
    list_filter = ("is_published", "is_private", "psychologist")
    search_fields = ("title", "short_description")
    inlines = [LessonInline]


class LessonContentInline(admin.TabularInline):
    model = LessonContent
    extra = 0


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    list_filter = ("course",)
    search_fields = ("title",)
    inlines = [LessonContentInline]


class TestOptionInline(admin.TabularInline):
    model = TestOption
    extra = 0


@admin.register(TestQuestion)
class TestQuestionAdmin(admin.ModelAdmin):
    list_display = ("question_text", "content", "question_type", "order")
    list_filter = ("question_type", "content")
    inlines = [TestOptionInline]


class GameStepOptionInline(admin.TabularInline):
    model = GameStepOption
    extra = 0


@admin.register(GameStep)
class GameStepAdmin(admin.ModelAdmin):
    list_display = ("step_text", "location", "character", "open_answer_allowed", "order")
    list_filter = ("location", "open_answer_allowed")
    inlines = [GameStepOptionInline]


@admin.register(Psychologist)
class PsychologistAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "specialization")
    search_fields = ("last_name", "first_name", "specialization")


@admin.register(ChildProfile)
class ChildProfileAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "age")
    search_fields = ("first_name", "last_name")


@admin.register(LessonContent)
class LessonContentAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson", "content_type", "order")
    list_filter = ("content_type",)
    search_fields = ("title", "article_body")


@admin.register(GameScenario)
class GameScenarioAdmin(admin.ModelAdmin):
    list_display = ("title", "content")


@admin.register(GameLocation)
class GameLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "scenario", "order")
    list_filter = ("scenario",)


@admin.register(GameCharacter)
class GameCharacterAdmin(admin.ModelAdmin):
    list_display = ("name", "scenario")
    list_filter = ("scenario",)


@admin.register(ChildContentResult)
class ChildContentResultAdmin(admin.ModelAdmin):
    list_display = ("child", "psychologist", "course", "total_score", "created_at")
    list_filter = ("psychologist", "course")
    search_fields = ("child__first_name", "child__last_name", "ai_summary")
