from django.db.models import Avg
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .models import (
    ChildContentResult,
    ChildProfile,
    Course,
    Lesson,
    LessonContent,
    Psychologist,
    TestOption,
)


def home(request: HttpRequest) -> HttpResponse:
    psychologists = Psychologist.objects.all().order_by("last_name", "first_name")
    context = {"psychologists": psychologists}
    return render(request, "academy/home.html", context)


def psychologist_dashboard(request: HttpRequest, psychologist_id: int) -> HttpResponse:
    psychologist = get_object_or_404(Psychologist, pk=psychologist_id)
    courses = psychologist.courses.all().order_by("title")
    child_results = psychologist.results.select_related("child", "course").all()[:100]
    context = {
        "psychologist": psychologist,
        "courses": courses,
        "child_results": child_results,
    }
    return render(request, "academy/psychologist_dashboard.html", context)


def course_detail(request: HttpRequest, course_id: int) -> HttpResponse:
    course = get_object_or_404(Course.objects.select_related("psychologist"), pk=course_id)
    lessons = course.lessons.prefetch_related("contents").all()
    return render(
        request,
        "academy/course_detail.html",
        {"course": course, "lessons": lessons},
    )


def lesson_detail(request: HttpRequest, lesson_id: int) -> HttpResponse:
    lesson = get_object_or_404(Lesson.objects.select_related("course"), pk=lesson_id)
    contents = lesson.contents.prefetch_related("questions__options", "game_scenario__locations__steps__options")
    return render(
        request,
        "academy/lesson_detail.html",
        {"lesson": lesson, "contents": contents},
    )


@require_http_methods(["POST"])
def submit_test(request: HttpRequest, content_id: int) -> HttpResponse:
    content = get_object_or_404(
        LessonContent.objects.select_related("lesson__course__psychologist"),
        pk=content_id,
        content_type=LessonContent.TEST,
    )
    child_name = request.POST.get("child_name", "").strip() or "Ребёнок"
    child, _ = ChildProfile.objects.get_or_create(first_name=child_name)

    total_score = 0
    open_answers = []
    for question in content.questions.all():
        selected_values = request.POST.getlist(f"q_{question.id}")
        if question.question_type == question.OPEN:
            answer_text = request.POST.get(f"q_{question.id}_open", "").strip()
            if answer_text:
                open_answers.append(f"Вопрос: {question.question_text}\nОтвет: {answer_text}")
            continue

        if not selected_values:
            continue

        options = TestOption.objects.filter(question=question, id__in=selected_values)
        total_score += sum(option.score for option in options)

    ai_summary = build_fake_ai_summary(total_score, open_answers)
    course = content.lesson.course
    ChildContentResult.objects.create(
        child=child,
        psychologist=course.psychologist,
        course=course,
        lesson=content.lesson,
        content=content,
        total_score=total_score,
        ai_summary=ai_summary,
    )
    return redirect("academy:course_detail", course_id=course.id)


def analytics_overview(request: HttpRequest) -> HttpResponse:
    rows = (
        ChildContentResult.objects.select_related("psychologist")
        .values("psychologist__last_name", "psychologist__first_name")
        .annotate(avg_score=Avg("total_score"))
        .order_by("psychologist__last_name")
    )
    return render(request, "academy/analytics_overview.html", {"rows": rows})


def build_fake_ai_summary(total_score: int, open_answers: list[str]) -> str:
    if total_score <= 3:
        mood = "повышенная тревожность"
    elif total_score <= 7:
        mood = "умеренная устойчивость"
    else:
        mood = "высокая уверенность"

    open_block = "\n".join(open_answers[:3]) if open_answers else "Открытые ответы не заполнены."
    return (
        "AI-анализ (демо):\n"
        f"Предполагаемая реакция: {mood}.\n"
        f"Суммарный балл: {total_score}.\n"
        "Рекомендация психологу: уточнить контекст в личной беседе.\n"
        f"{open_block}"
    )

# Create your views here.
