from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path

from stork_agent.config import PROFILES_PATH
from stork_agent.config import load_profiles
from stork_agent.config import save_profiles
from stork_agent.connectors import CONNECTORS
from stork_agent.models import UserProfile
from stork_agent.pipeline import run_daily
from stork_agent.storage.sqlite import SQLiteStore
from stork_agent.storage.sqlite import paper_key


DB_PATH = Path("data/stork_agent.sqlite3")
REPORT_DIR = Path("docs/stork")
SECRET_NAMES = (
    "OPENALEX_API_KEY",
    "SEMANTIC_SCHOLAR_API_KEY",
    "NCBI_EMAIL",
    "NCBI_API_KEY",
    "MAIL_USERNAME",
    "MAIL_AUTH_CODE",
    "WOS_API_KEY",
    "WOS_API_TYPE",
    "ELSEVIER_API_KEY",
    "ELSEVIER_INST_TOKEN",
    "IEEE_API_KEY",
    "OPENURL_BASE_URL",
    "ALERT_EMAIL_SAMPLE_PATH",
)


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="auto-stork", layout="wide")
    st.title("auto-stork")

    page = st.sidebar.radio(
        "View",
        ("Dashboard", "Research Profile", "Sources", "Daily Digest", "Feedback"),
    )

    if page == "Dashboard":
        dashboard_page(st)
    elif page == "Research Profile":
        profile_page(st)
    elif page == "Sources":
        sources_page(st)
    elif page == "Daily Digest":
        digest_page(st)
    else:
        feedback_page(st)


def dashboard_page(st) -> None:
    profiles = load_profiles()
    profile = profiles[0]
    col1, col2, col3 = st.columns(3)
    store = SQLiteStore(DB_PATH)
    try:
        runs = store.recent_runs(1)
        papers = store.recent_papers(10)
    finally:
        store.close()

    col1.metric("Profile", profile.name)
    col2.metric("Recent Papers", len(papers))
    col3.metric("Last Run", runs[0]["created_at"] if runs else "No run")

    if st.button("Run Dry Check"):
        with st.spinner("Running sources..."):
            papers = run_daily(dry_run=True)
        st.success(f"Found {len(papers)} new recommendation(s).")

    st.subheader("Today's Recommendations")
    if not papers:
        st.info("No stored recommendations yet. Run the agent to populate SQLite.")
    for paper in papers:
        render_paper_summary(st, paper)

    st.subheader("Source Health")
    health_rows = []
    env = dict(os.environ)
    for source_name in profile.sources:
        connector_cls = CONNECTORS.get(source_name)
        if not connector_cls:
            health_rows.append({"source": source_name, "status": "unknown", "message": "not registered"})
            continue
        health = connector_cls(env).healthcheck()
        health_rows.append({"source": source_name, "status": health["status"], "message": health["message"]})
    st.dataframe(health_rows, use_container_width=True)


def profile_page(st) -> None:
    profiles = load_profiles()
    names = [profile.name for profile in profiles]
    selected = st.selectbox("Profile", names)
    index = names.index(selected)
    profile = profiles[index]

    with st.form("profile_form"):
        name = st.text_input("Name", profile.name)
        keywords = st.text_area("Keywords", "\n".join(profile.keywords), height=140)
        exclude_keywords = st.text_area("Exclude Keywords", "\n".join(profile.exclude_keywords), height=100)
        sources = st.multiselect("Sources", sorted(CONNECTORS), default=[source for source in profile.sources if source in CONNECTORS])
        focus_authors = st.text_area("Focus Authors", "\n".join(profile.focus_authors), height=80)
        focus_venues = st.text_area("Focus Venues", "\n".join(profile.focus_venues), height=80)
        lookback_days = st.number_input("Lookback Days", min_value=1, max_value=90, value=profile.lookback_days)
        daily_limit = st.number_input("Daily Limit", min_value=1, max_value=200, value=profile.daily_limit)
        min_score = st.number_input("Minimum Score", min_value=0.0, max_value=100.0, value=float(profile.min_score))
        strict_api_keys = st.checkbox("Strict API Keys", value=profile.strict_api_keys)
        submitted = st.form_submit_button("Save Profile")

    if submitted:
        profiles[index] = UserProfile(
            name=name.strip() or profile.name,
            keywords=lines_to_tuple(keywords),
            exclude_keywords=lines_to_tuple(exclude_keywords),
            sources=tuple(sources),
            lookback_days=int(lookback_days),
            daily_limit=int(daily_limit),
            min_score=float(min_score),
            focus_authors=lines_to_tuple(focus_authors),
            focus_venues=lines_to_tuple(focus_venues),
            strict_api_keys=strict_api_keys,
        )
        save_profiles(profiles, PROFILES_PATH)
        st.success("Profile saved.")


def sources_page(st) -> None:
    st.subheader("Environment Secrets")
    rows = secret_status_rows(os.environ)
    st.dataframe(rows, use_container_width=True)

    st.caption("Values entered here are only set for the current Streamlit process and are not written to config files.")
    with st.form("session_secrets"):
        updates = {}
        for name in SECRET_NAMES:
            updates[name] = st.text_input(name, type="password", value="")
        submitted = st.form_submit_button("Set For This Session")
    if submitted:
        for name, value in updates.items():
            if value:
                os.environ[name] = value
        st.success("Session environment updated.")

    st.subheader("Reserved Institutional Sources")
    st.write("Web of Science, Elsevier, IEEE, alert email parsing, and OpenURL resolver are available as skeleton connectors. Use official APIs, email alerts, or resolver URLs only.")


def digest_page(st) -> None:
    reports = sorted(REPORT_DIR.glob("*.md"), reverse=True)
    if not reports:
        st.info("No Markdown reports found.")
        return
    selected = st.selectbox("Report", [report.name for report in reports])
    report_path = REPORT_DIR / selected
    markdown = report_path.read_text(encoding="utf-8")
    st.download_button("Export Markdown", markdown, file_name=selected)
    html_path = report_path.with_suffix(".html")
    if html_path.exists():
        st.download_button("Export HTML", html_path.read_text(encoding="utf-8"), file_name=html_path.name)
    st.markdown(markdown)


def feedback_page(st) -> None:
    store = SQLiteStore(DB_PATH)
    try:
        papers = store.recent_papers(50)
        if not papers:
            st.info("No stored papers available for feedback.")
            return
        titles = [paper.title for paper in papers]
        selected = st.selectbox("Paper", titles)
        paper = papers[titles.index(selected)]
        feedback = st.radio(
            "Feedback",
            ("favorite", "not_interested", "more_like_this", "less_like_this"),
            horizontal=True,
        )
        if st.button("Save Feedback"):
            store.save_feedback(paper_key(paper.doi, paper.title), feedback)
            st.success("Feedback saved.")
        render_paper_summary(st, paper)
    finally:
        store.close()


def render_paper_summary(st, paper) -> None:
    with st.expander(f"[{paper.recommendation_score}] {paper.title}", expanded=False):
        st.write(f"Source: {paper.source}")
        st.write(f"Reason: {paper.recommendation_reason or 'No reason recorded'}")
        st.write(f"Innovation: {paper.innovation_summary or 'No summary recorded'}")
        if paper.url:
            st.link_button("Open Record", paper.url)
        if paper.abstract:
            st.write(paper.abstract)


def lines_to_tuple(value: str) -> tuple[str, ...]:
    return tuple(line.strip() for line in value.splitlines() if line.strip())


def secret_status_rows(env) -> list[dict[str, str]]:
    return [{"name": name, "status": "configured" if env.get(name) else "missing"} for name in SECRET_NAMES]


if __name__ == "__main__":
    main()
