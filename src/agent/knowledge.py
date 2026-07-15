"""
Lightweight RAG knowledge base for team news/context.
Expand team_notes over time — this is intentionally simple to start.
"""
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document

team_notes = [
    Document(page_content="Germany: key striker returned from injury this week, expected to start.", metadata={"team": "Germany"}),
    Document(page_content="Japan: lost their starting goalkeeper to a red card suspension for the next match.", metadata={"team": "Japan"}),
    Document(page_content="Austria: manager confirmed a defensive lineup change ahead of this fixture.", metadata={"team": "Austria"}),
    Document(page_content="Jordan: squad has traveled internationally in the last week, possible fatigue factor.", metadata={"team": "Jordan"}),
    Document(page_content="Curaçao: no major injury concerns reported this week.", metadata={"team": "Curaçao"}),
]

_vectorstore = None

def get_vectorstore(api_key: str):
    global _vectorstore
    if _vectorstore is None:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
        _vectorstore = Chroma.from_documents(team_notes, embeddings)
    return _vectorstore

def search_team_news(team: str, api_key: str) -> str:
    vs = get_vectorstore(api_key)
    results = vs.similarity_search(team, k=2)
    if not results:
        return f"No recent notes found for {team}."
    return "\n".join([r.page_content for r in results])
