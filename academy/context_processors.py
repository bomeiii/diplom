from django.conf import settings


def telegram_webapp(request):
    telegram_user = getattr(request, "telegram_user", None)
    return {
        "telegram_user": telegram_user,
        "telegram_mini_app_enabled": getattr(settings, "TELEGRAM_MINI_APP_ENABLED", True),
        "telegram_bot_username": getattr(settings, "TELEGRAM_BOT_USERNAME", ""),
        "mini_app_url": getattr(settings, "TELEGRAM_MINI_APP_URL", ""),
    }
