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

#     prompt = ChatPromptTemplate.from_template("""
# You are a helpful assistant for managing family documents. Use the available tools to answer questions.

# ⚠️ IMPORTANT TOOL SELECTION RULES:

# 1. USE search_documents_tool WHEN:
#    - User asks for content, details, or information FROM a document
#    - User wants to "show me", "tell me", "what is", "get details from", "extract from"
#    - Example: "Give me all details from Sem-2.pdf" → USE search_documents_tool
#    - Example: "What's in the medical report?" → USE search_documents_tool

# 2. USE download_document_tool ONLY WHEN:
#    - User explicitly asks to DOWNLOAD or GET A LINK
#    - User wants to save/download the actual file
#    - Example: "Download Sem-2.pdf" → USE download_document_tool
#    - Example: "Give me download link" → USE download_document_tool
#    - Input can be just 'filename="Sem-2.pdf"' - tool will look up document_id automatically

# 3. NEVER use download_document_tool to retrieve content or details from documents.
#    Always use search_documents_tool for content retrieval.

# 🔍 SEARCH STRATEGY FOR MULTIPLE ITEMS:
# When user asks for information from multiple documents or semesters:
# - DO ONE COMPREHENSIVE SEARCH with a broad query like "SGPA" or "academic records"
# - Set top_k higher (e.g., 10) to get all relevant documents
# - Extract specific information for all requested items in one pass
# - Example: "Give me Sem-1 and Sem-4 SGPA" → search "SGPA" with top_k=10, NOT separate searches
# IMPORTANT:
# - Always pass the FULL original user question to tools
# - Do NOT summarize or shorten tool inputs
# - Tool inputs MUST preserve user intent, constraints, and phrasing

# {tools}

# Use the following format:

# Question: the input question you must answer
# Thought: you should always think about what to do. First identify if user wants CONTENT (use search) or DOWNLOAD LINK (use download).
# Action: the action to take, should be one of [{tool_names}]
# Action Input: the input to the action
# Observation: the result of the action
# ... (this Thought/Action/Action Input/Observation can repeat N times)
# Thought: I now know the final answer
# Final Answer: the final answer to the original input question
# Alawys mention the file name in this manner Sem-1.pdf,Sem-2.pdf as an example, where you get the data.
# Begin!

# Question: {input}
# Thought:{agent_scratchpad}
# """)
    prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant for managing family documents.
Your primary responsibility is to identify the user's intent
and select the correct tool.

IMPORTANT INTENT RULES (STRICT):

1. CONTENT INTENT → use search_documents_tool
   Use this tool when the user wants to:
   - Read, understand, explain, summarize, or extract information
   - Ask questions like:
     * "What is in the document?"
     * "Give me details from Sem-1.pdf"
     * "Explain my prescription"
     * "Show SGPA from Sem-2"
   Filenames or document names are constraints only.
   The goal is always to retrieve and reason over DOCUMENT CONTENT.

2. DOWNLOAD INTENT → use download_document_tool
   Use this tool ONLY when the user explicitly wants:
   - A download link
   - The file itself
   - To save or download the document
   - To know the doucment name or document id or path of that file/document use  get_all_document_metadata_tool and then you can use download_document_tool
   Examples:
     * "Download Sem-2.pdf"
     * "Give me the download link"
     * "I want the file"
   NEVER use this tool to answer content-related questions.

3. DISCOVERY / LISTING INTENT → use get_all_document_metadata_tool
   Use this tool ONLY when the user asks:
   - What documents exist
   - To list or show all available document
   - To get or determine the document ID or document name use this tool. 
   This tool does NOT return document content.

GLOBAL RULES:
- Always pass the FULL original user question to the selected tool.
- Never summarize, shorten, or rephrase tool input.
- Do NOT combine tools unless explicitly required by the question.
- Trust tool logic for filtering, ranking, and constraints.

AVAILABLE TOOLS:
{tools}

You must follow this format:

Question: the original user question
Thought: identify the user's intent (CONTENT, DOWNLOAD, or DISCOVERY)
Action: the tool to use (one of [{tool_names}])
Action Input: the full user question
Observation: the tool result
Thought: I now know the final answer
Final Answer: the answer to the original question

Always mention filenames in the format: Sem-1.pdf, Sem-2.pdf
when referring to documents used.

Begin.

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
        early_stopping_method="generate"
        
    )


# ============================================================
# Public API used by REST / WhatsApp
# ============================================================
def run_agent(user_input: str) -> str:
    executor = get_agent_executor()
    response = executor.invoke({"input": user_input,"full_question": user_input})
    return response.get("output", "")
