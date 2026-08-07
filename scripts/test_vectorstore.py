"""
Small test script to validate Chroma initialization and similarity search.
Usage:
    CHROMA_PERSIST_DIR=./chroma_db GEMINI_API_KEY=<your_key> python scripts/test_vectorstore.py
"""
import os
from src.agent.knowledge import get_vectorstore

def main():
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "<replace_with_key>"
    persist = os.environ.get("CHROMA_PERSIST_DIR", "./chroma_db")
    print("Persist dir:", persist)
    vs = get_vectorstore(api_key)
    print("Vectorstore type:", type(vs))
    res = vs.similarity_search("Germany", k=2)
    print("Search results count:", len(res))
    for i, d in enumerate(res):
        print(f"--- Result {i+1} ---")
        print(d.page_content)
        print(d.metadata)

if __name__ == "__main__":
    main()
