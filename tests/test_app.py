"""Run the Streamlit entry point with isolated test sessions."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

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
