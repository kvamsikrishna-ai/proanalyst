# Technical Summary — Upwork API Support Bot

## Architecture Overview

A three-layer RAG pipeline: **Ingestion** (PDF → chunks → ChromaDB) →
**Retrieval** (query → top-3 chunks by cosine similarity) → **Generation**
(chunks + system prompt → Meta-Llama-3.1-8B via DeepInfra → answer).

---

## Difficulties Faced

- **Chunking code snippets correctly.** The Upwork API docs mix narrative prose
  with GraphQL query blocks. A naive fixed-size split often broke a code block
  mid-token (e.g., separating a `curl` flag from its value), giving the LLM
  incomplete context. Resolved by using `RecursiveCharacterTextSplitter` which
  respects paragraph/sentence boundaries before resorting to character splits,
  combined with the 50-character overlap so boundary-spanning snippets always
  appear in full in at least one chunk.

- **Preventing hallucination on out-of-scope questions.** Without an explicit
  guard, the LLM would confidently answer questions whose answers are not in
  the documentation. Addressed via a two-part strategy: (1) the system prompt
  contains a hard-rule instruction — "base your answer ONLY on the context
  snippets provided" — and (2) the user prompt explicitly labels the retrieved
  text as the exclusive knowledge source, making deviation syntactically
  inconsistent with the instruction.

- **LLM API latency.** The DeepInfra endpoint round-trip for a 1 k-token prompt
  can be 4–10 seconds depending on model load.  The Streamlit spinner provides
  immediate user feedback; wall-clock latency is measured with `time.time()`
  and displayed as a `st.metric` so developers can see the true cost of each
  call.

- **Environment isolation for the embedding model.** `sentence-transformers`
  downloads ~90 MB of model weights on first use.  In a CI or cold-deploy
  scenario this adds significant setup time. The model is loaded once and
  cached with `st.cache_resource`, keeping subsequent query latency low.

- **Matching ingestion and query embeddings.** ChromaDB stores raw vectors
  without metadata about how they were normalised. Using
  `normalize_embeddings=True` in both `ingest.py` and `rag.py` ensures query
  vectors and stored vectors live in the same unit-sphere space, making cosine
  similarity scores reliable.

---

## How LLMs Were Used in Development

- **Claude (claude.ai)** was used as a pair-programmer to draft the LangChain
  integration code, verify that `ChatOpenAI`'s `openai_api_base` parameter
  correctly redirects requests to DeepInfra, and review the system prompt for
  ambiguous phrasing that could allow the model to bypass the hallucination
  guard.

- GPT-4 was consulted to cross-check the ChromaDB persistence API
  (specifically whether `persist_directory` in `Chroma.from_documents` is
  sufficient or whether an explicit `.persist()` call is still required in
  newer versions of `langchain-community`).

*Every line of the final code was written, reviewed, and understood by me
before submission. LLM suggestions that I could not explain were discarded.*

---

## Three Reasons I Am the Best Fit for the ProAnalyst AI Team

1. **End-to-end RAG ownership.** I designed and implemented every layer of this
   pipeline independently — data ingestion, chunking strategy, local embeddings,
   vector retrieval, prompt engineering, and the Streamlit UI — which maps
   directly to the breadth expected of an Associate AI Developer working across
   the full stack.

2. **Security-first mindset.** I immediately identified that hardcoding API keys
   is a disqualifying risk and structured the codebase around `python-dotenv`
   and environment variables from the start, not as an afterthought. This
   discipline matters in a product that handles client credentials.

3. **Explainability as a first principle.** Every function in this submission has
   a docstring explaining *why* it works the way it does (e.g. why overlap
   prevents context loss, why `normalize_embeddings=True` is required in both
   steps). On the ProAnalyst team, being able to articulate design decisions to
   stakeholders and colleagues is as important as writing the code itself.
