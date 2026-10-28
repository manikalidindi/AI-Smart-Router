
import os
from typing import TypedDict, Literal

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from tavily import TavilyClient


# =========================================================
# 1. ENVIRONMENT AND CLIENTS
# =========================================================

load_dotenv()

tavily_key = os.getenv("TAVILY_API_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")

if not tavily_key:
    raise ValueError("TAVILY_API_KEY is missing from .env")

if not gemini_key:
    raise ValueError("GEMINI_API_KEY is missing from .env")

tavily = TavilyClient(api_key=tavily_key)

ollama = ChatOllama(
    model="llama3.2",
    temperature=0
)

gemini = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    google_api_key=gemini_key,
    temperature=0
)


# =========================================================
# 2. STATE
# =========================================================

Route = Literal[
    "simple_response",
    "coding_task",
    "factual_query"
]


class UserState(TypedDict):
    user_input: str
    route: Route
    answer: str


# =========================================================
# 3. HELPER: EXTRACT TEXT FROM MODEL RESPONSES
# =========================================================

def extract_text(content) -> str:
    """Convert common LangChain text content formats to a string."""

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []

        for item in content:
            if isinstance(item, str):
                parts.append(item)

            elif isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))

        return "\n".join(parts).strip()

    return str(content).strip()


# =========================================================
# 4. ROUTER
# =========================================================

def route_query(query: str) -> Route:
    prompt = f"""
You are a query classification system.

Choose exactly one category:

simple_response:
Greetings, casual conversation, and simple questions
that do not require programming or web research.

coding_task:
Programming, debugging, algorithms, code explanations,
and software engineering.

factual_query:
Current information, news, research, and factual questions
that benefit from web search.

User query:
{query}

Return exactly one label:
simple_response
coding_task
factual_query

Do not explain your decision.
"""

    response = gemini.invoke(prompt)
    label = extract_text(response.content).lower()

    # Handle occasional extra formatting or explanation.
    allowed_routes = {
        "simple_response",
        "coding_task",
        "factual_query"
    }

    if label not in allowed_routes:
        normalized = label.replace("`", "").replace("*", "")

        # Prefer an exact label found on its own line.
        candidates = [
            line.strip().lower()
            for line in normalized.splitlines()
        ]

        matching = [
            item for item in candidates
            if item in allowed_routes
        ]

        if matching:
            label = matching[0]
        else:
            print(f"Unexpected router output: {label!r}")
            return "simple_response"

    return label


# =========================================================
# 5. ROUTER NODE
# =========================================================

def router_node(state: UserState):
    route = route_query(state["user_input"])

    print(f"\n[Router] Selected route: {route}")

    return {
        "route": route
    }


# =========================================================
# 6. SIMPLE RESPONSE NODE - OLLAMA
# =========================================================

def simple_response(state: UserState):
    response = ollama.invoke(state["user_input"])
    answer = extract_text(response.content)

    return {
        "answer": answer
    }


# =========================================================
# 7. CODING NODE - GEMINI
# =========================================================

def coding_task(state: UserState):
    prompt = f"""
You are an expert programming assistant.

Answer the user's programming question clearly.

When appropriate:
1. Explain the concept.
2. Provide correct, readable Python code.
3. Analyze time and space complexity.
4. Explain important edge cases.

User query:
{state["user_input"]}
"""

    response = gemini.invoke(prompt)

    return {
        "answer": extract_text(response.content)
    }


# =========================================================
# 8. FACTUAL RESEARCH NODE - TAVILY + GEMINI
# =========================================================

def factual_query(state: UserState):
    query = state["user_input"]

    search_response = tavily.search(
        query=query,
        max_results=5
    )

    results = search_response.get("results", [])

    if not results:
        return {
            "answer": (
                "I could not find relevant web search results. "
                "Please try a more specific query."
            )
        }

    context_parts = []

    for result in results:
        context_parts.append(
            f"Title: {result.get('title', 'Untitled')}\n"
            f"URL: {result.get('url', '')}\n"
            f"Content: {result.get('content', '')[:700]}"
        )

    context = "\n\n".join(context_parts)

    prompt = f"""
You are a factual research assistant.

Answer the question using the supplied search results.

Rules:
- Do not invent facts unsupported by the evidence.
- If the evidence is insufficient, say so.
- Include relevant source URLs in your answer.
- Distinguish established facts from uncertainty.

Question:
{query}

Search results:
{context}
"""

    response = gemini.invoke(prompt)

    return {
        "answer": extract_text(response.content)
    }


# =========================================================
# 9. BUILD LANGGRAPH
# =========================================================

builder = StateGraph(UserState)

builder.add_node("router", router_node)
builder.add_node("simple_response", simple_response)
builder.add_node("coding_task", coding_task)
builder.add_node("factual_query", factual_query)

builder.add_edge(START, "router")

builder.add_conditional_edges(
    "router",
    lambda state: state["route"],
    {
        "simple_response": "simple_response",
        "coding_task": "coding_task",
        "factual_query": "factual_query"
    }
)

builder.add_edge("simple_response", END)
builder.add_edge("coding_task", END)
builder.add_edge("factual_query", END)

workflow = builder.compile()


# =========================================================
# 10. RUN THE WORKFLOW
# =========================================================

if __name__ == "__main__":
    initial_state = {
        "user_input": (
            "What is the latest AI news?"
        )
    }


