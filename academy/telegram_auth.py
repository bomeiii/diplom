"""Валидация initData Telegram Mini App (Web App)."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any
from urllib.parse import parse_qsl

INIT_DATA_MAX_AGE_SECONDS = 86400


def validate_init_data(init_data: str, bot_token: str, *, max_age_seconds: int = INIT_DATA_MAX_AGE_SECONDS) -> dict[str, Any] | None:
    """Проверяет подпись initData и возвращает распарсенные поля или None."""
    if not init_data or not bot_token:
        return None

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated_hash, received_hash):
        return None

    auth_date_raw = parsed.get("auth_date")
    if auth_date_raw:
        try:
            auth_date = int(auth_date_raw)
        except (TypeError, ValueError):
            return None
        if time.time() - auth_date > max_age_seconds:
            return None

    return parsed


def parse_telegram_user(parsed_init_data: dict[str, Any]) -> dict[str, Any] | None:
    user_raw = parsed_init_data.get("user")
    if not user_raw:
        return None
    try:
        user = json.loads(user_raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(user, dict) or "id" not in user:
        return None
    return user


def extract_init_data(request) -> str:
    header = (request.headers.get("X-Telegram-Init-Data") or "").strip()
    if header:
        return header
    return (request.POST.get("telegram_init_data") or request.GET.get("tgWebAppData") or "").strip()
