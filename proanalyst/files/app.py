"""
app.py — Part B3: Streamlit UI
================================
Run with:
    streamlit run app.py

Make sure you have:
  1. Created a .env file with DEEPINFRA_API_KEY set.
  2. Run `python ingest.py` at least once to populate the ChromaDB store.
"""

import os

import streamlit as st
from dotenv import load_dotenv

# Load .env before importing rag so get_llm() sees DEEPINFRA_API_KEY
load_dotenv()

from rag import answer_query, get_rag_components

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Upwork API Support Bot",
    page_icon="🔧",
    layout="wide",
)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🔧 Upwork API Support Bot")
st.caption(
    "A RAG-powered assistant that answers developer questions "
    "using the official Upwork API documentation."
)
st.divider()


# ── Load RAG components (cached so they survive reruns) ───────────────────────
@st.cache_resource(show_spinner="Loading knowledge base and LLM…")
def load_components():
    """
    st.cache_resource caches the return value across all sessions and reruns.
    This means the embedding model is loaded into memory only once, and the
    ChromaDB connection is kept open — avoiding a cold-start on every query.
    """
    return get_rag_components()


# ── Guard: abort early if the ChromaDB store is missing ──────────────────────
if not os.path.exists("./chroma_db"):
    st.error(
        "⚠️ Vector store not found.  "
        "Please run `python ingest.py` first to build the knowledge base."
    )
    st.stop()

retriever, llm = load_components()


# ── Sidebar: evaluation questions ────────────────────────────────────────────
with st.sidebar:
    st.header("📋 Part C – Evaluation Queries")
    st.markdown(
        "Click any question to automatically test the bot "
        "against the ground-truth set from the assignment."
    )

    eval_questions = [
        "What is the specific request-per-second rate limit for the Upwork API, and is it enforced per Key or per IP?",
        "How long is an OAuth access token valid for?",
        "Can I use a Client Credentials Grant to access a user's private contract details?",
    ]

    for q in eval_questions:
        if st.button(q, use_container_width=True):
            # Directly process the question when button is clicked
            st.session_state["current_query"] = q
            st.rerun()

    st.divider()
    st.markdown(
        "**Model:** `meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo` via DeepInfra  \n"
        "**Embeddings:** `all-MiniLM-L6-v2` (local)  \n"
        "**Vector DB:** ChromaDB  \n"
        "**Top-K chunks:** 3"
    )


# ── Main query interface ──────────────────────────────────────────────────────
# Check if a question was auto-submitted from sidebar button
auto_query = st.session_state.pop("current_query", None)

with st.form("query_form", clear_on_submit=True):
    user_query = st.text_area(
        "Ask a question about the Upwork API:",
        value=auto_query or "",
        height=100,
        placeholder="e.g. How do I obtain an access token using the Authorization Code Grant?",
    )
    submit = st.form_submit_button("🔍 Ask", type="primary", use_container_width=True)

if (submit and user_query.strip()) or auto_query:
    query_to_process = user_query.strip() if submit else auto_query
    
    with st.spinner("Retrieving relevant documentation and generating answer…"):
        try:
            result = answer_query(query_to_process, retriever, llm)
        except Exception as exc:
            st.error(f"An error occurred while calling the LLM: {exc}")
            st.stop()

    # ── Answer ────────────────────────────────────────────────────────────────
    st.subheader("💬 Answer")
    st.markdown(result["answer"])

    # ── Latency metric ────────────────────────────────────────────────────────
    st.metric(
        label="⏱ Response latency",
        value=f"{result['latency']:.2f} s",
        help="Wall-clock time from query submission to receiving the full response.",
    )

    st.divider()

    # ── Sources ───────────────────────────────────────────────────────────────
    st.subheader("📄 Sources (retrieved chunks)")
    st.caption(
        "These are the exact documentation snippets the LLM used to "
        "construct its answer."
    )

    for i, src in enumerate(result["sources"], start=1):
        with st.expander(f"Chunk {i}  |  Page {src['page']}", expanded=(i == 1)):
            st.text(src["text"])


# ── Chat history (optional, stored in session state) ─────────────────────────
if "history" not in st.session_state:
    st.session_state["history"] = []

# Add to history if we processed a query
if ((submit and user_query.strip()) or auto_query) and "result" in dir():
    query_to_save = user_query.strip() if submit else auto_query
    st.session_state["history"].append(
        {"question": query_to_save, "answer": result["answer"]}
    )

if st.session_state.get("history"):
    with st.expander("🕓 Session history", expanded=False):
        for item in reversed(st.session_state["history"]):
            st.markdown(f"**Q:** {item['question']}")
            st.markdown(f"**A:** {item['answer']}")
            st.divider()
