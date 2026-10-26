"""Shared dark palette and Japanese font fallback for Windows / WSLg."""

from pathlib import Path

from PyQt6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PyQt6.QtWidgets import QApplication


def apply_appearance(app: QApplication) -> None:
    app.setStyle("Fusion")
    if not QFontDatabase.families(QFontDatabase.WritingSystem.Japanese):
        for name in ("YuGothR.ttc", "YuGothB.ttc"):
            path = Path("/mnt/c/Windows/Fonts") / name
            if path.is_file():
                QFontDatabase.addApplicationFont(str(path))
    for family in ("Yu Gothic UI", "Yu Gothic", "Noto Sans CJK JP"):
        if family in QFontDatabase.families():
            app.setFont(QFont(family, 10))
            break
    palette = QPalette()
    for role, color in {
        QPalette.ColorRole.Window: "#1b2534",
        QPalette.ColorRole.WindowText: "#edf3f8",
        QPalette.ColorRole.Base: "#131c29",
        QPalette.ColorRole.AlternateBase: "#243044",
        QPalette.ColorRole.Text: "#edf3f8",
        QPalette.ColorRole.Button: "#2a384c",
        QPalette.ColorRole.ButtonText: "#edf3f8",
        QPalette.ColorRole.Highlight: "#86e1c3",
        QPalette.ColorRole.HighlightedText: "#102b27",
        QPalette.ColorRole.ToolTipBase: "#243044",
        QPalette.ColorRole.ToolTipText: "#edf3f8",
    }.items():
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
