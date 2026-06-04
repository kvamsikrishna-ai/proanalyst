"""
rag.py — Part B: RAG Implementation
=====================================
Provides two public helpers used by the Streamlit app:

  get_rag_components()  – loads ChromaDB + initialises the LLM (cached)
  answer_query()        – retrieves top-3 chunks, calls the LLM, returns
                          the answer, the source snippets, and the latency
"""

import os
import time
from typing import Any

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# ── Constants ────────────────────────────────────────────────────────────────
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHROMA_DIR = "./chroma_db"
TOP_K = 3    # B1: number of chunks to retrieve per query

# DeepInfra exposes an OpenAI-compatible endpoint, so we can reuse
# LangChain's ChatOpenAI simply by overriding the base URL.
DEEPINFRA_BASE_URL = "https://api.deepinfra.com/v1/openai"
LLM_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"

# B2 – System Prompt: forces in-character responses and the hallucination guard
SYSTEM_PROMPT = """\

IMPORTANT FOR LIST QUESTIONS:

If the question asks for:
- types
- categories
- methods
- grant types
- authentication flows
- endpoints
- permissions
- supported features

You MUST scan the entire context and extract ALL matching items before answering.

Do not return only the first matching item.

If multiple values exist in different parts of the context, combine them into one complete answer.

Example:
Question: What OAuth grant types are supported?

Correct Answer:
Authorization Code, Implicit, Client Credentials, Refresh Token

Incorrect Answer:
Implicit Grant
"""


# ── Component loaders ─────────────────────────────────────────────────────────

def get_retriever(chroma_dir: str = CHROMA_DIR):
    """
    B1 – Semantic Retrieval:
    Re-use the same local embedding model that was used during ingestion so
    that query vectors live in the same semantic space as the stored chunk
    vectors.  We ask ChromaDB to return the top-3 nearest neighbours by
    cosine similarity.
    """
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    vectorstore = Chroma(
        persist_directory=chroma_dir,
        embedding_function=embeddings,
    )
    # search_type="similarity" uses cosine distance on normalised embeddings
    retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})
    return retriever


def get_llm() -> ChatOpenAI:
    """
    B2 – API Integration:
    Reads DEEPINFRA_API_KEY from the environment (never hardcoded).
    ChatOpenAI is initialised with a custom base_url so every request is
    routed to DeepInfra instead of OpenAI, while keeping the same SDK.
    temperature=0.1 makes the model deterministic and factual — appropriate
    for a technical Q&A bot.
    """
    api_key = os.getenv("DEEPINFRA_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "DEEPINFRA_API_KEY is not set. "
            "Copy .env.example to .env and add your key."
        )

    llm = ChatOpenAI(
        model=LLM_MODEL,
        openai_api_key=api_key,
        openai_api_base=DEEPINFRA_BASE_URL,
        max_tokens=1024,
        temperature=0.1,
    )
    return llm


def get_rag_components(chroma_dir: str = CHROMA_DIR):
    """
    Convenience wrapper that returns (retriever, llm) as a tuple.
    Streamlit will call this once and cache the result with st.cache_resource
    so the embedding model and ChromaDB connection are not reloaded on every
    user interaction.
    """
    retriever = get_retriever(chroma_dir)
    llm = get_llm()
    return retriever, llm


# ── Core RAG function ─────────────────────────────────────────────────────────

def answer_query(query: str, retriever: Any, llm: ChatOpenAI) -> dict:
    """
    B1 + B2 – Full RAG loop:

    1. Embed the user query and retrieve TOP_K relevant chunks.
    2. Concatenate the chunks into a single context block.
    3. Build a [SystemMessage, HumanMessage] conversation:
       - SystemMessage carries the persona + hallucination guard rule.
       - HumanMessage carries the context + the user's question.
    4. Call the LLM and measure wall-clock latency.
    5. Return a dict with the answer, the raw source snippets, and latency.
    """
    start_time = time.time()

    # Step 1 – Retrieve
    relevant_docs = retriever.invoke(query)

    # Step 2 – Build context string
    context_blocks = []
    for i, doc in enumerate(relevant_docs, start=1):
        source_label = f"[Chunk {i} | Page {doc.metadata.get('page', '?')}]"
        context_blocks.append(f"{source_label}\n{doc.page_content}")
    context = "\n\n".join(context_blocks)

    # Step 3 – Build prompt
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"""
    Documentation Context:

    {context}

    Question:
    {query}

    Instructions:
    1. Read ALL provided context before answering.
    2. If the question asks for types, methods, grant types, endpoints, permissions, features, limits, or categories, extract ALL relevant items from the context.
    3. Do not stop after finding the first match.
    4. Combine information from multiple sections when necessary.
    5. If the answer is not present in the context, respond exactly:
    "I'm sorry, but the provided documentation does not contain that information."

    Answer:
    """
        ),
    ]

    # Step 4 – Call the LLM
    response = llm.invoke(messages)
    latency = time.time() - start_time

    # Step 5 – Return structured result
    return {
        "answer": response.content,
        "sources": [
            {
                "answer": doc.page_content,
                "latency": latency,
            }
            for doc in relevant_docs
        ],
        "latency": latency,
    }