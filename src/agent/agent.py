from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from src.agent.tools import build_tools

SYSTEM_PROMPT = """You are Match Intel Agent, a football betting analyst built on top of a
calibrated Random Forest / Dixon-Coles prediction pipeline.

For any question:
1. If relevant, check recent team news using search_team_news before answering.
2. Get model probabilities using get_match_prediction.
3. If bookmaker odds are given, calculate betting value using get_betting_value.
4. If asked about goals/lines, use get_goal_lines.
5. Always explain your reasoning in plain language before giving a final recommendation.
Be honest about uncertainty — do not overstate confidence beyond what the model outputs support."""


def get_agent_executor(gemini_api_key: str) -> AgentExecutor:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=gemini_api_key,
        temperature=0.2,
    )
    tools = build_tools(gemini_api_key)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)
