"""
Streamlit page for the Match Intel Agent - interactive chat interface for betting analysis.
"""
import streamlit as st
import os
from datetime import datetime
from src.agent.agent import get_agent_executor
from src.agent.knowledge import answer_general_question

# Page configuration
st.set_page_config(
    page_title="Match Intel Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⚽ Match Intel Agent")
st.markdown("""
Ask natural-language questions about World Cup 2026 matches, betting odds, and team insights.
The agent reasons over predictions, odds, and team news to give you actionable betting analysis.
""")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent_initialized" not in st.session_state:
    st.session_state.agent_initialized = False

if "agent_executor" not in st.session_state:
    st.session_state.agent_executor = None

if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = None

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    gemini_api_key = st.text_input(
        "Enter your Google Gemini API Key",
        type="password",
        value=st.session_state.gemini_api_key or "",
        help="Required for the agent to work. Get it from https://makersuite.google.com/app/apikey"
    )
    
    if gemini_api_key:
        st.session_state.gemini_api_key = gemini_api_key
    
    if gemini_api_key and not st.session_state.agent_initialized:
        with st.spinner("Initializing agent..."):
            try:
                st.session_state.agent_executor = get_agent_executor(gemini_api_key)
                st.session_state.agent_initialized = True
                st.success("✅ Agent initialized successfully!")
            except Exception as e:
                st.error(f"❌ Failed to initialize agent: {str(e)}")
    
    st.markdown("---")
    
    # Example questions
    st.subheader("💡 Example Questions")
    example_questions = [
        "Should I trust England to beat Argentina?",
        "What's the betting value on Germany to beat Japan at 1.90 odds?",
        "Which team has the better form right now?",
        "Explain how Expected Value works in football betting",
        "What factors affect over/under goals predictions?",
    ]
    
    for i, example in enumerate(example_questions):
        if st.button(f"📌 {example}", key=f"example_{i}"):
            st.session_state.messages.append({"role": "user", "content": example})
            st.rerun()
    
    st.markdown("---")
    st.markdown("""
    ### How it works
    1. Ask any question about World Cup matches, teams, or betting
    2. The agent retrieves model predictions and odds data
    3. It searches team news and historical context
    4. Returns actionable betting insights with clear reasoning
    
    ### What it can do
    - 🔮 Predict match outcomes (1X2)
    - 💰 Calculate betting value and Kelly stake
    - ⚽ Estimate expected goals and goal lines
    - 📰 Fetch team news and injury updates
    - 📊 Explain betting concepts and analysis
    """)

# Main chat interface
st.subheader("💬 Conversation")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me about World Cup matches, odds, or betting..."):
    if not st.session_state.agent_initialized:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar to start chatting.")
    else:
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                try:
                    # Try to use the agent first
                    agent_response = st.session_state.agent_executor.invoke({
                        "input": prompt
                    })
                    
                    # Extract the response text
                    if isinstance(agent_response, dict):
                        response_text = agent_response.get("output", str(agent_response))
                    else:
                        response_text = str(agent_response)
                    
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    
                except Exception as e:
                    # Fallback to general question answering if agent fails
                    st.warning(f"Agent encountered an issue, trying knowledge base approach...")
                    try:
                        response_text = answer_general_question(prompt, gemini_api_key)
                        st.markdown(response_text)
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
                    except Exception as e2:
                        error_msg = f"❌ Error: {str(e2)}\n\nPlease try rephrasing your question or check your API key."
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    ⚠️ Disclaimer: This tool is for educational purposes. Betting carries risk. Do your own research.
</div>
""", unsafe_allow_html=True)
