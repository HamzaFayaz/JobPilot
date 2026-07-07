"""Reusable widgets for Search Helper desktop UI."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

WEBBRIDGE_INSTALL_URL = "https://www.kimi.com/features/webbridge"


class StatusBanner(QFrame):
  """Colored status row with dot, title, and optional hint."""

  def __init__(self, parent: QWidget | None = None) -> None:
    super().__init__(parent)
    self.setObjectName("StatusBanner")
    self.setProperty("statusKind", "neutral")

    row = QHBoxLayout(self)
    row.setContentsMargins(14, 12, 14, 12)
    row.setSpacing(10)

    self._dot = QLabel()
    self._dot.setObjectName("StatusDot")

    text_col = QVBoxLayout()
    text_col.setSpacing(2)
    self._text = QLabel()
    self._text.setObjectName("StatusText")
    self._text.setWordWrap(True)
    self._hint = QLabel()
    self._hint.setObjectName("StatusHint")
    self._hint.setWordWrap(True)
    self._hint.hide()
    text_col.addWidget(self._text)
    text_col.addWidget(self._hint)

    row.addWidget(self._dot, 0, Qt.AlignmentFlag.AlignTop)
    row.addLayout(text_col, 1)

  def set_status(self, text: str, *, kind: str = "neutral", hint: str | None = None) -> None:
    self._text.setText(text)
    self.setProperty("statusKind", kind)
    if hint:
      self._hint.setText(hint)
      self._hint.show()
    else:
      self._hint.hide()
    self.style().unpolish(self)
    self.style().polish(self)


class SecretField(QWidget):
  """Password input with show/hide toggle."""

  def __init__(self, placeholder: str = "", parent: QWidget | None = None) -> None:
    super().__init__(parent)
    layout = QHBoxLayout(self)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)

    self._input = QLineEdit()
    self._input.setEchoMode(QLineEdit.EchoMode.Password)
    self._input.setPlaceholderText(placeholder)

    self._toggle = QPushButton("Show")
    self._toggle.setObjectName("RevealButton")
    self._toggle.setCheckable(True)
    self._toggle.toggled.connect(self._on_toggle)

    layout.addWidget(self._input, 1)
    layout.addWidget(self._toggle)

  def _on_toggle(self, visible: bool) -> None:
    self._input.setEchoMode(
      QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password
    )
    self._toggle.setText("Hide" if visible else "Show")

  def line_edit(self) -> QLineEdit:
    return self._input

  def text(self) -> str:
    return self._input.text()

  def setText(self, value: str) -> None:  # noqa: N802 — Qt naming
    self._input.setText(value)

  def clear(self) -> None:
    self._input.clear()

  def set_placeholder(self, text: str) -> None:
    self._input.setPlaceholderText(text)


class WebBridgeInstallCard(QFrame):
  """Prompt to install Kimi WebBridge when extension is not connected."""

  install_clicked = Signal()

  def __init__(self, parent: QWidget | None = None) -> None:
    super().__init__(parent)
    self.setObjectName("WebBridgeCard")
    layout = QVBoxLayout(self)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(8)

    title = QLabel("Install Kimi WebBridge")
    title.setObjectName("WebBridgeTitle")
    body = QLabel(
      "Download the desktop helper and Chrome extension, then log into LinkedIn in Chrome."
    )
    body.setWordWrap(True)
    body.setObjectName("StatusHint")

    install_btn = QPushButton("Get Kimi WebBridge")
    install_btn.setObjectName("PrimaryButton")
    install_btn.clicked.connect(self._open_install)

    layout.addWidget(title)
    layout.addWidget(body)
    layout.addWidget(install_btn, 0, Qt.AlignmentFlag.AlignLeft)

  def _open_install(self) -> None:
    QDesktopServices.openUrl(WEBBRIDGE_INSTALL_URL)
    self.install_clicked.emit()


class LabeledField(QWidget):
  """Label + input + optional hint row."""

  def __init__(
    self,
    label: str,
    widget: QWidget,
    *,
    hint: str | None = None,
    badge: QLabel | None = None,
    parent: QWidget | None = None,
  ) -> None:
    super().__init__(parent)
    layout = QVBoxLayout(self)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    label_row = QHBoxLayout()
    label_row.setSpacing(8)
    title = QLabel(label)
    title.setObjectName("FieldLabel")
    label_row.addWidget(title)
    if badge is not None:
      label_row.addWidget(badge)
    label_row.addStretch(1)
    layout.addLayout(label_row)
    layout.addWidget(widget)
    if hint:
      hint_label = QLabel(hint)
      hint_label.setObjectName("FieldHint")
      hint_label.setWordWrap(True)
      layout.addWidget(hint_label)


class ConnectionSummaryCard(QFrame):
  """Read-only home view — shows configured / not configured, never secrets."""

  def __init__(self, parent: QWidget | None = None) -> None:
    super().__init__(parent)
    self.setObjectName("Card")
    layout = QVBoxLayout(self)
    layout.setContentsMargins(14, 14, 14, 14)
    layout.setSpacing(8)

    heading = QLabel("Connection")
    heading.setObjectName("FieldLabel")
    layout.addWidget(heading)

    self._pairing_row = QLabel()
    self._pairing_row.setObjectName("SetupStep")
    self._api_row = QLabel()
    self._api_row.setObjectName("SetupStep")
    layout.addWidget(self._pairing_row)
    layout.addWidget(self._api_row)

  def update_from_config(self, cfg: dict[str, str]) -> None:
    has_token = bool(cfg.get("worker_token", "").strip())
    has_key = bool(cfg.get("dashscope_api_key", "").strip())
    self._pairing_row.setText(
      "Pairing code · Configured" if has_token else "Pairing code · Not set"
    )
    self._api_row.setText(
      "API key · Configured" if has_key else "API key · Not set"
    )
