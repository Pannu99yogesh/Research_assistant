import json
import os
from pathlib import Path
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

load_dotenv(override=True)

st.set_page_config(
    page_title="The Research Room",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- STORAGE ----------------

HISTORY_FILE = Path(__file__).parent / "research_history.json"


def load_history():
    """Load research history safely from JSON."""
    if not HISTORY_FILE.exists():
        return []
    try:
        with HISTORY_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_history(history):
    """Persist research history to JSON."""
    try:
        with HISTORY_FILE.open("w", encoding="utf-8") as file:
            json.dump(history, file, ensure_ascii=False, indent=2)
    except OSError as error:
        st.error(f"Could not save research history: {error}")


if "research_history" not in st.session_state:
    st.session_state.research_history = load_history()

if "page" not in st.session_state:
    st.session_state.page = "New research"

if "selected_research_id" not in st.session_state:
    st.session_state.selected_research_id = None



# ---------------- PDF EXPORT ----------------

def create_report_pdf(topic, report, plan="", sources=None):
    """Create a clean PDF containing the report, plan, and source links."""
    from io import BytesIO
    import re
    from xml.sax.saxutils import escape
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=18*mm, bottomMargin=18*mm,
        title=f"{topic} - Research Report"
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle", parent=styles["Title"],
        fontName="Helvetica-Bold", fontSize=22, leading=28,
        textColor=colors.HexColor("#263B55"), alignment=TA_LEFT,
        spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        name="ReportHeading", parent=styles["Heading2"],
        fontName="Helvetica-Bold", fontSize=14, leading=18,
        textColor=colors.HexColor("#263B55"), spaceBefore=12, spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name="ReportBody", parent=styles["BodyText"],
        fontName="Helvetica", fontSize=9.5, leading=14,
        textColor=colors.HexColor("#273342"), spaceAfter=6
    ))
    story = [Paragraph(escape(topic), styles["ReportTitle"]),
             Paragraph("RESEARCH REPORT", styles["Heading3"]),
             HRFlowable(width="100%", color=colors.HexColor("#D8D7D0")),
             Spacer(1, 10)]

    def add_markdown(text):
        for raw_line in (text or "").splitlines():
            line = raw_line.strip()
            if not line:
                story.append(Spacer(1, 4))
                continue
            if line.startswith("#"):
                heading = line.lstrip("#").strip()
                story.append(Paragraph(escape(heading), styles["ReportHeading"]))
                continue
            if line.startswith(("- ", "* ")):
                line = "• " + line[2:]
            elif re.match(r"^\d+\.\s", line):
                line = "• " + re.sub(r"^\d+\.\s", "", line)
            # Basic Markdown emphasis and inline code
            line = escape(line)
            line = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
            line = re.sub(r"\*(.+?)\*", r"<i>\1</i>", line)
            line = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", line)
            story.append(Paragraph(line, styles["ReportBody"]))

    add_markdown(report)
    if plan:
        story.append(Paragraph("Research Plan", styles["ReportHeading"]))
        add_markdown(plan)
    if sources:
        story.append(Paragraph("Research Sources", styles["ReportHeading"]))
        for idx, source in enumerate(sources, 1):
            title = escape(str(source.get("title", "Untitled")))
            url = escape(str(source.get("url", "")))
            story.append(Paragraph(f"{idx}. <b>{title}</b><br/>{url}", styles["ReportBody"]))
    doc.build(story)
    return buffer.getvalue()


# ---------------- CUSTOM DESIGN ----------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap');

:root {
    --paper: #F7F6F2;
    --navy: #263B55;
    --muted: #778391;
    --line: #E3E2DC;
    --blue: #E8EDF3;
}

.stApp { background: var(--paper); color: #273342; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2.5rem; padding-bottom: 4rem; max-width: 1200px; }
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #263B55 !important; }

[data-testid="stSidebar"] {
    background: #F0EFEA;
    border-right: 1px solid #D8D7D0;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 { color: #35465A !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 { font-weight: 600; }
[data-testid="stSidebar"] .stCaption { color: #758294 !important; }
[data-testid="stSidebarNav"] span { color: #35465A !important; }
[data-testid="stSidebar"] .block-container { padding-top: 2rem; }

.stTextArea textarea {
    background: #FFFFFF;
    border: 1px solid #E0E2E5;
    border-radius: 12px;
    font-size: 16px;
    padding: 16px;
}
.stTextArea textarea:focus { border-color: #7189A3; box-shadow: 0 0 0 1px #7189A3; }

.stButton > button {
    background: var(--navy);
    color: white;
    border: 1px solid var(--navy);
    border-radius: 9px;
    padding: 0.65rem 1.4rem;
    font-weight: 600;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    background: #354F6D;
    border-color: #354F6D;
    color: white;
    transform: translateY(-1px);
}
.stDownloadButton > button { border-radius: 9px; }
hr { border-color: var(--line); }
div[data-testid="stMetric"] {
    background: white; border: 1px solid var(--line);
    padding: 16px; border-radius: 12px;
}
.research-label {
    color: #788697; font-size: 12px; letter-spacing: 2px;
    font-weight: 700; text-transform: uppercase;
}
.hero-subtitle { color: #778391; font-size: 16px; line-height: 1.8; }

.stTextArea textarea {
    background-color: #FFFFFF !important;
    color: #263B55 !important;
    border: 1px solid #D6DDE5 !important;
    border-radius: 12px !important;
    caret-color: #263B55 !important;
}
.stTextArea textarea::placeholder { color: #8995A4 !important; opacity: 1 !important; }
.stTextArea label, .stSelectbox label { color: #52647A !important; font-weight: 600 !important; }
.stSelectbox [data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    border: 1px solid #D6DDE5 !important;
    border-radius: 9px !important;
}
.stSelectbox [data-baseweb="select"] span { color: #263B55 !important; }
.stSelectbox [data-baseweb="select"] svg { fill: #52647A !important; }
[data-baseweb="popover"] li { color: #263B55 !important; background-color: #FFFFFF !important; }
.stButton button:disabled {
    background-color: #E2E7ED !important; color: #52647A !important;
    border: 1px solid #D1D9E2 !important; opacity: 1 !important;
    cursor: not-allowed !important;
}
div[style*="text-align:center"] { color: #758294 !important; }

/* Sidebar selected navigation */
div[data-testid="stSidebar"] button[kind="secondary"] {
    background: transparent;
    color: #35465A;
    border: 1px solid transparent;
    text-align: left;
}
div[data-testid="stSidebar"] button[kind="primary"] {
    background: #E1E7ED;
    color: #263B55;
    border: 1px solid #D1D9E2;
    text-align: left;
}

/* Sidebar navigation buttons */
[data-testid="stSidebar"] .stButton > button {
    background-color: #263B55 !important;
    color: #FFFFFF !important;
    border: 1px solid #263B55 !important;
}

/* Force sidebar button text to remain white */
[data-testid="stSidebar"] .stButton > button p {
    color: #FFFFFF !important;
}

/* Hover effect */
[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #354F6D !important;
    border-color: #354F6D !important;
}

</style>
""", unsafe_allow_html=True)


# ---------------- SIDEBAR ----------------

with st.sidebar:
    st.markdown("""
    <div style="font-family:'Playfair Display';font-size:25px;
                font-weight:600;color:#263B55;">
        ◈ Research Room
    </div>
    <div style="color:#82909E;font-size:12px;margin-top:5px;">
        YOUR PERSONAL RESEARCH DESK
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("##### Workspace")

    current_page = st.session_state.page

    if st.button(
        "📖  New research",
        use_container_width=True,
        type="primary" if current_page == "New research" else "secondary",
        key="nav_new"
    ):
        st.session_state.page = "New research"
        st.session_state.selected_research_id = None
        st.rerun()

    if st.button(
        "🗂️  Research library",
        use_container_width=True,
        type="primary" if current_page == "Research library" else "secondary",
        key="nav_library"
    ):
        st.session_state.page = "Research library"
        st.rerun()

    if st.button(
        "📑  Saved reports",
        use_container_width=True,
        type="primary" if current_page == "Saved reports" else "secondary",
        key="nav_saved"
    ):
        st.session_state.page = "Saved reports"
        st.rerun()

    st.divider()
    st.markdown("##### About")
    st.caption("An intelligent research workspace built for curious minds.")
    st.divider()
    st.caption("DESIGNED FOR DEEP THINKING · 2026")


# ---------------- PAGE: NEW RESEARCH ----------------

if st.session_state.page == "New research":

    st.markdown(
        '<div class="research-label">YOUR INTELLIGENT RESEARCH WORKSPACE</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    <h1 style="font-size:54px;line-height:1.2;margin-top:15px;">
        The Research Room<span style="color:#9AAABD;">.</span>
    </h1>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="hero-subtitle">
        Good research begins with a good question.<br>
        Let's explore something worth understanding.
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    st.write("")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**01 — Explore**")
        st.caption("Discover information from the web.")
    with col2:
        st.markdown("**02 — Understand**")
        st.caption("Analyze evidence and key findings.")
    with col3:
        st.markdown("**03 — Synthesize**")
        st.caption("Create a structured research report.")

    st.write("")
    st.divider()
    st.write("")

    st.markdown("### What are you curious about?")
    st.caption("Enter a question, topic, or problem you want to investigate.")

    topic = st.text_area(
        "Research topic",
        placeholder=(
            "e.g. How are autonomous AI agents "
            "transforming software engineering?"
        ),
        height=130,
        label_visibility="collapsed",
        key="research_topic_input"
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        depth = st.selectbox(
            "Research depth",
            ["Quick exploration", "Standard research"],
            index=0
        )
    with col2:
        focus = st.selectbox(
            "Research focus",
            [
                "General overview",
                "Technical analysis",
                "Latest developments",
                "Advantages & limitations"
            ]
        )

    st.write("")
    start = st.button(
        "Begin research  →",
        type="primary",
        disabled=not topic.strip(),
        use_container_width=True
    )

    if start:
        from graph import run_research

        st.session_state["research_topic"] = topic
        st.session_state["research_depth"] = depth
        st.session_state["research_focus"] = focus

        st.write("")
        st.divider()
        st.markdown("## Research workspace")
        st.caption(f"Investigating: {topic}")

        with st.status("Planning your research...", expanded=True) as status:
            st.write("🔄 Planner → Researcher → Writer")
            try:
                result = run_research(topic=topic, depth=depth, focus=focus)

                plan = result.get("plan", "")
                sources = result.get("sources", [])
                report = result.get("report", "")

                status.update(
                    label="Research completed successfully",
                    state="complete",
                    expanded=False
                )

                # Save only if report exists
                if report.strip():
                    research_item = {
                        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                        "topic": topic.strip(),
                        "depth": depth,
                        "focus": focus,
                        "plan": plan,
                        "report": report,
                        "sources": sources,
                        "created_at": datetime.now().strftime("%d %b %Y, %I:%M %p")
                    }
                    st.session_state.research_history.insert(0, research_item)
                    save_history(st.session_state.research_history)

                with st.container(border=True):
                    st.markdown("## 🧠 Research Plan")
                    st.markdown(plan)

                st.divider()
                with st.container(border=True):
                    st.markdown("## 📄 Research Report")
                    if report.strip():
                        st.markdown(report)
                    else:
                        st.warning("Writer returned an empty report.")

                if report.strip():
                    try:
                        pdf_bytes = create_report_pdf(topic, report, plan, sources)
                        st.download_button(
                            "⬇️ Download research as PDF",
                            data=pdf_bytes,
                            file_name=f"{topic.strip().replace(' ', '_')}_research.pdf",
                            mime="application/pdf",
                            type="primary",
                            key="download_current_research_pdf"
                        )
                    except ImportError:
                        st.warning("PDF export needs ReportLab. Install it with: pip install reportlab")

                st.divider()
                with st.container(border=True):
                    st.markdown("## 🔎 Research Sources")
                    st.caption(f"Collected {len(sources)} web sources")
                    if sources:
                        for i, source in enumerate(sources, 1):
                            with st.expander(f"{i}. {source.get('title', 'Untitled')}"):
                                st.markdown(f"[Open source]({source.get('url', '')})")
                                st.write(source.get("snippet", ""))
                                st.caption(f"Search query: {source.get('query', '')}")
                    else:
                        st.warning("No sources collected.")

            except Exception as e:
                status.update(label="Research encountered an error", state="error")
                st.error(str(e))


# ---------------- PAGE: RESEARCH LIBRARY ----------------

elif st.session_state.page == "Research library":

    st.markdown('<div class="research-label">YOUR RESEARCH COLLECTION</div>', unsafe_allow_html=True)
    st.title("🗂️ Research Library")
    st.caption("All completed research sessions saved on this device.")
    st.divider()

    history = st.session_state.research_history

    if not history:
        st.info("Your library is empty. Start a new research session to see it here.")
        if st.button("Start new research →", type="primary"):
            st.session_state.page = "New research"
            st.rerun()
    else:
        st.caption(f"{len(history)} research project(s)")
        for item in history:
            with st.container(border=True):
                st.markdown(f"### {item.get('topic', 'Untitled research')}")
                st.caption(item.get("created_at", ""))
                st.write(item.get("focus", "General overview"))

                col_a, col_b = st.columns([1, 1])
                with col_a:
                    if st.button("Open report →", key=f"open_{item['id']}", use_container_width=True):
                        st.session_state.selected_research_id = item["id"]
                        st.session_state.page = "Saved reports"
                        st.rerun()
                with col_b:
                    st.download_button(
                        "Download Markdown",
                        data=item.get("report", ""),
                        file_name=f"{item.get('topic', 'research').replace(' ', '_')}.md",
                        mime="text/markdown",
                        key=f"library_download_{item['id']}",
                        use_container_width=True
                    )


# ---------------- PAGE: SAVED REPORTS ----------------

elif st.session_state.page == "Saved reports":

    st.markdown('<div class="research-label">YOUR WRITTEN WORK</div>', unsafe_allow_html=True)
    st.title("📑 Saved Reports")
    st.caption("Open, review, or download your completed research reports.")
    st.divider()

    history = st.session_state.research_history

    if not history:
        st.info("No saved reports yet. Complete a research session first.")
    else:
        selected_id = st.session_state.selected_research_id
        selected_item = next(
            (item for item in history if item.get("id") == selected_id),
            None
        )

        if selected_item is None:
            selected_item = history[0]

        options = {
            item["id"]: f"{item.get('topic', 'Untitled')} — {item.get('created_at', '')}"
            for item in history
        }

        selected_id = st.selectbox(
            "Choose a report",
            options=list(options.keys()),
            format_func=lambda value: options[value],
            index=list(options.keys()).index(selected_item["id"])
        )
        selected_item = next(item for item in history if item["id"] == selected_id)
        st.session_state.selected_research_id = selected_id

        st.markdown(f"## {selected_item.get('topic', 'Research Report')}")
        st.caption(
            f"{selected_item.get('created_at', '')} · "
            f"{selected_item.get('depth', 'Quick exploration')} · "
            f"{selected_item.get('focus', 'General overview')}"
        )

        download_col1, download_col2 = st.columns(2)
        with download_col1:
            st.download_button(
                "⬇️ Download report (.md)",
                data=selected_item.get("report", ""),
                file_name=f"{selected_item.get('topic', 'research').replace(' ', '_')}.md",
                mime="text/markdown",
                type="primary"
            )
        with download_col2:
            try:
                saved_pdf = create_report_pdf(
                    selected_item.get("topic", "Research Report"),
                    selected_item.get("report", ""),
                    selected_item.get("plan", ""),
                    selected_item.get("sources", [])
                )
                st.download_button(
                    "📄 Download as PDF",
                    data=saved_pdf,
                    file_name=f"{selected_item.get('topic', 'research').replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    type="primary"
                )
            except ImportError:
                st.caption("PDF: install ReportLab (pip install reportlab)")

        st.divider()
        with st.container(border=True):
            st.markdown(selected_item.get("report", "No report content available."))

        with st.expander("View research plan"):
            st.markdown(selected_item.get("plan", "No plan saved."))

        with st.expander(f"View sources ({len(selected_item.get('sources', []))})"):
            for index, source in enumerate(selected_item.get("sources", []), 1):
                st.markdown(f"**{index}. [{source.get('title', 'Untitled')}]({source.get('url', '')})**")
                st.write(source.get("snippet", ""))
                st.caption(f"Search query: {source.get('query', '')}")
                st.divider()

        st.divider()
        if st.button("🗑️ Delete this saved report", key=f"delete_{selected_item['id']}"):
            st.session_state.research_history = [
                item for item in st.session_state.research_history
                if item.get("id") != selected_item["id"]
            ]
            save_history(st.session_state.research_history)
            st.session_state.selected_research_id = None
            st.success("Report deleted.")
            st.rerun()