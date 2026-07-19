"""Suggested-CV LLM: generate, validate, field-lock merge, repair, word-trim."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from openai import OpenAI

from backend.app.config import settings
from backend.app.observability import span
from backend.app.services.tailor_cv_prompt import TAILOR_CV_SYSTEM_PROMPT
from backend.app.services.word_trim import word_trim_to_max

logger = logging.getLogger(__name__)

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


class TailorCvError(Exception):
    def __init__(self, code: str, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable

    def safe_dict(self) -> dict[str, Any]:
        return {
            "stage": "tailor_cv",
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }


def _parse_slots_payload(raw: str | None) -> dict[str, Any]:
    if not raw or not str(raw).strip():
        raise TailorCvError("empty_model_output", "Suggested CV model returned empty output.")
    text = str(raw).strip()
    text = _JSON_FENCE_RE.sub("", text).strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TailorCvError(
            "invalid_json",
            "Suggested CV model returned invalid JSON.",
            retryable=True,
        ) from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("slots"), list):
        raise TailorCvError(
            "invalid_shape",
            "Suggested CV model output must include a slots array.",
            retryable=True,
        )
    return payload


def validate_generated_slots(
    payload: dict[str, Any],
    layout_slots: list[dict[str, Any]],
    approved_slot_indexes: list[int],
) -> list[str]:
    """Return validation error strings; empty means pass."""
    errors: list[str] = []
    slots = payload.get("slots") or []
    by_index: dict[int, dict[str, Any]] = {}
    for item in slots:
        if not isinstance(item, dict):
            errors.append("slots entries must be objects")
            continue
        try:
            slot_index = int(item.get("slot_index"))
        except (TypeError, ValueError):
            errors.append("slot_index must be an integer")
            continue
        by_index[slot_index] = item

    expected = [int(i) for i in approved_slot_indexes]
    if sorted(by_index.keys()) != sorted(expected):
        errors.append(
            f"slots indexes {sorted(by_index.keys())} != approved {sorted(expected)}"
        )

    layout_by_index = {int(slot["slot_index"]): slot for slot in layout_slots}
    for slot_index in expected:
        layout = layout_by_index.get(slot_index)
        generated = by_index.get(slot_index)
        if layout is None or generated is None:
            continue
        title = str(generated.get("title") or "")
        max_title = int((layout.get("title") or {}).get("max_characters") or 0)
        if len(title) > max_title:
            errors.append(
                f"slot {slot_index} title: length {len(title)} > max {max_title}"
            )
        items = generated.get("items")
        desc = layout.get("description_items") or []
        if not isinstance(items, list):
            errors.append(f"slot {slot_index} items must be an array")
            continue
        if len(items) != len(desc):
            errors.append(
                f"slot {slot_index}: expected {len(desc)} items, got {len(items)}"
            )
            continue
        for item_index, (value, spec) in enumerate(zip(items, desc)):
            text = str(value or "")
            max_chars = int(spec.get("max_characters") or 0)
            if len(text) > max_chars:
                errors.append(
                    f"slot {slot_index} items[{item_index}]: "
                    f"length {len(text)} > max {max_chars}"
                )
    return errors


def _field_key(slot_index: int, field: str) -> str:
    return f"{slot_index}:{field}"


def lock_passing_fields(
    payload: dict[str, Any],
    layout_slots: list[dict[str, Any]],
) -> dict[str, str]:
    """Return map of field keys that already pass budgets."""
    locked: dict[str, str] = {}
    layout_by_index = {int(slot["slot_index"]): slot for slot in layout_slots}
    for item in payload.get("slots") or []:
        if not isinstance(item, dict):
            continue
        slot_index = int(item["slot_index"])
        layout = layout_by_index.get(slot_index)
        if layout is None:
            continue
        title = str(item.get("title") or "")
        max_title = int((layout.get("title") or {}).get("max_characters") or 0)
        if len(title) <= max_title:
            locked[_field_key(slot_index, "title")] = title
        items = item.get("items")
        desc = layout.get("description_items") or []
        if not isinstance(items, list) or len(items) != len(desc):
            continue
        for item_index, (value, spec) in enumerate(zip(items, desc)):
            text = str(value or "")
            max_chars = int(spec.get("max_characters") or 0)
            if len(text) <= max_chars:
                locked[_field_key(slot_index, f"items[{item_index}]")] = text
    return locked


def merge_with_locked(
    call2_payload: dict[str, Any],
    locked: dict[str, str],
    layout_slots: list[dict[str, Any]],
    approved_slot_indexes: list[int],
) -> dict[str, Any]:
    """Keep call-1 locked fields; take call-2 only for unlocked fields."""
    layout_by_index = {int(slot["slot_index"]): slot for slot in layout_slots}
    call2_by_index = {
        int(item["slot_index"]): item
        for item in (call2_payload.get("slots") or [])
        if isinstance(item, dict) and "slot_index" in item
    }
    merged_slots: list[dict[str, Any]] = []
    for slot_index in approved_slot_indexes:
        layout = layout_by_index[int(slot_index)]
        call2 = call2_by_index.get(int(slot_index), {})
        desc = layout.get("description_items") or []
        title_key = _field_key(slot_index, "title")
        if title_key in locked:
            title = locked[title_key]
        else:
            title = str(call2.get("title") or "")
        items: list[str] = []
        call2_items = call2.get("items") if isinstance(call2.get("items"), list) else []
        for item_index, _spec in enumerate(desc):
            key = _field_key(slot_index, f"items[{item_index}]")
            if key in locked:
                items.append(locked[key])
            elif item_index < len(call2_items):
                items.append(str(call2_items[item_index] or ""))
            else:
                items.append("")
        merged_slots.append(
            {"slot_index": int(slot_index), "title": title, "items": items}
        )
    return {"slots": merged_slots}


def apply_word_trim_fallback(
    payload: dict[str, Any],
    layout_slots: list[dict[str, Any]],
) -> tuple[dict[str, Any], bool, list[dict[str, Any]]]:
    """Trim any still-over fields by whole words.

    Returns (payload, auto_shortened, capped_fields).
    """
    layout_by_index = {int(slot["slot_index"]): slot for slot in layout_slots}
    shortened = False
    capped: list[dict[str, Any]] = []
    out_slots: list[dict[str, Any]] = []
    for item in payload.get("slots") or []:
        slot_index = int(item["slot_index"])
        layout = layout_by_index[slot_index]
        max_title = int((layout.get("title") or {}).get("max_characters") or 0)
        title = str(item.get("title") or "")
        if len(title) > max_title:
            trimmed_title = word_trim_to_max(title, max_title)
            capped.append(
                {
                    "slot_index": slot_index,
                    "field": "title",
                    "max_characters": max_title,
                    "before": title,
                    "after": trimmed_title,
                    "before_len": len(title),
                    "after_len": len(trimmed_title),
                }
            )
            title = trimmed_title
            shortened = True
        desc = layout.get("description_items") or []
        raw_items = item.get("items") if isinstance(item.get("items"), list) else []
        items: list[str] = []
        for item_index, spec in enumerate(desc):
            max_chars = int(spec.get("max_characters") or 0)
            text = str(raw_items[item_index] if item_index < len(raw_items) else "")
            if len(text) > max_chars:
                trimmed_text = word_trim_to_max(text, max_chars)
                capped.append(
                    {
                        "slot_index": slot_index,
                        "field": f"items[{item_index}]",
                        "max_characters": max_chars,
                        "before": text,
                        "after": trimmed_text,
                        "before_len": len(text),
                        "after_len": len(trimmed_text),
                    }
                )
                text = trimmed_text
                shortened = True
            items.append(text)
        out_slots.append({"slot_index": slot_index, "title": title, "items": items})
    return {"slots": out_slots}, shortened, capped


def build_user_bundle(
    *,
    job: dict[str, Any],
    approved_swaps: list[dict[str, Any]],
    layout_slots: list[dict[str, Any]],
    projects: list[dict[str, Any]],
) -> dict[str, Any]:
    from backend.app.services.cv_layout_contract import layout_for_llm

    return {
        "job": job,
        "approved_swaps": approved_swaps,
        "layout_slots": layout_for_llm(layout_slots),
        "projects": projects,
    }


def generate_suggested_slot_text(
    *,
    user_id: int,
    job: dict[str, Any],
    approved_swaps: list[dict[str, Any]],
    layout_slots: list[dict[str, Any]],
    projects: list[dict[str, Any]],
    client: OpenAI | None = None,
) -> tuple[dict[str, Any], bool, dict[str, Any]]:
    """Run call1 (+ optional call2) then word-trim.

    Returns (slots_payload, auto_shortened, debug).
    """
    approved_indexes = [int(item["slot_index"]) for item in approved_swaps]
    user_bundle = build_user_bundle(
        job=job,
        approved_swaps=approved_swaps,
        layout_slots=layout_slots,
        projects=projects,
    )
    messages = [
        {"role": "system", "content": TAILOR_CV_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": json.dumps(
                user_bundle, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ),
        },
    ]
    llm = client or OpenAI(
        api_key=settings.dashscope_api_key,
        base_url=settings.qwen_base_url,
        timeout=120.0,
    )
    debug: dict[str, Any] = {
        "model": settings.tailor_cv_model,
        "prompt_version": settings.tailor_cv_prompt_version,
        "llm_input": {
            "system": TAILOR_CV_SYSTEM_PROMPT,
            "user_bundle": user_bundle,
        },
        "layout_budgets": [
            {
                "slot_index": slot["slot_index"],
                "title_max": (slot.get("title") or {}).get("max_characters"),
                "items_max": [
                    item.get("max_characters")
                    for item in (slot.get("description_items") or [])
                ],
            }
            for slot in layout_slots
        ],
        "attempts": [],
        "capping": None,
    }

    def _log_attempt(
        attempt: int,
        *,
        raw: str | None,
        errors: list[str] | None = None,
        payload: dict[str, Any] | None = None,
        note: str = "",
    ) -> None:
        entry = {
            "attempt": attempt,
            "note": note,
            "raw_response": raw,
            "validation_errors": errors or [],
            "parsed_slots": (payload or {}).get("slots") if payload else None,
        }
        debug["attempts"].append(entry)
        logger.info(
            "tailor_cv user_id=%s attempt=%s note=%s errors=%s raw=%s",
            user_id,
            attempt,
            note or "-",
            errors or [],
            (raw or "")[:4000],
        )

    with span(
        "tailor_cv_model",
        user_id=user_id,
        model=settings.tailor_cv_model,
        prompt_version=settings.tailor_cv_prompt_version,
        attempt=1,
    ):
        try:
            response = llm.chat.completions.create(
                model=settings.tailor_cv_model,
                messages=messages,
                temperature=settings.tailor_cv_temperature,
                response_format={"type": "json_object"},
                extra_body={"enable_thinking": settings.tailor_cv_enable_thinking},
            )
        except Exception as exc:
            logger.exception("tailor_cv call 1 failed user_id=%s", user_id)
            raise TailorCvError(
                "model_unavailable",
                "Suggested CV model is unavailable.",
                retryable=True,
            ) from exc
        raw_call1 = response.choices[0].message.content if response.choices else None

    payload1 = _parse_slots_payload(raw_call1)
    errors1 = validate_generated_slots(payload1, layout_slots, approved_indexes)
    _log_attempt(
        1,
        raw=raw_call1,
        errors=errors1,
        payload=payload1,
        note="initial generate",
    )
    if not errors1:
        debug["outcome"] = "call1_pass"
        logger.info("tailor_cv user_id=%s outcome=call1_pass", user_id)
        return payload1, False, debug

    locked = lock_passing_fields(payload1, layout_slots)
    debug["locked_fields_after_call1"] = sorted(locked.keys())
    logger.info(
        "tailor_cv user_id=%s locked_fields=%s",
        user_id,
        sorted(locked.keys()),
    )
    repair_user = {
        "instruction": (
            "Return the complete corrected JSON object only. "
            "Keep every field that already passed unchanged. "
            "Fix only the fields listed in validation_errors."
        ),
        "validation_errors": errors1,
    }
    debug["call2_repair_input"] = repair_user
    request_messages = list(messages)
    request_messages.append({"role": "assistant", "content": raw_call1 or ""})
    request_messages.append(
        {
            "role": "user",
            "content": json.dumps(
                repair_user, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ),
        }
    )

    with span(
        "tailor_cv_model",
        user_id=user_id,
        model=settings.tailor_cv_model,
        prompt_version=settings.tailor_cv_prompt_version,
        attempt=2,
    ):
        try:
            response2 = llm.chat.completions.create(
                model=settings.tailor_cv_model,
                messages=request_messages,
                temperature=settings.tailor_cv_temperature,
                response_format={"type": "json_object"},
                extra_body={"enable_thinking": settings.tailor_cv_enable_thinking},
            )
        except Exception as exc:
            logger.exception("tailor_cv call 2 failed user_id=%s", user_id)
            raise TailorCvError(
                "model_unavailable",
                "Suggested CV model is unavailable on repair.",
                retryable=True,
            ) from exc
        raw_call2 = response2.choices[0].message.content if response2.choices else None

    parse_error: str | None = None
    try:
        payload2 = _parse_slots_payload(raw_call2)
    except TailorCvError as exc:
        payload2 = {"slots": []}
        parse_error = exc.message

    _log_attempt(
        2,
        raw=raw_call2,
        errors=[parse_error] if parse_error else None,
        payload=payload2,
        note="repair generate",
    )

    merged = merge_with_locked(payload2, locked, layout_slots, approved_indexes)
    errors2 = validate_generated_slots(merged, layout_slots, approved_indexes)
    debug["merged_after_call2"] = merged
    debug["merged_validation_errors"] = errors2
    logger.info(
        "tailor_cv user_id=%s merge_errors=%s merged=%s",
        user_id,
        errors2,
        json.dumps(merged, ensure_ascii=False)[:4000],
    )
    if not errors2:
        debug["outcome"] = "call2_pass_after_merge"
        logger.info("tailor_cv user_id=%s outcome=call2_pass_after_merge", user_id)
        return merged, False, debug

    trimmed, auto_shortened, capped_fields = apply_word_trim_fallback(
        merged, layout_slots
    )
    debug["after_word_trim"] = trimmed
    debug["auto_shortened"] = auto_shortened
    debug["capping"] = {
        "applied": auto_shortened,
        "fields": capped_fields,
    }
    debug["outcome"] = "word_trim_fallback"
    logger.info(
        "tailor_cv user_id=%s outcome=word_trim_fallback auto_shortened=%s capped=%s",
        user_id,
        auto_shortened,
        len(capped_fields),
    )
    return trimmed, auto_shortened, debug
