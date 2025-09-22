import streamlit as st
from agent import search_web, extract_text, summarize_text
from db import init_db, save_report, get_reports, get_report_by_id
from utils import generate_pdf, format_summary

# ---------------- Initialize DB ----------------
init_db()

# ---------------- Page setup ----------------
st.set_page_config(
    page_title="🧠 AI Research Agent",
    page_icon="🤖",
    layout="wide"
)

st.markdown("<h1 style='text-align:center; color:#4B0082;'>🤖 AI Research Agent</h1>", unsafe_allow_html=True)
st.markdown("---")

# ---------------- User Query ----------------
query = st.text_input("💬 Enter your research query:")

if st.button("🚀 Generate Report") and query:
    # --- Step 1: Check if this query already exists in DB ---
    past_reports = get_reports()
    existing = next((r for r in past_reports if r[1].lower() == query.lower()), None)
    
    if existing:
        # Load report from DB
        report = get_report_by_id(existing[0])
        formatted_summary = format_summary(report["summary"])
        st.markdown(f"<h3 style='color:#000000;'>💬 Query: {query}</h3>", unsafe_allow_html=True)
        st.markdown(formatted_summary, unsafe_allow_html=True)

        pdf_file = generate_pdf(report["summary"], filename=f"Report_{existing[0]}.pdf")
        with open(pdf_file, "rb") as f:
            st.download_button(
                label="📥 Download Report as PDF",
                data=f,
                file_name=f"Report_{existing[0]}.pdf",
                mime="application/pdf"
            )

    else:
        # --- Step 2: Search and extract sources ---
        st.info("🔍 Searching for sources...")
        urls = search_web(query)

        if not urls:
            st.error("⚠️ No search results found. Try a different query.")
        else:
            results = []
            texts = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, url in enumerate(urls):
                status_text.text(f"📝 Extracting content from source {i+1}/{len(urls)}")
                try:
                    result = extract_text(url)
                    if not result["text"].strip():
                        st.warning(f"⚠️ Skipped empty source: {url}")
                        continue  # skip empty sources
                    results.append(result)
                    texts.append(result["text"])
                except Exception as e:
                    st.warning(f"⚠️ Failed to fetch {url}, skipping this source.")
                    print(f"[EXTRACTION ERROR] {url} -> {e}")
                progress_bar.progress(int((i+1)/len(urls)*50))

            if not results:
                st.error("⚠️ No valid sources to summarize.")
                progress_bar.empty()
                status_text.empty()
            else:
                titles = [r["title"] for r in results]

                # --- Summarization ---
                status_text.text("🤖 Summarizing content with AI...")
                with st.spinner("🕐 AI is generating the summary..."):
                    try:
                        summary = summarize_text(query, [r["url"] for r in results], texts, titles=titles)
                    except Exception as e:
                        st.error("⚠️ AI summarization failed. Try again later.")
                        print(f"[LLM ERROR] {e}")
                        summary = []  # fallback

                    progress_bar.progress(100)

                # --- Save report ---
                try:
                    save_report(query, summary, titles=titles, urls=[r["url"] for r in results])
                    st.success("✅ Report saved!")
                except Exception as e:
                    st.error("⚠️ Failed to save report.")
                    print(f"[DB ERROR] {e}")

                progress_bar.empty()
                status_text.empty()

                # Display Query
                st.markdown(f"<h3 style='color:#000000;'>💬 Query: {query}</h3>", unsafe_allow_html=True)

                # Format summary for display
                formatted_summary = format_summary(summary)
                st.markdown(formatted_summary, unsafe_allow_html=True)

                # PDF Download
                try:
                    pdf_file = generate_pdf(summary, filename="AI_Research_Report.pdf")
                    with open(pdf_file, "rb") as f:
                        st.download_button(
                            label="📥 Download Report as PDF",
                            data=f,
                            file_name="AI_Research_Report.pdf",
                            mime="application/pdf"
                        )
                except Exception as e:
                    st.error("⚠️ Failed to generate PDF.")
                    print(f"[PDF ERROR] {e}")

# ---------------- Past Reports ----------------
st.header("📚 Past Reports")
reports = get_reports()

if reports:
    for r in reports:
        report_id = r[0]
        report_query = r[1]
        timestamp = r[2]
        report = get_report_by_id(report_id)
        if not report:
            continue

        with st.expander(f"📝 {report_query}  ⏰ {timestamp}"):
            formatted_summary = format_summary(report["summary"])
            st.markdown(formatted_summary, unsafe_allow_html=True)

            pdf_file = generate_pdf(report["summary"], filename=f"Report_{report_id}.pdf")
            with open(pdf_file, "rb") as f:
                st.download_button(
                    label=f"📥 Download Report PDF",
                    data=f,
                    file_name=f"Report_{report_id}.pdf",
                    mime="application/pdf"
                )
else:
    st.info("ℹ️ No past reports yet. Generate your first report above!")
    