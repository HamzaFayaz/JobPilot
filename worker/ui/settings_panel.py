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

from worker.local_config import DEFAULT_MODEL, env_path
from worker.ui.widgets import LabeledField, SecretField


class SettingsPanel(QWidget):
    saved = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._disk_token = ""
        self._disk_api_key = ""
        self._disk_model = DEFAULT_MODEL
        self._editing = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 20)
        layout.setSpacing(14)

        self._intro = QLabel()
        self._intro.setObjectName("FieldHint")
        self._intro.setWordWrap(True)
        layout.addWidget(self._intro)

        self._stack = QStackedWidget()

        self._summary_page = self._build_summary_page()
        self._form_page = self._build_form_page()
        self._stack.addWidget(self._summary_page)
        self._stack.addWidget(self._form_page)
        layout.addWidget(self._stack)

        self._path_hint = QLabel()
        self._path_hint.setObjectName("FieldHint")
        self._path_hint.setWordWrap(True)
        layout.addWidget(self._path_hint)

        layout.addStretch(1)

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

        self._summary_pairing = QLabel()
        self._summary_pairing.setObjectName("SetupStep")
        self._summary_api = QLabel()
        self._summary_api.setObjectName("SetupStep")
        self._summary_model = QLabel()
        self._summary_model.setObjectName("SetupStep")
        card_layout.addWidget(self._summary_pairing)
        card_layout.addWidget(self._summary_api)
        card_layout.addWidget(self._summary_model)

        layout.addWidget(card)

        self._edit_button = QPushButton("Edit settings")
        self._edit_button.setObjectName("SecondaryButton")
        self._edit_button.clicked.connect(self._enter_edit_mode)
        layout.addWidget(self._edit_button, 0, Qt.AlignmentFlag.AlignLeft)
        return page

    def _build_form_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(12)

        self._token_field = SecretField("From JobPilot → Settings → Connect this computer")
        card_layout.addWidget(
            LabeledField(
                "Pairing code",
                self._token_field,
                hint="Generate this code on the JobPilot website.",
            )
        )

        self._api_key_field = SecretField("Enter your Dashscope API key")
        card_layout.addWidget(LabeledField("Dashscope API key", self._api_key_field))

        self._model_field = QLineEdit()
        self._model_field.setPlaceholderText(DEFAULT_MODEL)
        card_layout.addWidget(
            LabeledField(
                "Qwen model",
                self._model_field,
                hint=f"Default: {DEFAULT_MODEL}",
            )
        )

        layout.addWidget(card)

        buttons = QHBoxLayout()
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
        return page

    def is_editing(self) -> bool:
        return self._editing or not self._is_configured()

    def _is_configured(self) -> bool:
        return bool(self._disk_token and self._disk_api_key)

    def _enter_edit_mode(self) -> None:
        self._editing = True
        self._prepare_form_fields()
        self._stack.setCurrentWidget(self._form_page)
        self._intro.setText(
            "Update your connection details below. Leave pairing code and API key blank "
            "to keep the values already saved on this PC."
        )

    def _cancel_edit(self) -> None:
        self._editing = False
        if self._is_configured():
            self._show_summary()
        else:
            self._prepare_form_fields()

    def _prepare_form_fields(self) -> None:
        self._token_field.clear()
        self._token_field.set_placeholder(
            "Leave blank to keep current pairing code"
            if self._disk_token
            else "From JobPilot → Settings → Connect this computer"
        )
        self._api_key_field.clear()
        self._api_key_field.set_placeholder(
            "Leave blank to keep current API key"
            if self._disk_api_key
            else "Enter your Dashscope API key"
        )
        self._model_field.setText(self._disk_model)

    def _show_summary(self) -> None:
        self._summary_pairing.setText(
            "Pairing code · Configured" if self._disk_token else "Pairing code · Not set"
        )
        self._summary_api.setText(
            "API key · Configured" if self._disk_api_key else "API key · Not set"
        )
        self._summary_model.setText(f"Qwen model · {self._disk_model}")
        self._stack.setCurrentWidget(self._summary_page)
        self._intro.setText("Your connection is saved on this PC. Click Edit to change it.")

    def load_from_disk(self, cfg: dict[str, str]) -> None:
        self._disk_token = cfg.get("worker_token", "")
        self._disk_api_key = cfg.get("dashscope_api_key", "")
        self._disk_model = cfg.get("qwen_model", "") or DEFAULT_MODEL
        self._path_hint.setText(f"Saved to: {env_path()}")

        self._editing = False
        if self._is_configured():
            self._show_summary()
        else:
            self._editing = True
            self._prepare_form_fields()
            self._stack.setCurrentWidget(self._form_page)
            self._intro.setText(
                "Add your pairing code and API key to connect this computer to JobPilot."
            )

    def collect(self) -> dict[str, str]:
        token = self._token_field.text().strip() or self._disk_token
        api_key = self._api_key_field.text().strip() or self._disk_api_key
        model = self._model_field.text().strip() or self._disk_model or DEFAULT_MODEL
        return {
            "worker_token": token,
            "dashscope_api_key": api_key,
            "qwen_model": model,
        }
