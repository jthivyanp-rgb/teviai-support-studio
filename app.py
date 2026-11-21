"""TeviAI's session-based Streamlit workspace."""

import hashlib
import os
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from sample_data import SAMPLE_ENQUIRIES
from src.activity_logger import log_to_csv, log_to_dataframe, migrate_event
from src.ai_provider import DEFAULT_MODEL, generate_draft, verified_sample
from src.approval_workflow import (
    DRAFTABLE, EDITABLE, create_enquiry, decide, edit_draft, request_review,
    return_for_revision, review_risks, save_draft,
)
from src.business_config import DEFAULT_BUSINESS_NAME, DEFAULT_POLICIES, POLICY_LABELS
from src.classification import CATEGORIES
from src.data_models import LEGACY_STATUSES, MAX_MESSAGE, MAX_REPLY, REVIEWERS, STATUS_LABELS, Status
from src.response_generator import rule_based_reply
from src.risk_detection import find_personal_data, redact_pii, risk_codes, risk_level
from src.safety_lab import run_scenarios

st.set_page_config(page_title="TeviAI | Support Studio", page_icon=":material/verified_user:", layout="wide")

CHANNELS = ("Email", "Website form", "Website chat", "Instagram DM", "Facebook message", "Phone note")
RULE_MODE = "Rule-Based"
AI_MODE = "AI-Assisted"
REASONS = ("", "Needs factual verification", "Privacy or specialist handling", "Draft wording unsuitable", "Other")


def initialise():
    defaults = {
        "enquiries": [], "log": [], "business_name": DEFAULT_BUSINESS_NAME,
        "policies": dict(DEFAULT_POLICIES), "samples_loaded": False, "mode": RULE_MODE,
        "flash": None, "selected_enquiry": None, "safety_results": [],
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    for enquiry in st.session_state.enquiries:
        legacy_record = enquiry["status"] in LEGACY_STATUSES
        enquiry["status"] = LEGACY_STATUSES.get(enquiry["status"], enquiry["status"])
        enquiry.setdefault("received_at", "")
        enquiry.setdefault("decision_reason", "")
        enquiry.setdefault("sample_id", "")
        enquiry["label"] = CATEGORIES.get(enquiry["category"], enquiry["label"])
        source = enquiry["draft_source"]
        if source and source not in (RULE_MODE, AI_MODE):
            enquiry["draft_source"] = AI_MODE if source.startswith("AI-") else RULE_MODE
        if enquiry["reviewer"] not in REVIEWERS:
            enquiry["reviewer"] = ""
        if legacy_record:
            enquiry.pop("risks_at_decision", None)
            enquiry["risks"] = review_risks(enquiry, st.session_state.policies, enquiry["final_reply"] or None)
    st.session_state.log = [entry if "action" in entry else migrate_event(entry) for entry in st.session_state.log]
    if st.session_state.get("page") in ("Response Drafting", "Human Approval"):
        st.session_state.page = {
            "Response Drafting": "Draft Studio", "Human Approval": "Approval Centre",
        }[st.session_state.page]


def setting(name):
    try:
        return str(st.secrets.get(name, os.getenv(name, ""))).strip()
    except FileNotFoundError:
        return os.getenv(name, "").strip()


def navigate(page, enquiry_id=None):
    st.session_state.page = page
    if enquiry_id:
        st.session_state.selected_enquiry = enquiry_id


def notice(message, level="success"):
    st.session_state.flash = (level, message)
    st.rerun()


def load_samples():
    if not st.session_state.samples_loaded:
        for sample in SAMPLE_ENQUIRIES:
            add_enquiry(sample["customer_name"], sample["channel"], sample["message"], sample["case_id"])
        st.session_state.samples_loaded = True


def add_enquiry(name, channel, message, sample_id=""):
    enquiry = create_enquiry(
        name, channel, message, st.session_state.policies, st.session_state.log, sample_id=sample_id,
    )
    st.session_state.enquiries.append(enquiry)
    return enquiry


def submit_enquiry():
    form = st.session_state
    try:
        enquiry = add_enquiry(form.customer_name, form.customer_channel, form.customer_message)
    except ValueError as exc:
        form.enquiry_form_error = str(exc)
        return
    form.update(customer_name="", customer_channel=CHANNELS[0], customer_message="",
                selected_enquiry=enquiry["id"], detail_pick=enquiry["id"],
                inbox_query="", inbox_status="All statuses",
                flash=("success", f"{enquiry['id']} classified as {enquiry['label']}."))


def heading(title, description):
    st.title(title)
    st.caption(description)


def status_of(enquiry):
    return STATUS_LABELS[enquiry["status"]]


def display_name(enquiry):
    return redact_pii(enquiry["customer_name"])


def kind_of(enquiry):
    return "Built-in sample" if enquiry["sample_id"] else "Manual demo entry"


def picker(label, records, key):
    ids = {enquiry["id"]: enquiry for enquiry in records}
    if not ids:
        return None
    options = list(ids)
    if st.session_state.get(key) not in ids:
        selected = st.session_state.selected_enquiry
        st.session_state[key] = selected if selected in ids else options[0]
    choice = st.selectbox(
        label, options, key=key,
        format_func=lambda value: f"{value} · {ids[value]['label']} · {display_name(ids[value])}",
    )
    return ids.get(choice)


def risks_panel(risks):
    if not risks:
        st.caption("No flags detected. Review the context before making a decision.")
    for risk in risks:
        show = {"high": st.error, "medium": st.warning, "low": st.info}[risk["severity"]]
        show(f"**{risk['title']}** · {risk['severity'].title()}\n\n{risk['detail']}")


def show_message(enquiry):
    st.header("Customer message")
    st.text(f"{display_name(enquiry)}  ·  {enquiry['channel']}")
    st.caption(f"{enquiry['id']} · {kind_of(enquiry)} · {enquiry['label']} · {status_of(enquiry)}")
    st.code(redact_pii(enquiry["message"]), language=None, wrap_lines=True)
    st.caption(f"Keyword confidence: {enquiry['confidence']} · {enquiry['received_at'] or 'Earlier session record'}")


def case_controls(enquiry, *, drafting=False):
    status = enquiry["status"]
    if status in (Status.CLASSIFIED, Status.DRAFT_READY):
        if not drafting:
            st.button("Open in Draft Studio", on_click=navigate, args=("Draft Studio", enquiry["id"]))
        if drafting or status == Status.CLASSIFIED:
            st.button("Open escalation review", on_click=navigate,
                      args=("Approval Centre", enquiry["id"]))
    elif status == Status.PENDING_REVIEW:
        st.button("Open in Approval Centre", on_click=navigate, args=("Approval Centre", enquiry["id"]))
    elif status == Status.APPROVED:
        st.button("Open approved reply", on_click=navigate, args=("Approval Centre", enquiry["id"]))


def page_dashboard():
    st.markdown(
        '<div class="hero"><div class="mode">Human-controlled</div><h1>Support overview</h1>'
        '<p>Review customer enquiries, prepare safe replies and keep the final decision with your team.</p></div>',
        unsafe_allow_html=True,
    )
    enquiries = st.session_state.enquiries
    events = st.session_state.log
    statuses = [e["status"] for e in enquiries]
    with st.container(key="dashboard_metrics"):
        metrics = (
            ("Total enquiries", len(enquiries)),
            ("Pending reviews", statuses.count(Status.PENDING_REVIEW)),
            ("Flagged enquiries", sum(bool(e["risks"]) for e in enquiries)),
            ("Approved drafts", statuses.count(Status.APPROVED)),
            ("Rejected drafts", statuses.count(Status.REJECTED)),
        )
        for column, (label, value) in zip(st.columns(5), metrics):
            column.metric(label, value)

    with st.container(horizontal=True):
        st.button("Open inbox", type="primary", on_click=navigate, args=("Customer Enquiries",))
        st.button("Load fictional samples", key="load_samples", on_click=load_samples,
                  disabled=st.session_state.samples_loaded)
    left, right = st.columns([1, 1.1])
    with left, st.container(border=True):
        st.header("Enquiries by category")
        if enquiries:
            counts = pd.Series([e["label"] for e in enquiries]).value_counts()
            data = counts.rename_axis("Category").reset_index(name="Enquiries")
            categories = alt.Chart(data).encode(
                x=alt.X("Enquiries:Q", axis=alt.Axis(tickMinStep=1), scale=alt.Scale(domain=[0, int(counts.max()) + 1])),
                y=alt.Y("Category:N", title=None, sort="-x",
                        axis=alt.Axis(labelOverlap=False, labelPadding=7, labelLimit=110)),
                tooltip=["Category:N", "Enquiries:Q"],
            )
            bars = categories.mark_bar(color="#2563EB", cornerRadiusEnd=4)
            values = categories.mark_text(align="left", dx=7, color="#334155").encode(text="Enquiries:Q")
            chart = (bars + values).properties(height=max(110, len(counts) * 29)).configure_axis(
                labelColor="#475569", titleColor="#475569",
            )
            st.altair_chart(chart)
            st.caption(" · ".join(f"{category} {count}" for category, count in counts.items()))
        else:
            st.caption("Category counts will appear once you add an enquiry or load the fictional samples.")
    with right, st.container(border=True):
        st.header("Recent activity")
        if events:
            for item in reversed(events[-5:]):
                st.write(f"**{item['action']}** · {item['category']}  \n{item['enquiry_id']} · {item['status']}")
        else:
            st.caption("Classifications, draft changes and review decisions will appear here.")
    if enquiries:
        times = pd.to_datetime([e["received_at"] for e in enquiries if e["received_at"]], utc=True, errors="coerce")
        if times.notna().any():
            trend = pd.Series(1, index=times.dropna().floor("D")).resample("D").sum()
            with st.expander("Daily enquiry activity (UTC)"):
                st.bar_chart(trend.rename("Enquiries"))


def page_enquiries():
    heading("Customer Enquiries", "Classify, search and open enquiries in this session.")
    st.button("Load fictional samples", key="inbox_samples", on_click=load_samples,
              disabled=st.session_state.samples_loaded)
    with st.form("new_enquiry"):
        st.header("Add an enquiry")
        st.caption("Use fictional information only. The message can contain up to 4,000 characters.")
        col1, col2 = st.columns(2)
        col1.text_input("Customer name (fictional)", max_chars=70, key="customer_name")
        col2.selectbox("Channel", CHANNELS, key="customer_channel")
        st.text_area("Customer message", max_chars=MAX_MESSAGE, height=116,
                     placeholder="Example: Where is my order?", key="customer_message")
        st.form_submit_button("Add and classify", type="primary", on_click=submit_enquiry)
        error = st.session_state.pop("enquiry_form_error", None)
        if error:
            st.error(error)
    if not st.session_state.enquiries:
        st.info("Your inbox is empty. Add a fictional enquiry to begin.")
        return
    one, two = st.columns([2, 1])
    query = one.text_input("Search enquiries", placeholder="ID, name, category or message",
                           key="inbox_query").strip().casefold()
    status_filter = two.selectbox("Status", ("All statuses", *dict.fromkeys(STATUS_LABELS.values())),
                                  key="inbox_status")
    records = [
        enquiry for enquiry in st.session_state.enquiries
        if (status_filter == "All statuses" or status_of(enquiry) == status_filter)
        and query in " ".join((enquiry["id"], display_name(enquiry), enquiry["label"],
                               redact_pii(enquiry["message"]))).casefold()
    ]
    if not records:
        st.info("No enquiries match these filters.")
        return
    st.dataframe(pd.DataFrame([{
        "Enquiry": e["id"], "Customer": display_name(e), "Category": e["label"],
        "Risk": risk_level(e["risks"]).title(), "Status": status_of(e), "Data": kind_of(e),
    } for e in reversed(records)]), hide_index=True)
    enquiry = picker("Open enquiry", list(reversed(records)), "detail_pick")
    with st.container(border=True):
        show_message(enquiry)
        risks_panel(enquiry["risks"])
        if enquiry["decision_reason"]:
            st.text(f"Decision reason: {enquiry['decision_reason']}")
        case_controls(enquiry)


def make_template(enquiry):
    policies = st.session_state.policies
    return rule_based_reply(enquiry["category"], enquiry["customer_name"], policies,
                            st.session_state.business_name, review_risks(enquiry, policies),
                            message=enquiry["message"])


def page_drafting():
    heading("Draft Studio", "Generate a reply, review the flags and submit it for human approval.")
    candidates = [e for e in st.session_state.enquiries if e["status"] in DRAFTABLE | {Status.PENDING_REVIEW}]
    enquiry = picker("Enquiry to draft", candidates, "draft_pick")
    if not enquiry:
        st.info("There are no open enquiries. Start in Customer Enquiries.")
        return
    left, right = st.columns(2)
    policies = st.session_state.policies
    message_risks = review_risks(enquiry, policies)
    with left, st.container(border=True):
        show_message(enquiry)
        risks_panel(message_risks)
        case_controls(enquiry, drafting=True)
    with right, st.container(border=True):
        st.header("Suggested response")
        if enquiry["status"] == Status.PENDING_REVIEW:
            st.caption("Pending review · " + enquiry["draft_source"])
            st.code(redact_pii(enquiry["final_reply"]), language=None, wrap_lines=True)
            return
        key = f"draft_editor_{enquiry['id']}"
        if st.button("Generate rule-based draft", key=f"rule_{enquiry['id']}", type="primary"):
            save_draft(enquiry, st.session_state.log, make_template(enquiry), policies)
            st.session_state.pop(key, None)
            notice("Rule-based draft ready.")
        if st.session_state.mode == AI_MODE:
            api_key = setting("GEMINI_API_KEY")
            if not api_key or not verified_sample(enquiry):
                st.caption("AI-assisted drafting requires a configured key and an eligible built-in fictional sample.")
            else:
                consent = st.checkbox("Send this built-in fictional message to Google Gemini.",
                                      key=f"consent_{enquiry['id']}")
                if st.button("Generate AI-assisted draft", disabled=not consent, key=f"ai_{enquiry['id']}"):
                    with st.spinner("Requesting an acknowledgement from Gemini…"):
                        draft, warning = generate_draft(
                            enquiry, make_template(enquiry), api_key, setting("GEMINI_MODEL") or DEFAULT_MODEL,
                        )
                    save_draft(enquiry, st.session_state.log, draft, policies)
                    st.session_state.pop(key, None)
                    notice(warning or "AI-assisted draft ready.", "warning" if warning else "success")
        if enquiry["status"] in EDITABLE:
            st.caption(f"{enquiry['draft_source']} · Draft ready")
            reply = st.text_area("Edit draft", enquiry["final_reply"], key=key, height=240, max_chars=MAX_REPLY)
            message_codes = risk_codes(message_risks)
            draft_risks = [risk for risk in review_risks(enquiry, policies, reply) if risk["code"] not in message_codes]
            if draft_risks:
                risks_panel(draft_risks)
            else:
                st.caption("No additional draft flags detected.")
            save, submit = st.columns(2)
            try:
                if save.button("Save edits", key=f"save_{enquiry['id']}"):
                    edit_draft(enquiry, st.session_state.log, reply, policies)
                    notice("Draft saved.")
                if submit.button("Submit for review", key=f"submit_{enquiry['id']}", type="primary"):
                    request_review(enquiry, st.session_state.log, reply, policies)
                    st.session_state.selected_enquiry = enquiry["id"]
                    notice("Draft submitted to the Approval Centre.")
            except ValueError as exc:
                st.error(str(exc))
        else:
            st.caption("Generate a draft to begin. Your team reviews the reply before it becomes available to copy.")


def page_approval():
    heading("Approval Centre", "Review the proposed reply and record a human decision. Approved replies are available to copy.")
    replies = [e for e in st.session_state.enquiries if e["status"] == Status.APPROVED]
    selected = st.session_state.selected_enquiry
    default_tab = "Approved replies" if any(e["id"] == selected for e in replies) else "Review queue"
    pending, approved = st.tabs(["Review queue", "Approved replies"], default=default_tab)
    with pending:
        render_review_queue()
    with approved:
        if not replies:
            st.caption("Approved replies will appear here.")
        for enquiry in reversed(replies):
            with st.expander(f"{enquiry['id']} · Approved — Not Sent",
                             expanded=enquiry["id"] == st.session_state.selected_enquiry):
                st.caption(f"{enquiry['draft_source']} · {enquiry['reviewer'] or 'Earlier session reviewer'}")
                st.code(redact_pii(enquiry["final_reply"]), language=None, wrap_lines=True)


def revise(enquiry):
    return_for_revision(enquiry, st.session_state.log)
    navigate("Draft Studio", enquiry["id"])
    st.session_state.flash = ("success", "Draft returned for revision.")


def render_review_queue():
    selected = st.session_state.selected_enquiry
    queue = [
        e for e in st.session_state.enquiries
        if e["status"] == Status.PENDING_REVIEW or (e["id"] == selected and e["status"] in DRAFTABLE)
    ]
    enquiry = picker("Enquiry to review", queue, "approve_pick")
    if not enquiry:
        st.info("No drafts are pending. Submit a draft from Draft Studio.")
        return
    identifier = enquiry["id"]
    is_pending = enquiry["status"] == Status.PENDING_REVIEW
    policies = st.session_state.policies
    left, right = st.columns(2)
    with left, st.container(border=True):
        show_message(enquiry)
    with right, st.container(border=True):
        st.header("Review decision")
        reply = ""
        if is_pending:
            st.caption(f"{enquiry['draft_source']} · Pending review")
            reply = st.text_area("Edit reply before deciding", enquiry["final_reply"], height=230,
                                 max_chars=MAX_REPLY, key=f"review_reply_{identifier}")
        current_risks = review_risks(enquiry, policies, reply or None)
        risks_panel(current_risks)
        reviewer = st.selectbox("Reviewer", REVIEWERS, index=None, key=f"reviewer_{identifier}")
        reason = st.selectbox("Decision reason (optional)", REASONS, key=f"reason_{identifier}")
        acknowledged = False
        if is_pending and risk_level(current_risks) == "high":
            digest = hashlib.sha256(repr((reply, policies)).encode()).hexdigest()[:12]
            acknowledged = st.checkbox("I reviewed the high-severity flags for this version of the reply.",
                                       key=f"ack_{identifier}_{digest}")
        columns = st.columns(3) if is_pending else None
        actions = (
            (Status.APPROVED, "Approve draft", columns[0] if columns else None),
            (Status.REJECTED, "Reject draft", columns[1] if columns else None),
            (Status.ESCALATED, "Escalate", columns[2] if columns else st),
        )
        selected_action = None
        for target, label, location in actions:
            if location and location.button(label, type="primary" if target == Status.APPROVED else "secondary",
                                            key=f"{target.name.lower()}_{identifier}"):
                selected_action = target
        if is_pending:
            st.button("Return to Draft Studio", key=f"revise_{identifier}", on_click=revise, args=(enquiry,))
        if selected_action is None:
            return
        try:
            decide(enquiry, st.session_state.log, selected_action, reviewer, policies, reply=reply,
                   acknowledged=acknowledged, reason=reason)
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.session_state.selected_enquiry = identifier
            notice(f"{identifier} · {status_of(enquiry)}")


def page_log():
    heading("Activity Log", "Temporary session history. The log can be lost on reload and provides no tamper protection.")
    events = st.session_state.log
    if not events:
        st.info("Session activity will appear after an enquiry is added.")
        return
    one, two = st.columns([2, 1])
    query = one.text_input("Filter by enquiry ID").strip().casefold()
    action = two.selectbox("Action", ["All actions", *sorted({e["action"] for e in events})])
    rows = [entry for entry in reversed(events) if query in entry["enquiry_id"].casefold()
            and (action == "All actions" or entry["action"] == action)]
    if not rows:
        st.info("No events match these filters.")
        return
    st.download_button("Export filtered events (CSV)", log_to_csv(rows), "teviai_activity_log.csv", "text/csv",
                       on_click="ignore")
    st.caption(f"{len(rows)} matching events. The export includes workflow metadata and demo reviewer roles.")
    st.dataframe(log_to_dataframe(rows), hide_index=True)
    with st.expander("Read event details"):
        index = st.selectbox(
            "Event", range(len(rows)),
            format_func=lambda i: f"{rows[i]['action']} · {rows[i]['enquiry_id']} · {rows[i]['timestamp']}",
        )
        event = rows[index]
        st.text(f"Timestamp: {event['timestamp']}\nEnquiry: {event['enquiry_id']}\nAction: {event['action']}\n"
                f"Category: {event['category']}\nRisk: {event['risk_level']}\nFlags: {event['risk_flags'] or 'None'}\n"
                f"Draft mode: {event['draft_mode'] or 'None'}\nReviewer: {event['reviewer'] or 'None'}\n"
                f"Previous status: {event['previous_status'] or 'None'}\nStatus: {event['status']}")


def page_settings():
    heading("Settings", "Manage a fictional business profile and demo policies for this session.")
    st.info("Use synthetic data. Google Gemini can receive eligible built-in examples when you opt in during drafting.")
    with st.form("settings"):
        name = st.text_input("Fictional business name", st.session_state.business_name, max_chars=90)
        mode = st.selectbox("Drafting mode", [RULE_MODE, AI_MODE], index=int(st.session_state.mode == AI_MODE))
        st.caption("Blank policy fields direct the reviewer to verify the policy. Gemini uses server-side credentials.")
        policies = {
            key: st.text_area(label, st.session_state.policies.get(key, ""), max_chars=200, height=83)
            for key, label in POLICY_LABELS.items()
        }
        if st.form_submit_button("Save settings", type="primary"):
            if any(find_personal_data(text) and redact_pii(text) != text for text in [name, *policies.values()]):
                st.error("Remove detected personal or payment information before saving.")
            else:
                st.session_state.update(business_name=name.strip() or DEFAULT_BUSINESS_NAME,
                                        policies={key: value.strip() for key, value in policies.items()}, mode=mode)
                notice("Settings saved. Regenerate open drafts after policy changes.")
    with st.expander("Reset demo session"):
        confirm = st.checkbox("Clear this session’s enquiries, drafts, decisions and settings.", key="reset_confirm")
        if st.button("Reset demo data", disabled=not confirm):
            st.session_state.clear()
            notice("Demo session reset.")


def page_safety():
    heading("Safety Lab", "Run repeatable fictional scenarios against the same rules the workspace uses.")
    if st.button("Run safety evaluations", type="primary"):
        st.session_state.safety_results = run_scenarios()
    rows = st.session_state.safety_results
    if rows:
        st.metric("Scenarios passed", f"{sum(row['Result'] == 'Pass' for row in rows)} / {len(rows)}")
        st.dataframe(pd.DataFrame(rows), hide_index=True)
        st.caption("The Gemini failure scenario injects a local test double. These examples cover specific behaviours.")
    else:
        st.caption("Run the suite to compare expected and observed results.")


def main():
    initialise()
    styles = (Path(__file__).parent / "assets" / "styles.css").read_text(encoding="utf-8-sig")
    st.markdown(f"<style>{styles}</style>", unsafe_allow_html=True)
    pages = {
        "Dashboard": page_dashboard, "Customer Enquiries": page_enquiries, "Draft Studio": page_drafting,
        "Approval Centre": page_approval, "Activity Log": page_log, "Settings": page_settings,
        "Safety Lab": page_safety,
    }
    with st.sidebar:
        st.markdown(
            '<div class="brand"><span class="brand-mark" aria-hidden="true">✓</span>'
            '<div><div class="brand-name">TeviAI</div><div class="brand-caption">Support Studio</div></div></div>',
            unsafe_allow_html=True,
        )
        page = st.radio("Workspace navigation", list(pages), key="page", label_visibility="collapsed")
        st.divider()
        st.caption("Responsible Customer Support Automation")
        st.text(st.session_state.business_name)
        st.caption("Fictional data only · Temporary session")
    flash = st.session_state.flash
    if flash:
        st.session_state.flash = None
        if isinstance(flash, str):
            st.success(flash)
        else:
            getattr(st, flash[0])(flash[1])
    pages[page]()


main()
