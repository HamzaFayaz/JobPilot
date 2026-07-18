"""Tests for LinkedIn post listing rewrite helpers."""

from backend.app.models.browser import RawJobListing
from backend.app.services.listing_rewrite import (
    format_apply_header,
    rewrite_listings,
)


def test_format_apply_header_email():
    text = format_apply_header(
        apply_method="email",
        apply_value="hr-pk@aiengeers.pk",
        apply_note="Send resume with subject Proposal Engineer.",
    )
    assert "Apply via email: hr-pk@aiengeers.pk" in text
    assert "How to apply" in text


def test_format_apply_header_linkedin_dm():
    text = format_apply_header(
        apply_method="linkedin_dm",
        apply_value="Hifsa Naeem",
        apply_note="",
    )
    assert "DM on LinkedIn" in text
    assert "Hifsa Naeem" in text


def test_format_apply_header_none():
    text = format_apply_header(apply_method="none", apply_value="", apply_note="")
    assert "No apply info" in text


def test_rewrite_listings_skips_without_api_key(monkeypatch):
    from backend.app.services import listing_rewrite as mod

    monkeypatch.setattr(mod.settings, "dashscope_api_key", "")
    raw = RawJobListing(
        title="Hifsa Naeem Verified Profile 2nd",
        company="Hifsa Naeem Verified Profile 2nd",
        url="linkedin-post://abc",
        descriptionText="Messy post about Senior AI Engineer. DM me.",
        sourcePlatform="linkedin",
    )
    out = rewrite_listings([raw])
    assert out[0].title == raw.title
    assert out[0].description_text == raw.description_text


def test_rewrite_listings_applies_mock_response(monkeypatch):
    from backend.app.services import listing_rewrite as mod

    class _Msg:
        content = """{
          "listings": [{
            "index": 0,
            "title": "Senior AI Engineer (Part-Time)",
            "company": "CoPilot Innovations",
            "description": "Looking for a hands-on Senior AI Engineer. GenAI, RAG, Python.",
            "apply_method": "linkedin_dm",
            "apply_value": "Hifsa Naeem",
            "apply_note": "Send resume via LinkedIn DM."
          }]
        }"""

    class _Choice:
        message = _Msg()

    class _Resp:
        choices = [_Choice()]

    class _Completions:
        def create(self, **kwargs):
            return _Resp()

    class _Chat:
        completions = _Completions()

    class _Client:
        chat = _Chat()

    monkeypatch.setattr(mod.settings, "dashscope_api_key", "test-key")
    monkeypatch.setattr(mod, "_client", lambda: _Client())

    raw = RawJobListing(
        title="Hifsa Naeem Verified Profile 2nd",
        company="Hifsa Naeem Verified Profile 2nd",
        url="linkedin-post://abc",
        descriptionText="Hifsa Naeem Verified Profile 2nd #Hiring Senior AI Engineer 55 reactions",
        sourcePlatform="linkedin",
    )
    out = rewrite_listings([raw])
    assert out[0].title == "Senior AI Engineer (Part-Time)"
    assert out[0].company == "CoPilot Innovations"
    assert "How to apply" in out[0].description_text
    assert "Hifsa Naeem" in out[0].description_text
    assert "GenAI, RAG, Python" in out[0].description_text
    assert "55 reactions" not in out[0].description_text
