
import os
import re
from typing import TypedDict

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI


def get_secret(name, default=None):
    value = os.getenv(name)

    if value:
        return value

    try:
        import streamlit as st
        return st.secrets.get(name, default)
    except Exception:
        return default


load_dotenv(override=True)

# ---------- Research State ----------


class ResearchState(TypedDict, total=False):
    topic: str
    depth: str
    focus: str
    plan: str
    queries: list[str]
    sources: list[dict]
    report: str



# ---------- Groq-Gemini ----------


def get_llm():
    from langchain_groq import ChatGroq

    return ChatGroq(
        model="openai/gpt-oss-20b",
        api_key=get_secret("GROQ_API_KEY"),
        temperature=0.2,
        max_tokens=600,
        max_retries=1,
    )

def invoke_llm(prompt):
    try:
        print("⚡ Using Groq...")
        return get_llm().invoke(prompt)

    except Exception as groq_error:
        print("Groq failed:", groq_error)
        print("🔄 Switching to Gemini...")

        from langchain_google_genai import ChatGoogleGenerativeAI

        gemini = ChatGoogleGenerativeAI(
            model=get_secret("MODEL_NAME", "gemini-3.8-flash"),
            google_api_key=get_secret("GOOGLE_API_KEY"),
            timeout=30,
            max_retries=0,
            max_output_tokens=600,
        )

        return gemini.invoke(prompt)



# ---------- Planner Agent ----------

def planner_agent(state: ResearchState):
    prompt = f"""
Create a concise research plan.

Topic: {state["topic"]}
Depth: {state.get("depth", "Quick exploration")}
Focus: {state.get("focus", "General overview")}

Return:
1. Research objective (one sentence)
2. Three research questions
3. Exactly three web search queries, each on its own line
   and starting with QUERY:
4. Two limitations to consider

Keep the response under 250 words.
"""

    response = invoke_llm(prompt)
    content = response.content

    if isinstance(content, list):
        content = "\n".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        )

    # Extract search queries from the planner's response
    queries = re.findall(
        r"QUERY:\s*(.+)",
        content,
        flags=re.IGNORECASE
    )

    # Fallback if Gemini doesn't follow the format
    if not queries:
        topic = state["topic"]
        queries = [
            topic,
            f"{topic} latest research",
            f"{topic} challenges and applications",
        ]

    return {
        "plan": content,
        "queries": queries[:3]
    }


# ---------- Researcher Agent ----------




def researcher_agent(state: ResearchState):
    from tavily import TavilyClient

    client = TavilyClient(
        api_key=get_secret("TAVILY_API_KEY")
    )

    queries = state.get("queries", [])
    sources = []
    seen_urls = set()

    for query in queries:
        print(f"\n🔎 Tavily searching: {query}")

        try:
            response = client.search(
                query=query,
                search_depth="basic",
                max_results=3
            )

            results = response.get("results", [])

            print(f"✅ Found {len(results)} results")

            for result in results:
                url = result.get("url", "")

                if not url or url in seen_urls:
                    continue

                seen_urls.add(url)

                sources.append({
                    "title": result.get("title", "Untitled"),
                    "url": url,
                    "snippet": result.get("content", ""),
                    "query": query,
                    "score": result.get("score", 0)
                })

        except Exception as e:
            print(f"❌ Tavily search failed: {repr(e)}")

    print(f"\n📚 Total sources collected: {len(sources)}")

    return {"sources": sources}


#---------------------------------- writer-agent------------------------------------------------------



def writer_agent(state: ResearchState):
    sources = state.get("sources", [])

    if not sources:
        return {
            "report": "## Research Report\n\nNo sources were collected."
        }

    evidence = []

    for i, source in enumerate(sources, 1):
        evidence.append(
            f"[{i}] {source.get('title', 'Untitled')}\n"
            f"URL: {source.get('url', '')}\n"
            f"Evidence: {source.get('snippet', '')[:1000]}"
        )

    prompt = f"""
You are an evidence-based research report writer.

Topic: {state.get("topic", "")}
Focus: {state.get("focus", "General overview")}

Research plan:
{state.get("plan", "")}

Evidence:
{chr(10).join(evidence)}

Write a professional research report in Markdown with:
- Executive Summary
- Key Findings
- Detailed Analysis
- Limitations
- Conclusion
- References

Rules:
- Base factual claims only on supplied evidence.
- Cite claims using [1], [2], etc.
- References must match the supplied source numbers.
- Never invent sources.
- Mention evidence gaps honestly.
- Avoid repetition.
"""

    try:
        print("\n✍️ Writer Agent is generating the report...")

        response = invoke_llm(prompt)
        content = response.content

        # Handle different response content formats
        if isinstance(content, list):
            parts = []

            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    parts.append(item.get("text", ""))

            content = "\n".join(parts)

        content = str(content).strip()

        print(f"📝 Writer output length: {len(content)} characters")

        if not content:
            content = (
                "## Report generation failed\n\n"
                "The model returned an empty response. Please retry."
            )

        return {"report": content}

    except Exception as e:
        print(f"❌ Writer failed: {repr(e)}")

        return {
            "report": f"## Writer Error\n\n{str(e)}"
        }



# ---------- LangGraph Workflow ----------


def build_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("planner", planner_agent)
    graph.add_node("researcher", researcher_agent)
    graph.add_node("writer", writer_agent)

    graph.set_entry_point("planner")

    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "writer")
    graph.add_edge("writer", END)

    return graph.compile()



# ---------- Run Research ----------

def run_research(
    topic,
    depth="Quick exploration",
    focus="General overview"
):
    app = build_graph()

    result = app.invoke({
        "topic": topic,
        "depth": depth,
        "focus": focus
    })

    print("\n========== WRITER DEBUG ==========")
    print("Report exists:", bool(result.get("report")))
    print("Report length:", len(result.get("report", "")))
    print("================================\n")

    return result

