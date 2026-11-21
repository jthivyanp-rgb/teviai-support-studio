"""Run the Streamlit entry point with isolated test sessions."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src import ai_provider
from src.data_models import Status

PAGES = ["Dashboard", "Customer Enquiries", "Draft Studio", "Approval Centre", "Activity Log", "Settings", "Safety Lab"]


@pytest.fixture(autouse=True)
def no_gemini_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


def start():
    at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=20).run()
    assert not at.exception
    return at


def page(at, label):
    return at.radio(key="page").set_value(label).run()


def test_every_page_loads():
    at = start()
    for label in PAGES:
        page(at, label)
        assert not at.exception, label


def test_full_workflow_rule_based_draft_then_approval():
    at = start()
    at.button(key="load_samples").click().run()
    assert len(at.session_state["enquiries"]) == 10
    assert len(at.session_state["log"]) == 20
    assert at.button(key="load_samples").disabled

    identifier = at.session_state["enquiries"][0]["id"]
    page(at, "Draft Studio")
    at.button(key=f"rule_{identifier}").click().run()
    assert at.session_state["enquiries"][0]["status"] == Status.DRAFT_READY
    at.button(key=f"submit_{identifier}").click().run()
    assert at.session_state["enquiries"][0]["status"] == Status.PENDING_REVIEW

    page(at, "Approval Centre")
    at.button(key=f"approved_{identifier}").click().run()
    assert at.session_state["enquiries"][0]["status"] == Status.PENDING_REVIEW
    assert not at.button(key=f"rejected_{identifier}").disabled
    assert not at.button(key=f"escalated_{identifier}").disabled
    at.selectbox(key=f"reviewer_{identifier}").set_value("Demo Owner").run()
    at.checkbox[0].check().run()
    at.button(key=f"approved_{identifier}").click().run()
    assert not at.exception
    assert at.session_state["enquiries"][0]["status"] == Status.APPROVED
    assert at.session_state["log"][-1]["action"] == "Approved"
    assert at.session_state["log"][-1]["status"] == "Approved — Not Sent"


def test_activity_log_offers_download_and_filters():
    at = start()
    at.button(key="load_samples").click().run()
    page(at, "Activity Log")
    assert not at.exception
    assert len(at.get("download_button")) == 1
    at.selectbox[0].set_value("Classified").run()
    assert len(at.dataframe[0].value) == 10


def test_safety_lab_runs_all_scenarios():
    at = page(start(), "Safety Lab")
    at.button[0].click().run()
    assert not at.exception
    assert len(at.dataframe[0].value) == 18
    assert set(at.dataframe[0].value["Result"]) == {"Pass"}


def test_reset_requires_confirmation_and_other_sessions_are_isolated():
    one = start()
    one.button(key="load_samples").click().run()
    two = start()
    assert two.session_state["enquiries"] == []
    page(one, "Settings")
    assert one.button[-1].disabled
    one.checkbox(key="reset_confirm").check().run()
    one.button[-1].click().run()
    assert not one.exception
    assert one.session_state["enquiries"] == []
    assert one.session_state["log"] == []


def test_enquiry_form_preserves_other_fields_when_message_is_blank():
    at = page(start(), "Customer Enquiries")
    at.text_input(key="customer_name").input("Fictional Visitor")
    at.selectbox(key="customer_channel").set_value("Website chat")
    at.button[1].click().run()
    assert at.error[0].value == "Enter a customer message."
    assert at.text_input(key="customer_name").value == "Fictional Visitor"
    assert at.selectbox(key="customer_channel").value == "Website chat"
    assert at.session_state["enquiries"] == []

    at.text_area(key="customer_message").input("When do you close?")
    at.button[1].click().run()
    assert len(at.session_state["enquiries"]) == 1
    assert at.session_state["enquiries"][0]["customer_name"] == "Fictional Visitor"
    assert at.text_input(key="customer_name").value == ""


def test_new_enquiry_is_selected_after_submission_with_filters_active():
    at = start()
    at.button(key="load_samples").click().run()
    page(at, "Customer Enquiries")
    previous = at.selectbox(key="detail_pick").value
    at.text_input(key="inbox_query").input("no matching case").run()
    at.selectbox(key="inbox_status").set_value("Approved — Not Sent").run()

    at.text_input(key="customer_name").input("Fictional newcomer")
    at.text_area(key="customer_message").input("Where is my parcel?")
    at.button[1].click().run()
    assert not at.exception
    current = at.session_state["enquiries"][-1]
    assert current["id"] != previous
    assert at.text_input(key="inbox_query").value == ""
    assert at.selectbox(key="inbox_status").value == "All statuses"
    assert at.selectbox(key="detail_pick").value == current["id"]
    assert "Where is my parcel?" in at.code[0].value


@pytest.mark.parametrize("provider_error", [False, True], ids=["model-success", "model-failure"])
def test_ai_studio_labels_success_and_fallback(monkeypatch, provider_error):
    def fake_provider(message, allowed, key, model):
        assert key == "fixture-only"
        if provider_error:
            raise TimeoutError("Test provider unavailable")
        return {"opening": "delay"}

    original_generate = ai_provider.generate_draft
    monkeypatch.setattr(ai_provider, "generate_draft", lambda *args: original_generate(*args, provider=fake_provider))
    monkeypatch.setenv("GEMINI_API_KEY", "fixture-only")
    at = start()
    at.button(key="load_samples").click().run()
    at.session_state["mode"] = "AI-Assisted"
    delivery = at.session_state["enquiries"][1]["id"]
    at.session_state["selected_enquiry"] = delivery
    page(at, "Draft Studio")

    assert at.button(key=f"ai_{delivery}").disabled
    at.checkbox(key=f"consent_{delivery}").check().run()
    at.button(key=f"ai_{delivery}").click().run()
    assert not at.exception
    assert at.session_state["enquiries"][1]["draft_source"] == ("Rule-Based" if provider_error else "AI-Assisted")
    if provider_error:
        assert "Used the rule-based draft." in at.warning[0].value
    else:
        assert "delay you described" in at.text_area(key=f"draft_editor_{delivery}").value
