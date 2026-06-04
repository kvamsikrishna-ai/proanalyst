"""
ingest.py — Part A: Knowledge Engineering
=========================================
Loads the Upwork API PDF, performs a sanity check, chunks the text,
generates local embeddings (sentence-transformers), and persists the
resulting vectors into a ChromaDB collection on disk.

Run this script ONCE before starting the Streamlit app:
    python ingest.py --pdf API_Documentation_Partial.pdf
"""

import argparse
import os
import sys

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# ── Constants ────────────────────────────────────────────────────────────────
CHUNK_SIZE = 500        # A2: required chunk size
CHUNK_OVERLAP = 50      # A2: required overlap
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"   # A3: local model
CHROMA_DIR = "./chroma_db"                                # A3: local storage


# ── Core functions ────────────────────────────────────────────────────────────

def load_pdf(pdf_path: str):
    """
    Load every page of the PDF as a LangChain Document object.
    PyPDFLoader splits on page boundaries and stores the page number
    in doc.metadata so we can surface it to the user as a source.
    """
    if not os.path.exists(pdf_path):
        sys.exit(f"[ERROR] File not found: {pdf_path}")

    loader = PyPDFLoader(pdf_path)
    documents = loader.load()   # returns List[Document]
    return documents


def sanity_check(documents: list) -> str:
    """
    A1 – Sanity Check:
    Concatenate all page text and report total character count + a preview.
    This confirms the file was read correctly before we invest time in
    chunking and embedding.
    """
    full_text = "\n".join(doc.page_content for doc in documents)
    total_chars = len(full_text)

    print("=" * 60)
    print("SANITY CHECK")
    print("=" * 60)
    print(f"  Pages loaded      : {len(documents)}")
    print(f"  Total characters  : {total_chars:,}")
    print(f"  Sample (first 300 chars):\n")
    print(full_text[:300])
    print("=" * 60)

    return full_text


def chunk_documents(documents: list) -> list:
    """
    A2 – Document Chunking:
    RecursiveCharacterTextSplitter tries to split on paragraph / sentence /
    word / character boundaries in that order, so chunks stay semantically
    coherent even at the target size.

    Why overlap matters for technical docs:
    A code snippet or OAuth step that spans a chunk boundary would be
    silently cut in two; if only one half is retrieved the LLM sees
    incomplete context and may hallucinate.  The 50-char overlap ensures
    every boundary region appears in *both* adjacent chunks, so whichever
    chunk is retrieved the LLM always gets the full snippet.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )
    chunks = splitter.split_documents(documents)
    print(f"[Chunking] {len(documents)} pages → {len(chunks)} chunks "
          f"(size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    return chunks


def build_vector_store(chunks: list, persist_dir: str = CHROMA_DIR):
    """
    A3 – Vector Storage:
    1. Load a local sentence-transformers model to embed each chunk.
       Running locally means no data leaves the machine (satisfies the
       'No Data Uploads' rule).
    2. Persist the collection to disk via ChromaDB so the Streamlit app
       can reload it without re-embedding on every restart.
    """
    print(f"[Embedding] Loading model: {EMBED_MODEL}")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={"device": "cpu"},   # force CPU for portability
        encode_kwargs={"normalize_embeddings": True},
    )

    print(f"[ChromaDB] Storing vectors in: {persist_dir}")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir,
    )

    count = vectorstore._collection.count()
    print(f"[ChromaDB] Collection ready — {count} vectors stored.")
    return vectorstore


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Ingest Upwork API PDF into ChromaDB")
    parser.add_argument(
        "--pdf",
        default="API_Documentation_Partial.pdf",
        help="Path to the Upwork API documentation PDF",
    )
    parser.add_argument(
        "--chroma-dir",
        default=CHROMA_DIR,
        help="Directory where ChromaDB persists its data",
    )
    args = parser.parse_args()

    documents = load_pdf(args.pdf)
    sanity_check(documents)
    chunks = chunk_documents(documents)
    build_vector_store(chunks, persist_dir=args.chroma_dir)
    print("\n✅  Ingestion complete. You can now run:  streamlit run app.py")


if __name__ == "__main__":
    main()
