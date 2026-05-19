from __future__ import annotations

from django.http import HttpRequest

from .models import ChildProfile


def resolve_child_profile(request: HttpRequest) -> tuple[ChildProfile, bool]:
    """
    Возвращает профиль ребёнка и флаг, подставлен ли он из Telegram.
    """
    telegram_user = getattr(request, "telegram_user", None)
    if telegram_user:
        tg_id = int(telegram_user["id"])
        first_name = (telegram_user.get("first_name") or "").strip() or "Пользователь"
        last_name = (telegram_user.get("last_name") or "").strip()
        child, _ = ChildProfile.objects.get_or_create(
            telegram_user_id=tg_id,
            defaults={"first_name": first_name, "last_name": last_name},
        )
        updated = False
        if first_name and child.first_name != first_name:
            child.first_name = first_name
            updated = True
        if last_name and child.last_name != last_name:
            child.last_name = last_name
            updated = True
        if updated:
            child.save(update_fields=["first_name", "last_name"])
        return child, True

    child_name = (request.POST.get("child_name") or "").strip() or "Ребёнок"
    child, _ = ChildProfile.objects.get_or_create(first_name=child_name)
    return child, False
