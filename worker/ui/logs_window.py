"""Separate window for advanced worker logs."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QPlainTextEdit, QVBoxLayout, QWidget


class LogWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Search Helper — Logs")
        self.setMinimumSize(720, 480)
        self.resize(800, 560)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        hint = QLabel("Worker output from the most recent runs.")
        hint.setObjectName("FieldHint")
        layout.addWidget(hint)

        self._view = QPlainTextEdit()
        self._view.setObjectName("LogView")
        self._view.setReadOnly(True)
        self._view.setMaximumBlockCount(5000)
        layout.addWidget(self._view, 1)

        self.setCentralWidget(central)

    def set_content(self, text: str) -> None:
        self._view.setPlainText(text)

    def clear(self) -> None:
        self._view.clear()

    def append_line(self, line: str) -> None:
        self._view.appendPlainText(line)
        bar = self._view.verticalScrollBar()
        bar.setValue(bar.maximum())

    def closeEvent(self, event) -> None:  # noqa: ANN001 — Qt signature
        event.accept()
        self.hide()
