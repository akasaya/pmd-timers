"""Unit tests for src/services/i18n_service."""
from __future__ import annotations

import importlib

import pytest


def _reset_service() -> None:
    """Clear the module-level _strings dict between tests."""
    import src.services.i18n_service as svc
    svc._strings = {}


class TestInit:
    def test_init_ja_loads_japanese(self) -> None:
        from src.services.i18n_service import init, t
        init("ja")
        assert t("phase.working") == "作業中"

    def test_init_en_loads_english(self) -> None:
        from src.services.i18n_service import init, t
        init("en")
        assert t("phase.working") == "Working"

    def test_unknown_language_falls_back_to_japanese(self) -> None:
        from src.services.i18n_service import init, t
        init("fr")  # unsupported → fallback to ja
        assert t("phase.working") == "作業中"

    def test_reinit_switches_language(self) -> None:
        from src.services.i18n_service import init, t
        init("ja")
        assert t("phase.idle") == "待機中"
        init("en")
        assert t("phase.idle") == "Idle"


class TestTranslate:
    def setup_method(self) -> None:
        from src.services.i18n_service import init
        init("en")

    def test_known_key_returns_value(self) -> None:
        from src.services.i18n_service import t
        assert t("phase.short_break") == "Short Break"

    def test_unknown_key_returns_key_itself(self) -> None:
        from src.services.i18n_service import t
        assert t("nonexistent.key") == "nonexistent.key"

    def test_dynamic_format_count(self) -> None:
        from src.services.i18n_service import t
        assert t("widget.today_count", count=7) == "Today: 7"

    def test_dynamic_format_best_day(self) -> None:
        from src.services.i18n_service import t
        result = t("dashboard.chart.best", date="2026-03-16", count=5, total=20)
        assert "2026-03-16" in result
        assert "5" in result
        assert "20" in result

    def test_missing_format_key_returns_template(self) -> None:
        from src.services.i18n_service import t
        # Provide wrong kwargs — should not raise
        result = t("widget.today_count", wrong_key=3)
        assert result == "Today: {count}"

    def test_no_kwargs_returns_plain_string(self) -> None:
        from src.services.i18n_service import t
        assert t("tray.quit") == "Quit"


class TestJaStrings:
    def setup_method(self) -> None:
        from src.services.i18n_service import init
        init("ja")

    def test_streak_unit_ja(self) -> None:
        from src.services.i18n_service import t
        assert t("dashboard.stat.streak_unit", count=3) == "3日"

    def test_settings_suffix_minutes_ja(self) -> None:
        from src.services.i18n_service import t
        assert t("settings.suffix.minutes") == " 分"


class TestEnStrings:
    def setup_method(self) -> None:
        from src.services.i18n_service import init
        init("en")

    def test_streak_unit_en(self) -> None:
        from src.services.i18n_service import t
        assert t("dashboard.stat.streak_unit", count=3) == "3d"

    def test_settings_suffix_minutes_en(self) -> None:
        from src.services.i18n_service import t
        assert t("settings.suffix.minutes") == " min"


class TestAudioFilter:
    def test_audio_filter_is_constant(self) -> None:
        from src.services.i18n_service import AUDIO_FILTER
        assert "*.wav" in AUDIO_FILTER
        assert "*.mp3" in AUDIO_FILTER
