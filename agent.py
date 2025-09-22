import os
import re
from dotenv import load_dotenv
from tavily import TavilyClient
from trafilatura import fetch_url, extract, extract_metadata
from PyPDF2 import PdfReader
from openai import OpenAI
import streamlit as st


# ---------------- Load API Keys ----------------
load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")

tavily_client = TavilyClient(TAVILY_KEY)
client = OpenAI(api_key=OPENAI_KEY)

MAX_CHARS_PER_SOURCE = 3000
MAX_TOKENS_SUMMARY = 400

# ---------------- Web Search ----------------
def search_web(query, num_results=3):
    """Search online using Tavily API."""
    try:
        results = tavily_client.search(query)
        urls = [r["url"] for r in results["results"][:num_results]]
        if not urls:
            st.warning("⚠️ No sources found for your query. Try rephrasing it.")
        return urls
    except Exception as e:
        st.error("Oops! Something went wrong during web search.")
        print(f"[SEARCH ERROR] {e}")
        return []

# ---------------- Content Extraction ----------------
def extract_text(url):
    """
    Extract text from URL.
    Supports HTML pages (via trafilatura) and PDFs (via PyPDF2).
    """
    try:
        if url.endswith(".pdf"):
            reader = PdfReader(url)
            text = "\n".join([p.extract_text() or "" for p in reader.pages])
            title = reader.metadata.title if reader.metadata and reader.metadata.title else f"PDF Document {url}"
            return {"text": text, "title": title, "url": url}
        else:
            html = fetch_url(url)
            if not html:
                return {"text": "", "title": url, "url": url}
            extracted = extract(html) or ""
            metadata = extract_metadata(html)
            title = metadata.get("title") if metadata and isinstance(metadata, dict) and metadata.get("title") else url
            return {"text": extracted, "title": title, "url": url}
    except Exception as e:
        st.warning(f"⚠️ Error extracting content from {url}. Skipping this source.")
        print(f"[EXTRACTION ERROR] {url} -> {e}")
        return {"text": "", "title": url, "url": url}

# ---------------- Summarization ----------------
def summarize_text(query, urls, texts, titles=None):
    """
    Generate bullet-point summaries for each source using OpenAI.
    The first bullet is the main point/title, no extra LLM call.
    """
    source_summaries = []

    if titles is None:
        titles = [extract_text(url)["title"] for url in urls]

    for i, text in enumerate(texts):
        if not text.strip():
            continue
        truncated_text = text[:MAX_CHARS_PER_SOURCE]
        clean_title = re.sub(r"^\s*(?:[IVXLCDM]+\.\s*|\d+\.\s*)", "", titles[i])

        # Single prompt per source, first bullet is the main point
        prompt = f"""
You are an expert research assistant.
Summarize the following content from source "{clean_title}" into 3-5 concise bullet points.
- Make the first bullet the main point or title of the source.
- Keep all bullets informative and clear.

Content:
{truncated_text}
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=MAX_TOKENS_SUMMARY
            )
            summary_text = response.choices[0].message.content.strip()
            bullets = [line.strip("-• ") for line in summary_text.split("\n") if line.strip()]
            source_summaries.append({
                "title": clean_title,
                "bullets": bullets,
                "url": urls[i]
            })
        except Exception as e:
            st.warning(f"⚠️ Summarization failed for source {urls[i]}")
            print(f"[LLM ERROR] {urls[i]} -> {e}")
            source_summaries.append({
                "title": clean_title,
                "bullets": ["Summary failed."],
                "url": urls[i]
            })

    return source_summaries
