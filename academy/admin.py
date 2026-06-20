from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.html import format_html

from .models import (
    HomeSlide, 
    Psychologist, 
    SocialLink,
    ChildProfile,
    Course,
    Lesson,
    LessonContent,
    TestQuestion,
    TestOption,
    GameScenario,
    GameLocation,
    GameCharacter,
    GameStep,
    GameStepOption,
    BackgroundAsset,
    AvatarPartAsset,
    SavedAvatar,
    GameScene,
    GameSceneObject,
    GameTextElement,
    GameAnswerOption,
    ChildContentResult,
)


User = get_user_model()


class PsychologistAdminForm(forms.ModelForm):
    username = forms.CharField(label="Логин", required=False)
    password = forms.CharField(
        label="Пароль",
        required=False,
        widget=forms.PasswordInput(render_value=True),
        help_text="Заполните, чтобы установить/сменить пароль.",
    )

    class Meta:
        model = Psychologist
        fields = ("first_name", "last_name", "photo", "specialization", "bio")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["photo"].label = "Фото"
        if self.instance and self.instance.user_id:
            self.fields["username"].initial = self.instance.user.username

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if not username:
            return ""
        qs = User.objects.filter(username=username)
        if self.instance and self.instance.user_id:
            qs = qs.exclude(pk=self.instance.user_id)
        if qs.exists():
            raise forms.ValidationError("Этот логин уже занят.")
        return username


class SocialLinkInline(admin.TabularInline):
    """Инлайн для управления социальными сетями"""
    model = SocialLink
    extra = 1
    fields = ('platform', 'url', 'order')
    ordering = ('order',)
    verbose_name = "Социальная ссылка"
    verbose_name_plural = "Социальные ссылки"


@admin.register(Psychologist)
class PsychologistAdmin(admin.ModelAdmin):
    form = PsychologistAdminForm
    inlines = [SocialLinkInline]
    list_display = ("last_name", "first_name", "specialization", "get_username", "social_links_count")
    search_fields = ("last_name", "first_name", "specialization")
    readonly_fields = ("photo_preview",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "username",
                    "password",
                    "first_name",
                    "last_name",
                    "photo",
                    "photo_preview",
                    "specialization",
                    "bio",
                ),
            },
        ),
    )

    def photo_preview(self, obj: Psychologist) -> str:
        if not obj.photo:
            return "—"
        return format_html(
            '<img src="{}" alt="Фото" style="max-height:120px;border-radius:8px;">',
            obj.photo.url,
        )

    photo_preview.short_description = "Текущее фото"

    def get_username(self, obj: Psychologist) -> str:
        return obj.user.username if obj.user_id else ""

    get_username.short_description = "Логин"

    def social_links_count(self, obj: Psychologist) -> str:
        count = obj.social_links.count()
        if count == 0:
            return "❌ Нет"
        return f"✅ {count}"

    social_links_count.short_description = "Соцсети"

    def save_model(self, request, obj: Psychologist, form, change):
        username = form.cleaned_data.get("username") or ""
        password = form.cleaned_data.get("password") or ""

        if username:
            if obj.user_id:
                user = obj.user
                user.username = username
            else:
                user = User(username=username)
            user.is_staff = False
            user.is_superuser = False
            user.is_active = True
            if password:
                user.set_password(password)
            elif not user.pk:
                user.set_unusable_password()
            user.save()
            obj.user = user
        else:
            obj.user = None

        super().save_model(request, obj, form, change)


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ('psychologist', 'get_platform_display', 'url', 'order')
    list_filter = ('platform',)
    search_fields = ('psychologist__last_name', 'psychologist__first_name', 'url')
    ordering = ('psychologist', 'order')

    def get_platform_display(self, obj):
        return obj.get_platform_display()

    get_platform_display.short_description = 'Платформа'


@admin.register(HomeSlide)
class HomeSlideAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "is_active", "has_image")
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "text")
    ordering = ("order", "id")
    readonly_fields = ("image_preview",)
    fields = ("title", "text", "image", "image_preview", "order", "is_active")

    def has_image(self, obj: HomeSlide) -> bool:
        return bool(obj.image)

    has_image.boolean = True
    has_image.short_description = "Фото"

    def image_preview(self, obj: HomeSlide) -> str:
        if not obj.image:
            return "—"
        return format_html(
            '<img src="{}" alt="Превью" style="max-height:120px;border-radius:8px;">',
            obj.image.url,
        )

    image_preview.short_description = "Превью изображения"


@admin.register(ChildProfile)
class ChildProfileAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'age', 'telegram_user_id')
    search_fields = ('first_name', 'last_name', 'telegram_user_id')
    list_filter = ('age',)


class LessonContentInline(admin.TabularInline):
    model = LessonContent
    extra = 1
    fields = ('content_type', 'title', 'order', 'article_body', 'video_url', 'video_file', 'video_preview')
    readonly_fields = ('video_preview_preview',)
    
    def video_preview_preview(self, obj):
        if obj.video_preview:
            return format_html('<img src="{}" style="max-height:100px;"/>', obj.video_preview.url)
        return "—"
    video_preview_preview.short_description = "Превью"


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ('title', 'order', 'is_private')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'psychologist', 'is_published', 'is_private')
    list_filter = ('is_published', 'is_private', 'psychologist')
    search_fields = ('title', 'short_description', 'psychologist__first_name', 'psychologist__last_name')
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'is_private')
    list_filter = ('is_private', 'course')
    search_fields = ('title', 'course__title')
    inlines = [LessonContentInline]


@admin.register(LessonContent)
class LessonContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'content_type', 'order')
    list_filter = ('content_type', 'lesson__course')
    search_fields = ('title', 'article_body')


class TestOptionInline(admin.TabularInline):
    model = TestOption
    extra = 2
    fields = ('option_text', 'score', 'is_correct', 'is_hidden', 'order')


@admin.register(TestQuestion)
class TestQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'content', 'question_type', 'order')
    list_filter = ('question_type', 'answers_view')
    search_fields = ('question_text', 'content__title')
    inlines = [TestOptionInline]


@admin.register(TestOption)
class TestOptionAdmin(admin.ModelAdmin):
    list_display = ('option_text', 'question', 'score', 'is_correct', 'order')
    list_filter = ('is_correct', 'is_hidden')
    search_fields = ('option_text', 'question__question_text')


class GameLocationInline(admin.TabularInline):
    model = GameLocation
    extra = 1


class GameCharacterInline(admin.TabularInline):
    model = GameCharacter
    extra = 1


@admin.register(GameScenario)
class GameScenarioAdmin(admin.ModelAdmin):
    list_display = ('title', 'content')
    search_fields = ('title', 'content__title')
    inlines = [GameLocationInline, GameCharacterInline]


class GameStepOptionInline(admin.TabularInline):
    model = GameStepOption
    extra = 2


@admin.register(GameStep)
class GameStepAdmin(admin.ModelAdmin):
    list_display = ('step_text', 'location', 'character', 'order')
    list_filter = ('location__scenario',)
    search_fields = ('step_text',)
    inlines = [GameStepOptionInline]


@admin.register(GameLocation)
class GameLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'scenario', 'order')
    search_fields = ('name', 'scenario__title')


@admin.register(GameCharacter)
class GameCharacterAdmin(admin.ModelAdmin):
    list_display = ('name', 'scenario')
    search_fields = ('name', 'scenario__title')


@admin.register(BackgroundAsset)
class BackgroundAssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'image_preview')
    search_fields = ('name',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:50px;"/>', obj.image.url)
        return "—"
    image_preview.short_description = "Превью"


@admin.register(AvatarPartAsset)
class AvatarPartAssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'part_type', 'image_preview')
    list_filter = ('part_type',)
    search_fields = ('name',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:50px;"/>', obj.image.url)
        return "—"
    image_preview.short_description = "Превью"


@admin.register(SavedAvatar)
class SavedAvatarAdmin(admin.ModelAdmin):
    list_display = ('name', 'psychologist', 'created_at')
    search_fields = ('name', 'psychologist__first_name', 'psychologist__last_name')
    list_filter = ('created_at',)


class GameSceneObjectInline(admin.TabularInline):
    model = GameSceneObject
    extra = 1


class GameTextElementInline(admin.TabularInline):
    model = GameTextElement
    extra = 1


class GameAnswerOptionInline(admin.TabularInline):
    model = GameAnswerOption
    extra = 2


@admin.register(GameScene)
class GameSceneAdmin(admin.ModelAdmin):
    list_display = ('title', 'content', 'order', 'background')
    list_filter = ('content__lesson__course',)
    search_fields = ('title', 'question_text')
    inlines = [GameSceneObjectInline, GameTextElementInline, GameAnswerOptionInline]


@admin.register(ChildContentResult)
class ChildContentResultAdmin(admin.ModelAdmin):
    list_display = ('child', 'psychologist', 'course', 'total_score', 'created_at')
    list_filter = ('psychologist', 'course', 'created_at')
    search_fields = ('child__first_name', 'child__last_name', 'psychologist__first_name')
    readonly_fields = ('selected_answers', 'ai_summary')