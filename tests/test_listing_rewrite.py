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


def test_format_apply_header_none_falls_back_to_search_poster():
    text = format_apply_header(apply_method="none", apply_value="", apply_note="")
    assert "search" in text.lower()
    assert "LinkedIn" in text


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
    assert out[0].display_description_text == ""


def test_rewrite_keeps_raw_description_for_analysis(monkeypatch):
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

    raw_body = "Hifsa Naeem Verified Profile 2nd #Hiring Senior AI Engineer 55 reactions"
    raw = RawJobListing(
        title="Hifsa Naeem Verified Profile 2nd",
        company="Hifsa Naeem Verified Profile 2nd",
        url="linkedin-post://abc",
        descriptionText=raw_body,
        sourcePlatform="linkedin",
    )
    out = rewrite_listings([raw])
    assert out[0].title == "Senior AI Engineer (Part-Time)"
    assert out[0].company == "CoPilot Innovations"
    # Analysis path keeps the original scrape.
    assert out[0].description_text == raw_body
    # UI path gets formatting + apply header.
    assert "How to apply" in out[0].display_description_text
    assert "Hifsa Naeem" in out[0].display_description_text
    assert "GenAI, RAG, Python" in out[0].display_description_text
    assert "55 reactions" not in out[0].display_description_text


def test_rewrite_none_apply_becomes_linkedin_dm(monkeypatch):
    from backend.app.services import listing_rewrite as mod

    class _Msg:
        content = """{
          "listings": [{
            "index": 0,
            "title": "Backend Engineer",
            "company": "Acme",
            "description": "Need a backend engineer. Python, FastAPI.",
            "apply_method": "none",
            "apply_value": "",
            "apply_note": ""
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
        title="Poster Name",
        company="Poster Name",
        url="linkedin-post://xyz",
        descriptionText="Hiring backend engineer",
        sourcePlatform="linkedin",
    )
    out = rewrite_listings([raw])
    assert out[0].description_text == "Hiring backend engineer"
    assert "DM on LinkedIn" in out[0].display_description_text
    assert "Acme" in out[0].display_description_text
