"""
Enhanced RAG knowledge base that supports both hardcoded and LLM-generated context.
Handles general football/betting questions in addition to team-specific notes.
"""
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
from langchain_google_genai import ChatGoogleGenerativeAI
import json

# Hardcoded team notes - expanded for more teams
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

_vectorstore = None
_llm = None

def get_vectorstore(api_key: str):
    global _vectorstore
    if _vectorstore is None:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=api_key)
        _vectorstore = Chroma.from_documents(team_notes, embeddings)
    return _vectorstore

def get_llm(api_key: str):
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
    vs = get_vectorstore(api_key)
    results = vs.similarity_search(team, k=2)
    if not results:
        return f"No specific notes found for {team}. This team may not have recent updates in our knowledge base."
    return "\n".join([r.page_content for r in results])

def answer_general_question(question: str, api_key: str) -> str:
    """
    Use LLM to answer general football/betting questions based on the knowledge base.
    This bypasses the JSON parsing issue by directly generating natural language responses.
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

Provide a clear, concise answer focused on betting analysis and football insights. If the question relates to team matchups, consider factors like form, team strength, and historical performance."""
        
        # Get response from LLM
        response = llm.invoke(prompt)
        
        # Extract text from LangChain response object
        if hasattr(response, 'content'):
            return response.content
        return str(response)
    
    except Exception as e:
        return f"I encountered an error answering your question: {str(e)}. Please try rephrasing your question."
