from django.conf import settings

from .telegram_auth import extract_init_data, parse_telegram_user, validate_init_data

# Пути, которые не открываются в iframe Telegram (кабинет психолога, админка).
_PROTECTED_PREFIXES = ("/psych/", "/admin/", "/ckeditor/")


class TelegramMiniAppMiddleware:
    """Разрешает встраивание в Telegram и подставляет пользователя из initData."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.telegram_user = None
        bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
        if bot_token:
            init_data = extract_init_data(request)
            if init_data:
                parsed = validate_init_data(init_data, bot_token)
                if parsed:
                    request.telegram_user = parse_telegram_user(parsed)
                    request.session["telegram_user"] = request.telegram_user
            elif request.session.get("telegram_user"):
                request.telegram_user = request.session["telegram_user"]

        response = self.get_response(request)

        path = request.path
        if any(path.startswith(prefix) for prefix in _PROTECTED_PREFIXES):
            return response

        if getattr(settings, "TELEGRAM_MINI_APP_ENABLED", True):
            response.headers.pop("X-Frame-Options", None)
            frame_ancestors = getattr(
                settings,
                "TELEGRAM_FRAME_ANCESTORS",
                "https://web.telegram.org https://*.telegram.org https://telegram.org",
            )
            csp_parts = [f"frame-ancestors 'self' {frame_ancestors}"]
            existing = response.get("Content-Security-Policy", "")
            if existing:
                csp_parts.insert(0, existing.rstrip(";"))
            response["Content-Security-Policy"] = "; ".join(csp_parts)

        return response
