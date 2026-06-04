# ProAnalyst – Upwork API Technical Support Bot
🔧 Upwork API Support Bot
A RAG-powered Technical Support AI that answers developer questions about
the Upwork API — built as part of the Associate AI Developer take-home assignment
for the ProAnalyst AI team.

📌 What It Does
Developers often struggle to find quick, accurate answers inside large API
reference documents. This bot solves that by:

Reading the official Upwork API documentation PDF
Breaking it into searchable vector chunks stored locally
Retrieving only the most relevant sections for each question
Generating a grounded, hallucination-resistant answer via a hosted LLM


🧠 How It Works (RAG Pipeline)
PDF Document
     │
     ▼
 [ingest.py]
 Load → Chunk (500 chars / 50 overlap) → Embed (MiniLM) → Store (ChromaDB)
     │
     ▼
 [rag.py]
 User Query → Embed → Top-3 Similarity Search → Build Prompt → LLM Call
     │
     ▼
 [app.py]
 Streamlit UI → Show Answer + Sources + Latency

🛠️ Tech Stack
LayerTechnologyLanguagePython 3.10+LLMMeta-Llama-3.1-8B-Instruct-Turbo (via DeepInfra)FrameworkLangChainEmbeddingssentence-transformers/all-MiniLM-L6-v2 (local)Vector DatabaseChromaDB (persisted on disk)UIStreamlitSecretspython-dotenv

📁 Project Structure
upwork-api-bot/
├── app.py                  # Streamlit UI
├── ingest.py               # PDF loading, chunking, embedding, ChromaDB storage
├── rag.py                  # Retriever, LLM client, answer_query()
├── requirements.txt        # All dependencies
├── .env.example            # Environment variable template (safe to commit)
├── .env                    # Your actual secrets (DO NOT commit)
├── technical_summary.txt   # Assignment write-up
└── chroma_db/              # Auto-generated vector store (DO NOT commit)

🚀 Getting Started
1. Clone the repo
bashgit clone https://github.com/YOUR_USERNAME/upwork-api-bot.git
cd upwork-api-bot
2. Install dependencies
bashpip install -r requirements.txt
3. Set up your API key
bashcp .env.example .env
# Open .env and set:  DEEPINFRA_API_KEY=your_key_here
4. Build the vector store (run once)
bashpython ingest.py --pdf API_Documentation_Partial.pdf
5. Launch the app
bashstreamlit run app.py

💬 Example Questions

"How long is an OAuth access token valid for?"
"How do I obtain an authorization code using the Authorization Code Grant?"
"Can I use a Client Credentials Grant to access a user's private contract details?"
"What HTTP status code does GraphQL return on a validation error?"

🛡️ Hallucination Guard

The assistant is restricted to answering only from retrieved documentation.
If relevant information cannot be found, it responds with:
"I'm sorry, but the provided documentation does not contain that information."
🔐 Security

API keys are never hardcoded — loaded from .env at runtime
.env and chroma_db/ are excluded via .gitignore
Embeddings run locally — no document content is sent to external servers


👤 Author
Vamsi Krishna K
📧 krish13vamsi@gmail.com
🔗 GitHub

📄 License
This project was built as a private take-home assignment and is not licensed for
public distribution.
