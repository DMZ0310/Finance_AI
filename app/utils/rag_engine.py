"""
RAG (Retrieval-Augmented Generation) engine.
Uses ChromaDB for vector storage and Google Gemini for generation.
"""

import logging
import hashlib
from typing import Optional

import pandas as pd

from app.utils.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    CHROMA_PERSIST_DIR,
    CHROMA_COLLECTION,
)

logger = logging.getLogger(__name__)

# ─── Lazy imports (expensive; loaded on first use) ────────────────────────────

_chroma_client = None
_collection    = None
_embedder      = None
_llm           = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading SentenceTransformer model…")
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def _get_chroma():
    global _chroma_client, _collection
    if _collection is None:
        import chromadb
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        _collection = _chroma_client.get_or_create_collection(
            name=CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB collection ready (%d docs)", _collection.count())
    return _collection


def _get_llm():
    global _llm
    if _llm is None:
        if not GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to your .env file."
            )
        from langchain_google_genai import ChatGoogleGenerativeAI
        _llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GEMINI_API_KEY,
            temperature=0.4,
            convert_system_message_to_human=True,
        )
    return _llm


# ─── Indexing ─────────────────────────────────────────────────────────────────

def index_transactions(df: pd.DataFrame, summary_text: str) -> int:
    """
    Embed transaction documents and upsert into ChromaDB.
    Returns total count of indexed documents.
    """
    collection = _get_chroma()
    embedder   = _get_embedder()

    documents, ids, metadatas = [], [], []

    # 1) Individual expense sentences
    expenses = df[df["is_expense"]].copy()
    for _, row in expenses.iterrows():
        doc_text = (
            f"Transaction: {row['description']} | "
            f"Amount: ${abs(row['amount']):.2f} | "
            f"Category: {row['category']} | "
            f"Date: {row['date'].strftime('%Y-%m-%d')} | "
            f"Month: {row['month']}"
        )
        doc_id = hashlib.md5(doc_text.encode()).hexdigest()
        documents.append(doc_text)
        ids.append(doc_id)
        metadatas.append({
            "category": row["category"],
            "month"   : str(row["month"]),
            "amount"  : float(abs(row["amount"])),
            "type"    : "transaction",
        })

    # 2) Monthly summary chunks
    monthly = expenses.groupby("month")
    for month, group in monthly:
        cat_breakdown = group.groupby("category")["amount"].sum().abs()
        breakdown_str = " | ".join(
            f"{c}: ${v:.2f}" for c, v in cat_breakdown.items()
        )
        doc_text = (
            f"Monthly summary for {month}: "
            f"Total spent ${group['amount'].sum().__abs__():.2f}. "
            f"Breakdown — {breakdown_str}."
        )
        doc_id = hashlib.md5(doc_text.encode()).hexdigest()
        documents.append(doc_text)
        ids.append(doc_id)
        metadatas.append({"type": "monthly_summary", "month": str(month)})

    # 3) Overall summary
    overall_id = hashlib.md5(summary_text[:200].encode()).hexdigest()
    documents.append(summary_text[:2000])
    ids.append(overall_id)
    metadatas.append({"type": "overall_summary"})

    if not documents:
        logger.warning("No documents to index.")
        return 0

    # Batch embed
    embeddings = embedder.encode(documents, show_progress_bar=False).tolist()

    # Upsert in chunks of 100
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        collection.upsert(
            documents=documents[i : i + batch_size],
            embeddings=embeddings[i : i + batch_size],
            ids=ids[i : i + batch_size],
            metadatas=metadatas[i : i + batch_size],
        )

    total = collection.count()
    logger.info("Indexed %d documents. Collection total: %d", len(documents), total)
    return total


def clear_index():
    """Remove all documents from the ChromaDB collection."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        client.delete_collection(CHROMA_COLLECTION)
        global _collection
        _collection = None
        logger.info("ChromaDB collection cleared.")
    except Exception as e:
        logger.warning("Could not clear collection: %s", e)


# ─── Retrieval ────────────────────────────────────────────────────────────────

def retrieve(query: str, n_results: int = 8) -> list[str]:
    """Semantic search: return top-n relevant document strings."""
    collection = _get_chroma()
    if collection.count() == 0:
        return []

    embedder = _get_embedder()
    q_emb    = embedder.encode([query]).tolist()

    results = collection.query(
        query_embeddings=q_emb,
        n_results=min(n_results, collection.count()),
    )
    docs = results.get("documents", [[]])[0]
    logger.debug("Retrieved %d docs for query: '%s'", len(docs), query[:60])
    return docs


# ─── Generation ───────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are FinanceAI, an expert personal finance assistant.
You analyse bank statement data and provide clear, actionable financial advice.

Rules:
- Be concise but thorough. Use bullet points and numbers where helpful.
- Always ground your answers in the provided financial context.
- If data is insufficient, say so clearly and ask for more.
- Provide specific, actionable budgeting recommendations.
- When identifying problems, offer constructive solutions.
- Format currency as $X,XXX.XX and use month names.
- Be empathetic — money is personal.
"""


def answer_question(
    question: str,
    kpis: Optional[dict] = None,
    chat_history: Optional[list] = None,
) -> str:
    """
    Full RAG pipeline: retrieve relevant docs → build prompt → generate answer.

    Args:
        question:     User's natural-language question.
        kpis:         Precomputed KPI dict (optional enrichment).
        chat_history: List of {"role": "user"|"assistant", "content": str}.

    Returns:
        The assistant's response string.
    """
    # 1. Retrieve context
    context_docs = retrieve(question)
    context_str  = "\n".join(f"- {d}" for d in context_docs) if context_docs else "No transaction data indexed yet."

    # 2. Build KPI context
    kpi_str = ""
    if kpis:
        kpi_str = f"""
Key Financial Summary:
- Total Expenses: ${kpis.get('total_expenses', 0):,.2f}
- Total Income: ${kpis.get('total_income', 0):,.2f}
- Net Savings: ${kpis.get('net_savings', 0):,.2f}
- Savings Rate: {kpis.get('savings_rate', 0):.1f}%
- Top Spending Category: {kpis.get('top_category', 'N/A')} (${kpis.get('top_category_amount', 0):,.2f})
- Largest Single Expense: ${kpis.get('largest_expense', 0):,.2f}
- Average Transaction: ${kpis.get('avg_transaction', 0):,.2f}
"""

    # 3. Build full prompt
    prompt = f"""{SYSTEM_PROMPT}

{kpi_str}

Relevant transaction context:
{context_str}

User question: {question}

Please provide a helpful, specific answer based on the financial data above."""

    # 4. Include chat history for conversational memory
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    if chat_history:
        for msg in chat_history[-6:]:  # last 3 turns
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

    # Final user message with full context
    messages.append(
        HumanMessage(
            content=f"""Financial Context:
{kpi_str}

Relevant transactions:
{context_str}

Question: {question}"""
        )
    )

    llm = _get_llm()
    response = llm.invoke(messages)
    return response.content


def generate_budget_recommendations(kpis: dict) -> str:
    """Generate AI-powered budgeting tips from KPI data."""
    cat_totals = kpis.get("category_totals", {})
    cat_str = "\n".join(
        f"  - {cat}: ${amt:,.2f}" for cat, amt in sorted(cat_totals.items(), key=lambda x: -x[1])
    )

    prompt = f"""You are a certified financial planner. Analyse this person's spending and provide:
1. Three specific areas to cut back
2. A realistic monthly savings goal
3. Three actionable money-saving tips tailored to their spending pattern
4. A simple 50/30/20 budget recommendation

Financial data:
- Total Monthly Expenses: ${kpis.get('total_expenses', 0) / max(len(kpis.get('monthly_totals', {1: 1})), 1):,.2f}
- Total Income: ${kpis.get('total_income', 0):,.2f}
- Current Savings Rate: {kpis.get('savings_rate', 0):.1f}%
- Spending by category:
{cat_str}

Be specific, warm, and practical. Format with clear headers."""

    llm = _get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content


def detect_anomalies_ai(df: pd.DataFrame, kpis: dict) -> str:
    """Use AI to identify and explain unusual spending patterns."""
    anomalies = kpis.get("anomalies", pd.DataFrame())
    if anomalies.empty:
        anom_str = "No statistical anomalies detected."
    else:
        rows = []
        for _, row in anomalies.iterrows():
            rows.append(
                f"  - {row['description']}: ${abs(row['amount']):.2f} on {row['date'].strftime('%b %d')}"
            )
        anom_str = "\n".join(rows)

    prompt = f"""Analyse these potentially unusual transactions from a bank statement and explain:
1. Which ones look genuinely suspicious or unusual
2. Which are likely one-time legitimate expenses
3. Any spending patterns worth flagging

Flagged transactions (>2 standard deviations from mean):
{anom_str}

Average transaction: ${kpis.get('avg_transaction', 0):.2f}

Be concise and helpful."""

    from langchain_core.messages import HumanMessage
    llm = _get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content
