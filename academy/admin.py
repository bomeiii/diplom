from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Psychologist


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
        fields = ("first_name", "last_name", "photo_url", "specialization", "bio")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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


@admin.register(Psychologist)
class PsychologistAdmin(admin.ModelAdmin):
    form = PsychologistAdminForm
    list_display = ("last_name", "first_name", "specialization", "get_username")
    search_fields = ("last_name", "first_name", "specialization")

    def get_username(self, obj: Psychologist) -> str:
        return obj.user.username if obj.user_id else ""

    get_username.short_description = "Логин"

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
