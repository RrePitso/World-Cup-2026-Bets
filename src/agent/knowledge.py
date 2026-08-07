"""
Enhanced RAG knowledge base with robust Chroma init + recovery.
Handles general football/betting questions in addition to team-specific notes.
"""
import os
import logging
import sqlite3
from typing import Optional

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOGLEVEL", "INFO"))

# Hardcoded team notes
team_notes = [
    Document(page_content="Germany: key striker returned from injury this week, expected to start.", metadata={"team": "Germany", "type": "team_news"}),
    Document(page_content="Japan: lost their starting goalkeeper to a red card suspension for the next match.", metadata={"team": "Japan", "type": "team_news"}),
    Document(page_content="Austria: manager confirmed a defensive lineup change ahead of this fixture.", metadata={"team": "Austria", "type": "team_news"}),
    Document(page_content="Jordan: squad has traveled internationally in the last week, possible fatigue factor.", metadata={"team": "Jordan", "type": "team_news"}),
    Document(page_content="Curaçao: no major injury concerns reported this week.", metadata={"team": "Curaçao", "type": "team_news"}),
    Document(page_content="England: historically strong in tournaments, experienced squad with world-class players.", metadata={"team": "England", "type": "team_news"}),
    Document(page_content="Argentina: defending champions, strong attacking options led by experienced forwards.", metadata={"team": "Argentina", "type": "team_news"}),
    Document(page_content="France: strong midfielder depth, solid defensive record in tournaments.", metadata={"team": "France", "type": "team_news"}),
    Document(page_content="Brazil: traditionally strong attacking side, multiple offensive options.", metadata={"team": "Brazil", "type": "team_news"}),
    Document(page_content="Spain: possession-based tiki-taka style, strong midfield control.", metadata={"team": "Spain", "type": "team_news"}),
    # General betting knowledge
    Document(page_content="Expected Value (EV) is calculated as: EV = (Probability × Decimal Odds) - 1. Positive EV indicates a value bet.", metadata={"type": "betting_concept"}),
    Document(page_content="Kelly Criterion helps determine optimal bet sizing: Stake = (Edge / Odds) where Edge is probability advantage.", metadata={"type": "betting_concept"}),
    Document(page_content="In football, home field advantage typically adds 0.3-0.5 expected goals to the home team.", metadata={"type": "football_insight"}),
    Document(page_content="Bookmaker odds are typically implied probabilities that already incorporate a margin (vig). Finding +EV means beating that margin.", metadata={"type": "betting_concept"}),
    Document(page_content="Form and Elo ratings are key predictors of match outcomes, capturing recent performance and historical strength.", metadata={"type": "football_insight"}),
    Document(page_content="Weather conditions affect playing style - rain reduces goal frequency, wind affects passing accuracy.", metadata={"type": "football_insight"}),
    Document(page_content="Team injuries to key players (strikers, midfielders) typically reduce expected goals by 10-15%.", metadata={"type": "football_insight"}),
]

_vectorstore: Optional[Chroma] = None
_llm = None


def _safe_remove_sqlite(persist_dir: str):
    """Remove likely chroma sqlite files inside persist_dir."""
    candidates = ["chromadb.db", "chroma.db", "chroma.sqlite", "chroma.sqlite3"]
    removed = []
    for name in candidates:
        fp = os.path.join(persist_dir, name)
        if os.path.exists(fp):
            try:
                os.remove(fp)
                removed.append(fp)
                logger.warning("Removed corrupted Chroma sqlite file: %s", fp)
            except Exception as e:
                logger.exception("Failed to remove %s: %s", fp, e)
    return removed


def get_vectorstore(api_key: str):
    """
    Initialize or return cached Chroma vectorstore.

    Behavior:
    - Uses CHROMA_PERSIST_DIR env var (default ./chroma_db).
    - Attempts to load existing persistent store.
    - On sqlite schema errors (e.g., 'no such table'), removes sqlite artifacts and rebuilds from team_notes.
    - If rebuild fails, falls back to an in-memory store to keep the app responsive.
    """
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    persist_dir = os.environ.get("CHROMA_PERSIST_DIR", "./chroma_db")
    os.makedirs(persist_dir, exist_ok=True)

    # Create embeddings (may raise if API key invalid)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=api_key)

    # Try to load existing persistent Chroma first (preferred)
    try:
        logger.info("Attempting to load Chroma from persist_directory=%s", persist_dir)
        # This constructor attempts to open the persisted DB/collections.
        _vectorstore = Chroma(persist_directory=persist_dir, embedding_function=embeddings)
        logger.info("Loaded existing Chroma vectorstore from %s", persist_dir)
        return _vectorstore
    except Exception as e_load:
        msg = str(e_load).lower()
        logger.warning("Loading persisted Chroma failed: %s", e_load)

        # If it's a sqlite/schema issue, attempt removal and rebuild
        if "no such table" in msg or isinstance(e_load, (sqlite3.DatabaseError, sqlite3.OperationalError)):
            logger.warning("Detected sqlite schema issue; attempting to remove DB files and rebuild.")
            _safe_remove_sqlite(persist_dir)
            try:
                logger.info("Rebuilding Chroma collections from team_notes into %s", persist_dir)
                _vectorstore = Chroma.from_documents(team_notes, embeddings, persist_directory=persist_dir)
                logger.info("Successfully rebuilt Chroma vectorstore at %s", persist_dir)
                return _vectorstore
            except Exception as e_rebuild:
                logger.exception("Rebuild attempt failed: %s", e_rebuild)
                # Fall through to general fallback below

        # If loading failed for another reason or rebuild didn't work, try to create/from_documents anyway.
        try:
            logger.info("Attempting to create/populate Chroma at %s using from_documents()", persist_dir)
            _vectorstore = Chroma.from_documents(team_notes, embeddings, persist_directory=persist_dir)
            logger.info("Chroma created/populated at %s", persist_dir)
            return _vectorstore
        except Exception as e_create:
            logger.exception("Persistent Chroma creation failed: %s", e_create)
            # Final fallback: in-memory vectorstore (no persistence)
            try:
                logger.warning("Falling back to in-memory Chroma (no persistence).")
                _vectorstore = Chroma.from_documents(team_notes, embeddings, persist_directory=None)
                return _vectorstore
            except Exception as e_mem:
                logger.exception("In-memory Chroma fallback failed: %s", e_mem)
                # Re-raise the original error to make failure visible
                raise e_load


def get_llm(api_key: str):
    """Return a cached ChatGoogleGenerativeAI LLM instance."""
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model="gemini-flash-latest",
            google_api_key=api_key,
            temperature=0.3,
        )
    return _llm


def search_team_news(team: str, api_key: str) -> str:
    """Search team-specific news from the knowledge base."""
    try:
        vs = get_vectorstore(api_key)
        results = vs.similarity_search(team, k=2)
        if not results:
            return f"No specific notes found for {team}. This team may not have recent updates in our knowledge base."
        return "\n".join([r.page_content for r in results])
    except Exception as e:
        logger.exception("search_team_news failed: %s", e)
        return f"Could not search team news due to an error: {str(e)}"


def answer_general_question(question: str, api_key: str) -> str:
    """
    Use LLM to answer general football/betting questions based on the knowledge base.
    """
    try:
        vs = get_vectorstore(api_key)
        llm = get_llm(api_key)

        # Retrieve relevant context from knowledge base
        relevant_docs = vs.similarity_search(question, k=4)
        context = "\n".join([doc.page_content for doc in relevant_docs])

        # Build the prompt
        prompt = f"""You are an expert football betting analyst. Answer the following question based on your knowledge and the context provided.

Context from knowledge base:
{context}

Question: {question}

Provide a clear, concise answer focused on betting analysis and football insights. If the question relates to team matchups, consider factors like form, team strength, and historical performance.
"""

        # Get response from LLM
        response = llm.invoke(prompt)

        # Extract text from LangChain response object
        if hasattr(response, "content"):
            return response.content
        return str(response)
    except Exception as e:
        logger.exception("answer_general_question failed: %s", e)
        return f"I encountered an error answering your question: {str(e)}. Please try rephrasing your question."
