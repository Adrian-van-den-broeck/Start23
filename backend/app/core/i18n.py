"""Athlete language for server-authored public text.

Dutch is the product default. English is used only when the client asks for it
through the standard ``Accept-Language`` header. The language changes wording
only; it never changes codes, values, rules or persisted records.
"""

from collections.abc import Mapping
from contextvars import ContextVar
from typing import Final, Literal

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

Language = Literal["nl", "en"]
LocalizedText = Mapping[Language, str]

DEFAULT_LANGUAGE: Final[Language] = "nl"
_SUPPORTED: Final[Mapping[str, Language]] = {"nl": "nl", "en": "en"}
_MAX_HEADER_LENGTH: Final = 512

_request_language: ContextVar[Language] = ContextVar(
    "athlete_language",
    default=DEFAULT_LANGUAGE,
)


def resolve_language(accept_language: str | None) -> Language:
    """Pick nl or en from an Accept-Language value; anything else is Dutch."""
    if not accept_language:
        return DEFAULT_LANGUAGE
    best: tuple[float, Language] | None = None
    for entry in accept_language[:_MAX_HEADER_LENGTH].split(","):
        tag, _, parameters = entry.partition(";")
        language = _SUPPORTED.get(tag.strip().split("-")[0].lower())
        if language is None:
            continue
        quality = 1.0
        for parameter in parameters.split(";"):
            name, _, value = parameter.partition("=")
            if name.strip().lower() == "q":
                try:
                    quality = float(value.strip())
                except ValueError:
                    quality = 0.0
        if not 0.0 < quality <= 1.0:
            continue
        if best is None or quality > best[0]:
            best = (quality, language)
    return DEFAULT_LANGUAGE if best is None else best[1]


def current_language() -> Language:
    """Return the language of the request being served (Dutch outside requests)."""
    return _request_language.get()


class LanguageMiddleware:
    """Expose the requested athlete language to public response serializers."""

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        language = resolve_language(Headers(scope=scope).get("accept-language"))

        async def send_with_language(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["Content-Language"] = language
                headers.add_vary_header("Accept-Language")
            await send(message)

        token = _request_language.set(language)
        try:
            await self._app(scope, receive, send_with_language)
        finally:
            _request_language.reset(token)
