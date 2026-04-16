from django.db.models import Avg
import json
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.http import Http404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.urls import reverse

from .forms import CourseForm, LessonContentForm, LessonForm, TestOptionForm, TestQuestionForm
from .models import (
    AvatarPartAsset,
    BackgroundAsset,
    ChildContentResult,
    ChildProfile,
    Course,
    GameAnswerOption,
    GameScene,
    GameSceneObject,
    GameTextElement,
    Lesson,
    LessonContent,
    Psychologist,
    SavedAvatar,
    TestQuestion,
    TestOption,
)


def _delete_lesson_content_files(content: LessonContent) -> None:
    if content.video_file:
        content.video_file.delete(save=False)
    if content.video_preview:
        content.video_preview.delete(save=False)


def home(request: HttpRequest) -> HttpResponse:
    psychologists = Psychologist.objects.all().order_by("last_name", "first_name")
    context = {"psychologists": psychologists}
    return render(request, "academy/home.html", context)


def psychologist_dashboard(request: HttpRequest, psychologist_id: int) -> HttpResponse:
    psychologist = get_object_or_404(Psychologist, pk=psychologist_id)
    courses = psychologist.courses.all().order_by("title")
    context = {
        "psychologist": psychologist,
        "courses": courses,
    }
    return render(request, "academy/psychologist_dashboard.html", context)


def _has_private_course_access(request: HttpRequest, course: Course) -> bool:
    if request.user.is_authenticated and Psychologist.objects.filter(user=request.user, pk=course.psychologist_id).exists():
        return True
    access_token = (request.GET.get("access") or request.POST.get("access") or "").strip()
    return bool(access_token and access_token == course.private_access_token)


def _has_private_lesson_access(request: HttpRequest, lesson: Lesson) -> bool:
    if request.user.is_authenticated and Psychologist.objects.filter(user=request.user, pk=lesson.course.psychologist_id).exists():
        return True
    access_token = (request.GET.get("lesson_access") or request.POST.get("lesson_access") or "").strip()
    return bool(access_token and access_token == lesson.private_access_token)


def course_detail(request: HttpRequest, course_id: int) -> HttpResponse:
    course = get_object_or_404(Course.objects.select_related("psychologist"), pk=course_id)
    if course.is_private and not _has_private_course_access(request, course):
        raise Http404("Курс доступен только по приватной ссылке.")
    lessons = course.lessons.prefetch_related("contents").all()
    access_token = (request.GET.get("access") or "").strip()
    return render(
        request,
        "academy/course_detail.html",
        {"course": course, "lessons": lessons, "access_token": access_token},
    )


def lesson_detail(request: HttpRequest, lesson_id: int) -> HttpResponse:
    lesson = get_object_or_404(Lesson.objects.select_related("course"), pk=lesson_id)
    if lesson.course.is_private and not _has_private_course_access(request, lesson.course):
        raise Http404("Урок доступен только по приватной ссылке.")
    if lesson.is_private and not _has_private_lesson_access(request, lesson):
        raise Http404("Урок доступен только по приватной ссылке.")
    contents = lesson.contents.prefetch_related("questions__options", "game_scenario__locations__steps__options")
    access_token = (request.GET.get("access") or "").strip()
    lesson_access_token = (request.GET.get("lesson_access") or "").strip()
    return render(
        request,
        "academy/lesson_detail.html",
        {
            "lesson": lesson,
            "contents": contents,
            "access_token": access_token,
            "lesson_access_token": lesson_access_token,
        },
    )


@require_http_methods(["POST"])
def submit_test(request: HttpRequest, content_id: int) -> HttpResponse:
    content = get_object_or_404(
        LessonContent.objects.select_related("lesson__course__psychologist"),
        pk=content_id,
        content_type=LessonContent.TEST,
    )
    child_name = request.POST.get("child_name", "").strip() or "Ребёнок"
    course = content.lesson.course
    if course.is_private and not _has_private_course_access(request, course):
        raise Http404("Тест доступен только по приватной ссылке.")
    if content.lesson.is_private and not _has_private_lesson_access(request, content.lesson):
        raise Http404("Тест доступен только по приватной ссылке.")
    child, _ = ChildProfile.objects.get_or_create(first_name=child_name)

    total_score = 0
    open_answers = []
    selected_answers = []
    for question in content.questions.all():
        selected_values = request.POST.getlist(f"q_{question.id}")
        if question.question_type == question.OPEN:
            answer_text = request.POST.get(f"q_{question.id}_open", "").strip()
            if answer_text:
                correct_variants = list(
                    question.options.filter(is_correct=True).values_list("option_text", flat=True)
                )
                selected_answers.append(
                    {
                        "question": question.question_text,
                        "question_type": question.question_type,
                        "selected": answer_text,
                        "correct": correct_variants,
                    }
                )
                open_answers.append(
                    {
                        "question": question.question_text,
                        "answer": answer_text,
                        "correct_variants": correct_variants,
                    }
                )
            continue

        if not selected_values:
            continue

        options_qs = question.options.all()
        selected_ids = {int(v) for v in selected_values if str(v).isdigit()}
        selected_texts = list(options_qs.filter(id__in=selected_ids).values_list("option_text", flat=True))
        correct_texts = list(options_qs.filter(is_correct=True).values_list("option_text", flat=True))
        selected_answers.append(
            {
                "question": question.question_text,
                "question_type": question.question_type,
                "selected": selected_texts,
                "correct": correct_texts,
            }
        )
        correct_ids = set(options_qs.filter(is_correct=True).values_list("id", flat=True))
        if correct_ids:
            # Баллы учитываются только при полностью правильном ответе.
            if selected_ids == correct_ids:
                scored = list(options_qs.filter(id__in=selected_ids))
                score_sum = sum(o.score for o in scored)
                total_score += score_sum if score_sum > 0 else 1
        else:
            options = options_qs.filter(id__in=selected_ids)
            total_score += sum(option.score for option in options)

    ai_summary = build_fake_ai_summary(course=course, lesson=content.lesson, total_score=total_score, open_answers=open_answers)
    ChildContentResult.objects.create(
        child=child,
        psychologist=course.psychologist,
        course=course,
        lesson=content.lesson,
        content=content,
        total_score=total_score,
        selected_answers=selected_answers,
        ai_summary=ai_summary,
    )
    access_token = (request.POST.get("access") or "").strip()
    lesson_access_token = (request.POST.get("lesson_access") or "").strip()
    query_parts = []
    if access_token and access_token == course.private_access_token:
        query_parts.append(f"access={access_token}")
    if lesson_access_token and lesson_access_token == content.lesson.private_access_token:
        query_parts.append(f"lesson_access={lesson_access_token}")
    if query_parts:
        return redirect(f"{reverse('academy:course_detail', kwargs={'course_id': course.id})}?{'&'.join(query_parts)}")
    return redirect("academy:course_detail", course_id=course.id)


@require_http_methods(["POST"])
def submit_game(request: HttpRequest, content_id: int) -> HttpResponse:
    content = get_object_or_404(
        LessonContent.objects.select_related("lesson__course__psychologist"),
        pk=content_id,
        content_type=LessonContent.GAME,
    )
    course = content.lesson.course
    if course.is_private and not _has_private_course_access(request, course):
        raise Http404("Игра доступна только по приватной ссылке.")
    if content.lesson.is_private and not _has_private_lesson_access(request, content.lesson):
        raise Http404("Игра доступна только по приватной ссылке.")

    child_name = request.POST.get("child_name", "").strip() or "Ребёнок"
    child, _ = ChildProfile.objects.get_or_create(first_name=child_name)
    scene_id = request.POST.get("scene_id")
    scene = content.game_scenes.filter(pk=scene_id).first() if scene_id and scene_id.isdigit() else None
    answer_text = (request.POST.get("game_open_answer") or "").strip()
    selected_option_ids = request.POST.getlist("game_option")
    selected_options = []
    correct_options = []
    score = 0

    if scene and scene.answer_mode == "choices":
        selected_ids = {int(x) for x in selected_option_ids if x.isdigit()}
        selected_options = list(scene.answer_options.filter(id__in=selected_ids).values_list("option_text", flat=True))
        correct_options = list(scene.answer_options.filter(is_correct=True).values_list("option_text", flat=True))
        correct_ids = set(scene.answer_options.filter(is_correct=True).values_list("id", flat=True))
        if correct_ids and selected_ids == correct_ids:
            score = 1
        elif not correct_ids:
            score = sum(scene.answer_options.filter(id__in=selected_ids).values_list("score", flat=True))
    else:
        score = 0

    selected_payload = [
        {
            "scene": scene.title if scene else "Сцена",
            "question": scene.question_text if scene else "",
            "question_type": "open" if not scene or scene.answer_mode == "open" else "choices",
            "selected": answer_text if answer_text else selected_options,
            "correct": correct_options,
        }
    ]
    open_answers = []
    if answer_text:
        open_answers.append(
            {
                "question": scene.question_text if scene else "Игровой вопрос",
                "answer": answer_text,
                "correct_variants": correct_options,
            }
        )
    ai_summary = build_fake_ai_summary(course=course, lesson=content.lesson, total_score=score, open_answers=open_answers)
    ChildContentResult.objects.create(
        child=child,
        psychologist=course.psychologist,
        course=course,
        lesson=content.lesson,
        content=content,
        total_score=score,
        selected_answers=selected_payload,
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


@csrf_protect
@require_http_methods(["GET", "POST"])
def psych_login(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        if Psychologist.objects.filter(user=request.user).exists():
            return redirect("academy:psych_dashboard")
        logout(request)

    error = ""
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        user = authenticate(request, username=username, password=password)
        if user is None:
            error = "Неверный логин или пароль."
        else:
            login(request, user)
            return redirect("academy:psych_dashboard")

    return render(request, "psych/login.html", {"error": error})


@login_required
def psych_logout(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect("academy:psych_login")


def _get_current_psychologist(request: HttpRequest) -> Psychologist:
    psychologist = Psychologist.objects.filter(user=request.user).first()
    if psychologist is None:
        raise Psychologist.DoesNotExist
    return psychologist


@login_required
def psych_dashboard(request: HttpRequest) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    courses = psychologist.courses.all().order_by("-created_at")
    return render(request, "psych/dashboard.html", {"psychologist": psychologist, "courses": courses})


@login_required
@require_http_methods(["GET", "POST"])
def psych_course_create(request: HttpRequest) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    form = CourseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        course = form.save(commit=False)
        course.psychologist = psychologist
        course.save()
        return redirect("academy:psych_course_edit", course_id=course.id)
    return render(
        request,
        "psych/course_form.html",
        {"psychologist": psychologist, "form": form, "mode": "create"},
    )


@login_required
@require_http_methods(["GET", "POST"])
def psych_course_edit(request: HttpRequest, course_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    course = get_object_or_404(Course, pk=course_id, psychologist=psychologist)
    form = CourseForm(request.POST or None, instance=course)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("academy:psych_course_edit", course_id=course.id)
    lessons = course.lessons.all().order_by("order", "id")
    return render(
        request,
        "psych/course_edit.html",
        {"psychologist": psychologist, "form": form, "course": course, "lessons": lessons},
    )


@login_required
@require_http_methods(["POST"])
def psych_course_delete(request: HttpRequest, course_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    course = get_object_or_404(Course, pk=course_id, psychologist=psychologist)
    course.delete()
    return redirect("academy:psych_dashboard")


@login_required
@require_http_methods(["GET", "POST"])
def psych_lesson_create(request: HttpRequest) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    course_id = int(request.GET.get("course_id") or 0)
    course = get_object_or_404(Course, pk=course_id, psychologist=psychologist)
    form = LessonForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        lesson = form.save(commit=False)
        lesson.course = course
        lesson.save()
        return redirect("academy:psych_lesson_edit", lesson_id=lesson.id)
    return render(
        request,
        "psych/lesson_form.html",
        {"psychologist": psychologist, "form": form, "course": course, "mode": "create"},
    )


@login_required
@require_http_methods(["GET", "POST"])
def psych_lesson_edit(request: HttpRequest, lesson_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    lesson = get_object_or_404(Lesson, pk=lesson_id, course__psychologist=psychologist)
    form = LessonForm(request.POST or None, instance=lesson)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("academy:psych_lesson_edit", lesson_id=lesson.id)
    contents = lesson.contents.all().order_by("order", "id")
    lesson_results = (
        ChildContentResult.objects.select_related("child", "content")
        .filter(lesson=lesson)
        .order_by("-created_at")[:100]
    )
    return render(
        request,
        "psych/lesson_edit.html",
        {
            "psychologist": psychologist,
            "form": form,
            "lesson": lesson,
            "course": lesson.course,
            "contents": contents,
            "lesson_results": lesson_results,
        },
    )


def _get_psych_content_or_404(psychologist: Psychologist, content_id: int) -> LessonContent:
    return get_object_or_404(LessonContent, pk=content_id, lesson__course__psychologist=psychologist, content_type=LessonContent.TEST)


def _get_psych_game_content_or_404(psychologist: Psychologist, content_id: int) -> LessonContent:
    return get_object_or_404(LessonContent, pk=content_id, lesson__course__psychologist=psychologist, content_type=LessonContent.GAME)


@login_required
def psych_test_editor(request: HttpRequest, content_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    content = _get_psych_content_or_404(psychologist, content_id)
    questions = (
        content.questions.prefetch_related("options")
        .all()
    )
    payload = []
    for q in questions:
        payload.append(
            {
                "id": q.id,
                "question_text": q.question_text,
                "help_text": q.help_text,
                "question_type": q.question_type,
                "is_required": q.is_required,
                "shuffle_options": q.shuffle_options,
                "answers_view": q.answers_view,
                "order": q.order,
                "identifier": q.identifier,
                "has_image": bool(q.image),
                "options": [
                    {
                        "id": o.id,
                        "option_text": o.option_text,
                        "score": o.score,
                        "is_correct": o.is_correct,
                        "is_hidden": o.is_hidden,
                        "order": o.order,
                        "identifier": o.identifier,
                    }
                    for o in q.options.all().order_by("order", "id")
                ],
            }
        )
    return render(
        request,
        "psych/test_editor.html",
        {
            "psychologist": psychologist,
            "content": content,
            "questions": questions,
            "builder_json": json.dumps(payload, ensure_ascii=False),
        },
    )


@login_required
@require_http_methods(["POST"])
def psych_test_builder_save(request: HttpRequest, content_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    content = _get_psych_content_or_404(psychologist, content_id)

    raw_payload = request.POST.get("payload") or ""
    try:
        data = json.loads(raw_payload) if raw_payload else []
    except json.JSONDecodeError:
        data = []

    seen_question_ids: set[int] = set()
    for idx, item in enumerate(data, start=1):
        q_id = item.get("id")
        if q_id:
            question = content.questions.filter(pk=q_id).first()
        else:
            question = None
        if question is None:
            question = TestQuestion(content=content)
        question.question_text = (item.get("question_text") or "").strip()
        question.help_text = (item.get("help_text") or "").strip()
        question.question_type = item.get("question_type") or TestQuestion.SINGLE
        question.is_required = bool(item.get("is_required", True))
        question.shuffle_options = bool(item.get("shuffle_options", False))
        view_value = item.get("answers_view") or TestQuestion.ANSWERS_VIEW_TILE
        if view_value not in dict(TestQuestion.ANSWERS_VIEW_CHOICES):
            view_value = TestQuestion.ANSWERS_VIEW_TILE
        question.answers_view = view_value
        question.order = int(item.get("order") or idx)
        question.save()
        seen_question_ids.add(question.id)

        options = item.get("options") or []
        seen_option_ids: set[int] = set()
        for o_idx, o_item in enumerate(options, start=1):
            o_id = o_item.get("id")
            if o_id:
                opt = question.options.filter(pk=o_id).first()
            else:
                opt = None
            if opt is None:
                opt = TestOption(question=question)
            opt.option_text = (o_item.get("option_text") or "").strip()
            try:
                opt.score = int(o_item.get("score") or 0)
            except (TypeError, ValueError):
                opt.score = 0
            opt.is_correct = bool(o_item.get("is_correct", False))
            opt.is_hidden = bool(o_item.get("is_hidden", False))
            opt.order = int(o_item.get("order") or o_idx)
            opt.save()
            seen_option_ids.add(opt.id)

        # удалить варианты, которых нет в payload
        question.options.exclude(pk__in=seen_option_ids).delete()

    # удалить вопросы, которых нет в payload
    content.questions.exclude(pk__in=seen_question_ids).delete()

    return redirect("academy:psych_test_editor", content_id=content.id)


@login_required
def psych_game_editor(request: HttpRequest, content_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")

    content = _get_psych_game_content_or_404(psychologist, content_id)
    scenes = content.game_scenes.prefetch_related("scene_objects__avatar", "texts", "answer_options", "background").all()
    backgrounds = BackgroundAsset.objects.all().order_by("name")
    avatars = psychologist.saved_avatars.select_related(
        "body_part", "eyes_part", "hair_part", "clothes_part", "accessory_part"
    ).all()
    part_assets = AvatarPartAsset.objects.all().order_by("part_type", "name")
    return render(
        request,
        "psych/game_editor.html",
        {
            "psychologist": psychologist,
            "content": content,
            "scenes": scenes,
            "backgrounds": backgrounds,
            "avatars": avatars,
            "part_assets": part_assets,
        },
    )


@login_required
@require_http_methods(["POST"])
def psych_game_scene_save(request: HttpRequest, content_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    content = _get_psych_game_content_or_404(psychologist, content_id)

    scene_id = request.POST.get("scene_id")
    if scene_id and scene_id.isdigit():
        scene = get_object_or_404(GameScene, pk=int(scene_id), content=content)
    else:
        scene = GameScene(content=content)

    scene.title = (request.POST.get("title") or "").strip() or "Сцена"
    scene.order = int(request.POST.get("order") or 1)
    scene.width = int(request.POST.get("width") or 960)
    scene.height = int(request.POST.get("height") or 540)
    scene.question_text = (request.POST.get("question_text") or "").strip()
    answer_mode = (request.POST.get("answer_mode") or "open").strip()
    scene.answer_mode = answer_mode if answer_mode in {"open", "choices"} else "open"
    bg_id = request.POST.get("background_id")
    scene.background = BackgroundAsset.objects.filter(pk=bg_id).first() if bg_id and bg_id.isdigit() else None
    scene.save()

    raw_objects = request.POST.get("objects_json") or "[]"
    raw_texts = request.POST.get("texts_json") or "[]"
    raw_options = request.POST.get("options_json") or "[]"
    try:
        objects = json.loads(raw_objects)
        texts = json.loads(raw_texts)
        options = json.loads(raw_options)
    except json.JSONDecodeError:
        objects, texts, options = [], [], []

    scene.scene_objects.all().delete()
    for item in objects:
        avatar_id = item.get("avatar_id")
        avatar = SavedAvatar.objects.filter(pk=avatar_id, psychologist=psychologist).first() if avatar_id else None
        GameSceneObject.objects.create(
            scene=scene,
            object_type=GameSceneObject.CHARACTER,
            name=(item.get("name") or "").strip(),
            avatar=avatar,
            x=float(item.get("x") or 120),
            y=float(item.get("y") or 120),
            width=float(item.get("width") or 180),
            height=float(item.get("height") or 180),
            scale=float(item.get("scale") or 1),
            flip_x=bool(item.get("flip_x") or False),
            z_index=int(item.get("z_index") or 1),
        )

    scene.texts.all().delete()
    for item in texts:
        text = (item.get("text") or "").strip()
        if not text:
            continue
        GameTextElement.objects.create(
            scene=scene,
            text=text,
            x=float(item.get("x") or 100),
            y=float(item.get("y") or 100),
            width=float(item.get("width") or 220),
            font_size=int(item.get("font_size") or 18),
        )

    scene.answer_options.all().delete()
    for idx, item in enumerate(options, start=1):
        text = (item.get("option_text") or "").strip()
        if not text:
            continue
        GameAnswerOption.objects.create(
            scene=scene,
            option_text=text,
            is_correct=bool(item.get("is_correct") or False),
            score=int(item.get("score") or 0),
            order=idx,
        )

    return redirect("academy:psych_game_editor", content_id=content.id)


@login_required
@require_http_methods(["POST"])
def psych_game_scene_delete(request: HttpRequest, scene_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    scene = get_object_or_404(GameScene, pk=scene_id, content__lesson__course__psychologist=psychologist)
    content_id = scene.content_id
    scene.delete()
    return redirect("academy:psych_game_editor", content_id=content_id)


@login_required
@require_http_methods(["GET"])
def psych_avatar_builder(request: HttpRequest, content_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    content = _get_psych_game_content_or_404(psychologist, content_id)
    part_assets = AvatarPartAsset.objects.all().order_by("part_type", "name")
    return render(
        request,
        "psych/avatar_builder.html",
        {"psychologist": psychologist, "content": content, "part_assets": part_assets},
    )


@login_required
@require_http_methods(["POST"])
def psych_avatar_create(request: HttpRequest, content_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    content = _get_psych_game_content_or_404(psychologist, content_id)
    name = (request.POST.get("name") or "").strip() or "Персонаж"
    saved = SavedAvatar(
        psychologist=psychologist,
        name=name,
        body_part=AvatarPartAsset.objects.filter(pk=request.POST.get("body_part"), part_type=AvatarPartAsset.BODY).first(),
        eyes_part=AvatarPartAsset.objects.filter(pk=request.POST.get("eyes_part"), part_type=AvatarPartAsset.EYES).first(),
        hair_part=AvatarPartAsset.objects.filter(pk=request.POST.get("hair_part"), part_type=AvatarPartAsset.HAIR).first(),
        clothes_part=AvatarPartAsset.objects.filter(pk=request.POST.get("clothes_part"), part_type=AvatarPartAsset.CLOTHES).first(),
        accessory_part=AvatarPartAsset.objects.filter(pk=request.POST.get("accessory_part"), part_type=AvatarPartAsset.ACCESSORY).first(),
    )
    saved.save()
    return redirect("academy:psych_game_editor", content_id=content.id)


@login_required
@require_http_methods(["GET", "POST"])
def psych_test_question_create(request: HttpRequest, content_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    content = _get_psych_content_or_404(psychologist, content_id)
    form = TestQuestionForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        question = form.save(commit=False)
        question.content = content
        question.save()
        _save_inline_options(question, request)
        return redirect("academy:psych_test_editor", content_id=content.id)
    return render(
        request,
        "psych/test_question_form.html",
        {
            "psychologist": psychologist,
            "content": content,
            "form": form,
            "mode": "create",
            "options_data_json": json.dumps([]),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def psych_test_question_edit(request: HttpRequest, question_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    question = get_object_or_404(TestQuestion, pk=question_id, content__lesson__course__psychologist=psychologist)
    old_image = question.image if question.image else None
    form = TestQuestionForm(request.POST or None, request.FILES or None, instance=question)
    if request.method == "POST" and form.is_valid():
        updated = form.save(commit=False)
        if old_image and updated.image and old_image.name != updated.image.name:
            old_image.delete(save=False)
        updated.save()
        _save_inline_options(updated, request)
        return redirect("academy:psych_test_editor", content_id=question.content_id)
    options_data = list(question.options.values("id", "option_text", "is_correct", "score"))
    return render(
        request,
        "psych/test_question_form.html",
        {
            "psychologist": psychologist,
            "content": question.content,
            "form": form,
            "mode": "edit",
            "options_data_json": json.dumps(options_data, ensure_ascii=False),
        },
    )


def _save_inline_options(question: TestQuestion, request: HttpRequest) -> None:
    if question.question_type == TestQuestion.OPEN:
        question.options.all().delete()
        return

    texts = request.POST.getlist("option_text[]")
    correct_indexes = {int(x) for x in request.POST.getlist("option_correct[]") if x.isdigit()}
    scores = request.POST.getlist("option_score[]")

    question.options.all().delete()
    for idx, text in enumerate(texts):
        cleaned = text.strip()
        if not cleaned:
            continue
        raw_score = scores[idx] if idx < len(scores) else "0"
        try:
            score = int(raw_score)
        except ValueError:
            score = 0
        TestOption.objects.create(
            question=question,
            option_text=cleaned,
            is_correct=idx in correct_indexes,
            score=score,
        )


@login_required
@require_http_methods(["POST"])
def psych_test_question_delete(request: HttpRequest, question_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    question = get_object_or_404(TestQuestion, pk=question_id, content__lesson__course__psychologist=psychologist)
    content_id = question.content_id
    question.delete()
    return redirect("academy:psych_test_editor", content_id=content_id)


@login_required
@require_http_methods(["POST"])
def psych_test_question_remove_image(request: HttpRequest, question_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    question = get_object_or_404(TestQuestion, pk=question_id, content__lesson__course__psychologist=psychologist)
    if question.image:
        question.image.delete(save=False)
        question.image = None
        question.save(update_fields=["image"])
    return redirect("academy:psych_test_question_edit", question_id=question.id)


@login_required
@require_http_methods(["GET", "POST"])
def psych_test_option_create(request: HttpRequest, question_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    question = get_object_or_404(TestQuestion, pk=question_id, content__lesson__course__psychologist=psychologist)
    form = TestOptionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        option = form.save(commit=False)
        option.question = question
        option.save()
        return redirect("academy:psych_test_editor", content_id=question.content_id)
    return render(request, "psych/test_option_form.html", {"psychologist": psychologist, "question": question, "form": form, "mode": "create"})


@login_required
@require_http_methods(["GET", "POST"])
def psych_test_option_edit(request: HttpRequest, option_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    option = get_object_or_404(TestOption, pk=option_id, question__content__lesson__course__psychologist=psychologist)
    form = TestOptionForm(request.POST or None, instance=option)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("academy:psych_test_editor", content_id=option.question.content_id)
    return render(request, "psych/test_option_form.html", {"psychologist": psychologist, "question": option.question, "form": form, "mode": "edit"})


@login_required
@require_http_methods(["POST"])
def psych_test_option_delete(request: HttpRequest, option_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    option = get_object_or_404(TestOption, pk=option_id, question__content__lesson__course__psychologist=psychologist)
    content_id = option.question.content_id
    option.delete()
    return redirect("academy:psych_test_editor", content_id=content_id)


@login_required
@require_http_methods(["POST"])
def psych_result_delete(request: HttpRequest, result_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    result = get_object_or_404(ChildContentResult, pk=result_id, lesson__course__psychologist=psychologist)
    lesson_id = result.lesson_id
    result.delete()
    return redirect("academy:psych_lesson_edit", lesson_id=lesson_id)


@login_required
@require_http_methods(["POST"])
def psych_lesson_results_delete_all(request: HttpRequest, lesson_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    lesson = get_object_or_404(Lesson, pk=lesson_id, course__psychologist=psychologist)
    ChildContentResult.objects.filter(lesson=lesson).delete()
    return redirect("academy:psych_lesson_edit", lesson_id=lesson.id)


@login_required
@require_http_methods(["POST"])
def psych_lesson_delete(request: HttpRequest, lesson_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    lesson = get_object_or_404(Lesson, pk=lesson_id, course__psychologist=psychologist)
    course_id = lesson.course_id
    lesson.delete()
    return redirect("academy:psych_course_edit", course_id=course_id)


@login_required
@require_http_methods(["GET", "POST"])
def psych_content_create(request: HttpRequest) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    lesson_id = int(request.GET.get("lesson_id") or 0)
    lesson = get_object_or_404(Lesson, pk=lesson_id, course__psychologist=psychologist)
    form = LessonContentForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        content = form.save(commit=False)
        content.lesson = lesson
        content.save()
        if content.content_type == LessonContent.TEST:
            return redirect("academy:psych_test_editor", content_id=content.id)
        return redirect("academy:psych_lesson_edit", lesson_id=lesson.id)
    return render(
        request,
        "psych/content_form.html",
        {"psychologist": psychologist, "form": form, "lesson": lesson, "course": lesson.course, "mode": "create"},
    )


@login_required
@require_http_methods(["GET", "POST"])
def psych_content_edit(request: HttpRequest, content_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    content = get_object_or_404(LessonContent, pk=content_id, lesson__course__psychologist=psychologist)
    old_video_file = content.video_file if content.video_file else None
    old_video_preview = content.video_preview if content.video_preview else None
    form = LessonContentForm(request.POST or None, request.FILES or None, instance=content)
    if request.method == "POST" and form.is_valid():
        updated = form.save(commit=False)

        if old_video_file and updated.video_file and old_video_file.name != updated.video_file.name:
            old_video_file.delete(save=False)
        if old_video_preview and updated.video_preview and old_video_preview.name != updated.video_preview.name:
            old_video_preview.delete(save=False)

        updated.save()
        return redirect("academy:psych_lesson_edit", lesson_id=content.lesson_id)
    return render(
        request,
        "psych/content_form.html",
        {
            "psychologist": psychologist,
            "form": form,
            "lesson": content.lesson,
            "course": content.lesson.course,
            "mode": "edit",
        },
    )


@login_required
@require_http_methods(["POST"])
def psych_content_remove_video_file(request: HttpRequest, content_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    content = get_object_or_404(LessonContent, pk=content_id, lesson__course__psychologist=psychologist)
    if content.video_file:
        content.video_file.delete(save=False)
        content.video_file = None
        content.save(update_fields=["video_file"])
    return redirect("academy:psych_content_edit", content_id=content.id)


@login_required
@require_http_methods(["POST"])
def psych_content_remove_video_preview(request: HttpRequest, content_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    content = get_object_or_404(LessonContent, pk=content_id, lesson__course__psychologist=psychologist)
    if content.video_preview:
        content.video_preview.delete(save=False)
        content.video_preview = None
        content.save(update_fields=["video_preview"])
    return redirect("academy:psych_content_edit", content_id=content.id)


@login_required
@require_http_methods(["POST"])
def psych_content_delete(request: HttpRequest, content_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")
    content = get_object_or_404(LessonContent, pk=content_id, lesson__course__psychologist=psychologist)
    lesson_id = content.lesson_id
    _delete_lesson_content_files(content)
    content.delete()
    return redirect("academy:psych_lesson_edit", lesson_id=lesson_id)


@login_required
@require_http_methods(["POST"])
def psych_contents_reorder(request: HttpRequest, lesson_id: int) -> HttpResponse:
    try:
        psychologist = _get_current_psychologist(request)
    except Psychologist.DoesNotExist:
        logout(request)
        return redirect("academy:psych_login")

    lesson = get_object_or_404(Lesson, pk=lesson_id, course__psychologist=psychologist)
    ordered_ids_raw = (request.POST.get("ordered_ids") or "").strip()
    if not ordered_ids_raw:
        return redirect("academy:psych_lesson_edit", lesson_id=lesson.id)

    ordered_ids = []
    for value in ordered_ids_raw.split(","):
        value = value.strip()
        if value.isdigit():
            ordered_ids.append(int(value))

    valid_contents = {c.id: c for c in lesson.contents.all()}
    position = 1
    for content_id in ordered_ids:
        content = valid_contents.get(content_id)
        if content is None:
            continue
        content.order = position
        content.save(update_fields=["order"])
        position += 1
    return redirect("academy:psych_lesson_edit", lesson_id=lesson.id)


def build_fake_ai_summary(course: Course, lesson: Lesson, total_score: int, open_answers: list[dict]) -> str:
    if total_score <= 3:
        mood = "повышенная тревожность"
    elif total_score <= 7:
        mood = "умеренная устойчивость"
    else:
        mood = "высокая уверенность"

    if open_answers:
        lines = []
        for idx, item in enumerate(open_answers[:5], start=1):
            correct_variants = item.get("correct_variants") or []
            correct_text = ", ".join(correct_variants) if correct_variants else "не задан"
            lines.append(
                f"{idx}) Курс: {course.title}\n"
                f"   Урок: {lesson.title}\n"
                f"   Вопрос: {item.get('question')}\n"
                f"   Ответ ребёнка: {item.get('answer')}\n"
                f"   Правильный вариант: {correct_text}"
            )
        open_block = "\n".join(lines)
    else:
        open_block = "Открытые ответы не заполнены."
    return (
        "AI-анализ (демо):\n"
        f"Предполагаемая реакция: {mood}.\n"
        f"Суммарный балл: {total_score}.\n"
        "Рекомендация психологу: уточнить контекст в личной беседе.\n"
        f"{open_block}"
    )

# Create your views here.
