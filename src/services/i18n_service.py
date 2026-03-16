"""Internationalisation service: init() + t() + AUDIO_FILTER."""
from __future__ import annotations

_strings: dict[str, str] = {}

AUDIO_FILTER = "Audio files (*.wav *.mp3 *.ogg *.flac *.aac *.m4a *.opus);;All files (*)"


def init(language: str) -> None:
    """Load translation strings for *language* (``"ja"`` or ``"en"``).

    Must be called once at application startup before any UI is built.
    Falls back to Japanese for unknown language codes.
    """
    global _strings
    if language == "en":
        from src.locale.en import STRINGS
    else:
        from src.locale.ja import STRINGS
    _strings = STRINGS


def t(key: str, **kwargs: object) -> str:
    """Return the translated string for *key*.

    If the key is not found the key itself is returned (never an empty string).
    Keyword arguments are forwarded to :meth:`str.format`; a ``KeyError`` in
    format is silently suppressed and the unformatted template is returned.
    """
    s = _strings.get(key, key)
    if not kwargs:
        return s
    try:
        return s.format(**kwargs)
    except (KeyError, IndexError):
        return s
