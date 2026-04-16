from django.conf import settings
from django.db import models
import uuid
from urllib.parse import parse_qs, urlparse


def generate_private_access_token() -> str:
    return uuid.uuid4().hex


def generate_test_identifier() -> str:
    return uuid.uuid4().hex


class Psychologist(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="psychologist_profile",
    )
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)
    photo_url = models.URLField(blank=True)
    specialization = models.CharField(max_length=255, default="Психолог")
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class ChildProfile(models.Model):
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120, blank=True)
    age = models.PositiveSmallIntegerField(null=True, blank=True)

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or f"Ребёнок #{self.pk}"


class Course(models.Model):
    psychologist = models.ForeignKey(
        Psychologist,
        on_delete=models.CASCADE,
        related_name="courses",
    )
    title = models.CharField(max_length=255)
    short_description = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)
    is_private = models.BooleanField(default=False)
    private_access_token = models.CharField(max_length=32, default=generate_private_access_token, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)
    is_private = models.BooleanField(default=False)
    private_access_token = models.CharField(max_length=32, default=generate_private_access_token, editable=False)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.course.title}: {self.title}"


class LessonContent(models.Model):
    ARTICLE = "article"
    VIDEO = "video"
    TEST = "test"
    GAME = "game"
    TYPE_CHOICES = [
        (ARTICLE, "Статья"),
        (VIDEO, "Видео"),
        (TEST, "Тест"),
        (GAME, "Игра"),
    ]

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="contents")
    content_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)

    article_body = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    video_file = models.FileField(upload_to="lesson_videos/", blank=True, null=True)
    video_preview = models.FileField(upload_to="lesson_video_previews/", blank=True, null=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.get_content_type_display()}: {self.title}"

    def get_video_embed_url(self) -> str:
        if not self.video_url:
            return ""
        parsed = urlparse(self.video_url)
        host = parsed.netloc.lower()
        path = parsed.path.strip("/")

        if "youtu.be" in host:
            video_id = path.split("/")[0]
            return f"https://www.youtube.com/embed/{video_id}" if video_id else ""

        if "youtube.com" in host:
            if path == "watch":
                video_id = parse_qs(parsed.query).get("v", [""])[0]
                return f"https://www.youtube.com/embed/{video_id}" if video_id else ""
            if path.startswith("embed/"):
                return self.video_url

        if "rutube.ru" in host and "/video/" in f"/{path}":
            parts = path.split("/")
            try:
                video_idx = parts.index("video")
                video_id = parts[video_idx + 1]
                return f"https://rutube.ru/play/embed/{video_id}"
            except (ValueError, IndexError):
                return ""

        return self.video_url

    def get_video_preview_url(self) -> str:
        if self.video_preview:
            return self.video_preview.url
        if not self.video_url:
            return ""

        parsed = urlparse(self.video_url)
        host = parsed.netloc.lower()
        path = parsed.path.strip("/")

        if "youtu.be" in host:
            video_id = path.split("/")[0]
            return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg" if video_id else ""

        if "youtube.com" in host:
            if path == "watch":
                video_id = parse_qs(parsed.query).get("v", [""])[0]
                return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg" if video_id else ""
            if path.startswith("embed/"):
                video_id = path.split("/")[1] if len(path.split("/")) > 1 else ""
                return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg" if video_id else ""

        return ""


class TestQuestion(models.Model):
    SINGLE = "single"
    MULTI = "multi"
    OPEN = "open"
    QUESTION_TYPE_CHOICES = [
        (SINGLE, "Один вариант"),
        (MULTI, "Несколько вариантов"),
        (OPEN, "Открытый ответ"),
    ]

    content = models.ForeignKey(
        LessonContent,
        on_delete=models.CASCADE,
        related_name="questions",
        limit_choices_to={"content_type": LessonContent.TEST},
    )
    question_text = models.TextField()
    image = models.ImageField(upload_to="test_questions/", blank=True, null=True)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default=SINGLE)
    order = models.PositiveIntegerField(default=1)
    help_text = models.TextField(blank=True)
    is_required = models.BooleanField(default=True)
    shuffle_options = models.BooleanField(default=False)
    ANSWERS_VIEW_TILE = "tile"
    ANSWERS_VIEW_ROW = "row"
    ANSWERS_VIEW_STARS = "stars"
    ANSWERS_VIEW_CHOICES = [
        (ANSWERS_VIEW_TILE, "Плитка"),
        (ANSWERS_VIEW_ROW, "В один ряд"),
        (ANSWERS_VIEW_STARS, "Звезды"),
    ]
    answers_view = models.CharField(max_length=20, choices=ANSWERS_VIEW_CHOICES, default=ANSWERS_VIEW_TILE)
    identifier = models.CharField(max_length=64, default=generate_test_identifier, editable=False)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.question_text[:100]


class TestOption(models.Model):
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE, related_name="options")
    option_text = models.CharField(max_length=255)
    score = models.IntegerField(default=0)
    is_correct = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=1)
    identifier = models.CharField(max_length=64, default=generate_test_identifier, editable=False)

    def __str__(self):
        return self.option_text


class GameScenario(models.Model):
    content = models.OneToOneField(
        LessonContent,
        on_delete=models.CASCADE,
        related_name="game_scenario",
        limit_choices_to={"content_type": LessonContent.GAME},
    )
    title = models.CharField(max_length=255)
    intro_text = models.TextField(blank=True)

    def __str__(self):
        return self.title


class GameLocation(models.Model):
    scenario = models.ForeignKey(GameScenario, on_delete=models.CASCADE, related_name="locations")
    name = models.CharField(max_length=120)
    background_url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.name


class GameCharacter(models.Model):
    scenario = models.ForeignKey(GameScenario, on_delete=models.CASCADE, related_name="characters")
    name = models.CharField(max_length=120)
    head_asset_url = models.URLField(blank=True)
    body_asset_url = models.URLField(blank=True)
    accessory_asset_url = models.URLField(blank=True)
    default_phrase = models.TextField(blank=True)

    def __str__(self):
        return self.name


class GameStep(models.Model):
    location = models.ForeignKey(GameLocation, on_delete=models.CASCADE, related_name="steps")
    character = models.ForeignKey(
        GameCharacter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="steps",
    )
    step_text = models.TextField()
    open_answer_allowed = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.step_text[:100]


class GameStepOption(models.Model):
    step = models.ForeignKey(GameStep, on_delete=models.CASCADE, related_name="options")
    option_text = models.CharField(max_length=255)
    reaction_score = models.IntegerField(default=0)

    def __str__(self):
        return self.option_text


class BackgroundAsset(models.Model):
    name = models.CharField(max_length=120)
    image = models.ImageField(upload_to="game/backgrounds/")

    def __str__(self):
        return self.name


class AvatarPartAsset(models.Model):
    BODY = "body"
    EYES = "eyes"
    HAIR = "hair"
    CLOTHES = "clothes"
    ACCESSORY = "accessory"
    PART_CHOICES = [
        (BODY, "Тело"),
        (EYES, "Глаза"),
        (HAIR, "Волосы"),
        (CLOTHES, "Одежда"),
        (ACCESSORY, "Аксессуар"),
    ]

    name = models.CharField(max_length=120)
    part_type = models.CharField(max_length=20, choices=PART_CHOICES)
    image = models.ImageField(upload_to="game/avatar_parts/")

    def __str__(self):
        return f"{self.get_part_type_display()}: {self.name}"


class SavedAvatar(models.Model):
    psychologist = models.ForeignKey(Psychologist, on_delete=models.CASCADE, related_name="saved_avatars")
    name = models.CharField(max_length=120)
    body_part = models.ForeignKey(
        AvatarPartAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="avatar_body_uses",
        limit_choices_to={"part_type": AvatarPartAsset.BODY},
    )
    eyes_part = models.ForeignKey(
        AvatarPartAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="avatar_eyes_uses",
        limit_choices_to={"part_type": AvatarPartAsset.EYES},
    )
    hair_part = models.ForeignKey(
        AvatarPartAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="avatar_hair_uses",
        limit_choices_to={"part_type": AvatarPartAsset.HAIR},
    )
    clothes_part = models.ForeignKey(
        AvatarPartAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="avatar_clothes_uses",
        limit_choices_to={"part_type": AvatarPartAsset.CLOTHES},
    )
    accessory_part = models.ForeignKey(
        AvatarPartAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="avatar_accessory_uses",
        limit_choices_to={"part_type": AvatarPartAsset.ACCESSORY},
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class GameScene(models.Model):
    content = models.ForeignKey(
        LessonContent,
        on_delete=models.CASCADE,
        related_name="game_scenes",
        limit_choices_to={"content_type": LessonContent.GAME},
    )
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)
    background = models.ForeignKey(BackgroundAsset, on_delete=models.SET_NULL, null=True, blank=True, related_name="scenes")
    width = models.PositiveIntegerField(default=960)
    height = models.PositiveIntegerField(default=540)
    question_text = models.TextField(blank=True)
    answer_mode = models.CharField(
        max_length=20,
        choices=[("open", "Открытый ответ"), ("choices", "Выбор варианта")],
        default="open",
    )

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class GameSceneObject(models.Model):
    CHARACTER = "character"
    TEXT = "text"
    TYPE_CHOICES = [(CHARACTER, "Персонаж"), (TEXT, "Текст")]

    scene = models.ForeignKey(GameScene, on_delete=models.CASCADE, related_name="scene_objects")
    object_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=CHARACTER)
    name = models.CharField(max_length=120, blank=True)
    avatar = models.ForeignKey(SavedAvatar, on_delete=models.SET_NULL, null=True, blank=True, related_name="scene_objects")
    x = models.FloatField(default=120)
    y = models.FloatField(default=120)
    width = models.FloatField(default=180)
    height = models.FloatField(default=180)
    scale = models.FloatField(default=1.0)
    flip_x = models.BooleanField(default=False)
    z_index = models.IntegerField(default=1)

    def __str__(self):
        return self.name or f"Объект #{self.pk}"


class GameTextElement(models.Model):
    scene = models.ForeignKey(GameScene, on_delete=models.CASCADE, related_name="texts")
    text = models.TextField()
    x = models.FloatField(default=100)
    y = models.FloatField(default=100)
    width = models.FloatField(default=220)
    font_size = models.PositiveIntegerField(default=18)

    def __str__(self):
        return self.text[:60]


class GameAnswerOption(models.Model):
    scene = models.ForeignKey(GameScene, on_delete=models.CASCADE, related_name="answer_options")
    option_text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    score = models.IntegerField(default=0)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.option_text


class ChildContentResult(models.Model):
    child = models.ForeignKey(ChildProfile, on_delete=models.CASCADE, related_name="results")
    psychologist = models.ForeignKey(Psychologist, on_delete=models.CASCADE, related_name="results")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="results")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="results", null=True, blank=True)
    content = models.ForeignKey(
        LessonContent,
        on_delete=models.CASCADE,
        related_name="results",
        null=True,
        blank=True,
    )
    total_score = models.IntegerField(default=0)
    selected_answers = models.JSONField(default=list, blank=True)
    ai_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.child} -> {self.course} ({self.total_score})"
