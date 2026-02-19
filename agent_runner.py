import os
import importlib.util
from functools import lru_cache

from langchain_aws import ChatBedrock
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import ChatPromptTemplate


# ============================================================
# Tool Loader (IDENTICAL behavior to main.py)
# ============================================================
def load_tools():
    tools_dir = os.path.join(os.path.dirname(__file__), "tools")
    tools = []

    for filename in os.listdir(tools_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            spec = importlib.util.spec_from_file_location(
                filename[:-3],
                os.path.join(tools_dir, filename)
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for attr in module.__dict__.values():
                if (
                    hasattr(attr, "name")
                    and hasattr(attr, "description")
                    and callable(getattr(attr, "run", None))
                ):
                    tools.append(attr)

    return tools


# ============================================================
# Agent Factory (BUILT ONCE, REUSED)
# ============================================================
@lru_cache(maxsize=1)
def get_agent_executor() -> AgentExecutor:
    tools = load_tools()

    llm = ChatBedrock(
        model_id=os.getenv(
            "BEDROCK_MODEL_ID",
            "anthropic.claude-3-haiku-20240307-v1:0"
        ),
        region_name=os.getenv("AWS_REGION", "eu-west-1"),
        model_kwargs={
            "temperature": float(os.getenv("MODEL_TEMPERATURE", "0.0"))
        },
    )

    prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant for managing family documents. Use the available tools to answer questions.

⚠️ IMPORTANT TOOL SELECTION RULES:

1. USE search_documents_tool WHEN:
   - User asks for content, details, or information FROM a document
   - User wants to "show me", "tell me", "what is", "get details from", "extract from"

2. USE download_document_tool ONLY WHEN:
   - User explicitly asks to DOWNLOAD or GET A LINK
   - Input can be just filename="Sem-2.pdf"

3. NEVER use download_document_tool to retrieve document content.

🔍 SEARCH STRATEGY:
- Use ONE broad search for multi-document questions
- Increase top_k if multiple semesters/documents are requested

{tools}

Use the following format:

Question: the input question
Thought: reasoning
Action: tool name
Action Input: tool input
Observation: result
... repeat if needed ...
Final Answer: final answer (always mention filenames like Sem-1.pdf, Sem-2.pdf)

Begin!

Question: {input}
Thought:{agent_scratchpad}
""")

    agent = create_react_agent(llm, tools, prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=30,          # 🔥 SAME AS CLI
        early_stopping_method="generate",
    )


# ============================================================
# Public API used by REST / WhatsApp
# ============================================================
def run_agent(user_input: str) -> str:
    executor = get_agent_executor()
    response = executor.invoke({"input": user_input})
    return response.get("output", "")
