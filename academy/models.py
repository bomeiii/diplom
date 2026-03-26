from django.db import models


class Psychologist(models.Model):
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
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)

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

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.get_content_type_display()}: {self.title}"


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
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default=SINGLE)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.question_text[:100]


class TestOption(models.Model):
    question = models.ForeignKey(TestQuestion, on_delete=models.CASCADE, related_name="options")
    option_text = models.CharField(max_length=255)
    score = models.IntegerField(default=0)

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
    ai_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.child} -> {self.course} ({self.total_score})"
