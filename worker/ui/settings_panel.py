"""Settings tab — view mode with Edit, or form mode for changes."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from worker.local_config import DEFAULT_API_BASE, env_path, normalize_api_base
from worker.ui.widgets import LabeledField, SecretField


def _plain_line_edit(placeholder: str = "") -> QLineEdit:
    field = QLineEdit()
    field.setPlaceholderText(placeholder)
    field.setMinimumHeight(40)
    field.setMaximumHeight(40)
    return field


class SettingsPanel(QWidget):
    saved = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._disk_api_base = DEFAULT_API_BASE
        self._disk_token = ""
        self._editing = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 12)
        layout.setSpacing(10)

        self._intro = QLabel()
        self._intro.setObjectName("FieldHint")
        self._intro.setWordWrap(True)
        layout.addWidget(self._intro)

        self._stack = QStackedWidget()
        self._summary_page = self._build_summary_page()
        self._form_page = self._build_form_page()
        self._stack.addWidget(self._summary_page)
        self._stack.addWidget(self._form_page)
        layout.addWidget(self._stack, 1)

        self._path_hint = QLabel()
        self._path_hint.setObjectName("FieldHint")
        self._path_hint.setWordWrap(True)
        layout.addWidget(self._path_hint)

    def _build_summary_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(8)

        heading = QLabel("Saved connection")
        heading.setObjectName("FieldLabel")
        card_layout.addWidget(heading)

        self._summary_api_base = QLabel()
        self._summary_api_base.setObjectName("SetupStep")
        self._summary_api_base.setWordWrap(True)
        self._summary_pairing = QLabel()
        self._summary_pairing.setObjectName("SetupStep")
        self._summary_agent = QLabel()
        self._summary_agent.setObjectName("SetupStep")
        card_layout.addWidget(self._summary_api_base)
        card_layout.addWidget(self._summary_pairing)
        card_layout.addWidget(self._summary_agent)

        layout.addWidget(card)

        self._edit_button = QPushButton("Edit settings")
        self._edit_button.setObjectName("SecondaryButton")
        self._edit_button.clicked.connect(self._enter_edit_mode)
        layout.addWidget(self._edit_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addStretch(1)
        return page

    def _build_form_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(12)

        self._api_base_field = _plain_line_edit("http://localhost:8000")
        card_layout.addWidget(
            LabeledField(
                "JobPilot API URL",
                self._api_base_field,
                hint="Local needs a port (http://localhost:8000). Cloud usually has no port.",
            )
        )

        self._token_field = SecretField("Paste pairing code from JobPilot Settings")
        card_layout.addWidget(
            LabeledField(
                "Pairing code",
                self._token_field,
                hint="From JobPilot → Settings → Search Helper. Model API key stays on the server.",
            )
        )

        layout.addWidget(card)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        self._save_button = QPushButton("Save settings")
        self._save_button.setObjectName("PrimaryButton")
        self._save_button.clicked.connect(self.saved.emit)

        self._cancel_button = QPushButton("Cancel")
        self._cancel_button.setObjectName("SecondaryButton")
        self._cancel_button.clicked.connect(self._cancel_edit)

        buttons.addWidget(self._save_button)
        buttons.addWidget(self._cancel_button)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        layout.addStretch(1)
        return page

    def is_editing(self) -> bool:
        return self._editing or not self._is_configured()

    def _is_configured(self) -> bool:
        return bool(self._disk_token and self._disk_api_base)

    def _enter_edit_mode(self) -> None:
        self._editing = True
        self._prepare_form_fields()
        self._stack.setCurrentWidget(self._form_page)
        self._intro.setText(
            "Edit API URL and pairing code. Leave pairing code blank to keep the saved value."
        )

    def _cancel_edit(self) -> None:
        self._editing = False
        if self._is_configured():
            self._show_summary()
        else:
            self._prepare_form_fields()

    def _prepare_form_fields(self) -> None:
        self._api_base_field.setText(self._disk_api_base or DEFAULT_API_BASE)
        self._token_field.clear()
        self._token_field.set_placeholder(
            "Leave blank to keep current pairing code"
            if self._disk_token
            else "Paste pairing code from JobPilot Settings"
        )

    def _show_summary(self) -> None:
        self._summary_api_base.setText(f"API URL · {self._disk_api_base or 'Not set'}")
        self._summary_pairing.setText(
            "Pairing code · Configured" if self._disk_token else "Pairing code · Not set"
        )
        self._summary_agent.setText("Search agent · Cloud (server model key)")
        self._stack.setCurrentWidget(self._summary_page)
        self._intro.setText("Connection saved on this PC. Click Edit settings to change it.")

    def load_from_disk(self, cfg: dict[str, str]) -> None:
        self._disk_api_base = (
            normalize_api_base(cfg.get("jobpilot_api_base", "") or DEFAULT_API_BASE)
            or DEFAULT_API_BASE
        )
        self._disk_token = cfg.get("worker_token", "")
        self._path_hint.setText(f"Saved to: {env_path()}")

        self._editing = False
        if self._is_configured():
            self._show_summary()
        else:
            self._editing = True
            self._prepare_form_fields()
            self._stack.setCurrentWidget(self._form_page)
            self._intro.setText(
                "Add API URL and pairing code from JobPilot Settings, then Save."
            )

    def collect(self) -> dict[str, str]:
        api_base = (
            normalize_api_base(self._api_base_field.text())
            or self._disk_api_base
            or DEFAULT_API_BASE
        )
        token = self._token_field.text().strip() or self._disk_token
        return {
            "jobpilot_api_base": api_base,
            "worker_token": token,
        }
