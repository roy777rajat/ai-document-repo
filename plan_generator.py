# plan_generator.py

from typing import List
import re


from langsmith import traceable

from llm import call_claude_simple


PLAN_PROMPT = """
You are a planner for a document assistant.

Your task:
- Decide WHAT actions are required
- Decide the CORRECT ORDER
- Do NOT execute tools
- Do NOT explain

Allowed steps (USE ONLY THESE WORDS):
- search_documents
- download_document
- list_documents

Rules:
- Content questions → search_documents
- Download/link questions → download_document
- List/show documents → list_documents
- Multiple steps allowed
- Order matters
- search_documents MUST come before download_document

Respond with the steps in ANY format.
DO NOT explain.

Tool semantics (IMPORTANT):

search_documents:
- Use when the user wants to understand, analyze, compare,
  summarize, or extract information FROM documents.
- This tool reads document content.

download_document:
- Use ONLY when the user wants the FILE itself
  (download, link, keep a copy, save for later).
- This tool does NOT read content.
- This is about file ownership, not understanding.

list_documents:
- Use ONLY when the user is exploring what documents exist.
- Do NOT use if the user already refers to a specific document.
- Do NOT use together with download_document.

User question:
{question}
"""


# ------------------------------------------------------------
# 🔵 HARDENED STEP EXTRACTOR
# ------------------------------------------------------------
def _extract_steps(text: str, question: str) -> List[str]:
    text = text.lower()
    question_l = question.lower()

    # --------------------------------------------------
    # 1️⃣ Extract LLM-proposed steps (fuzzy)
    # --------------------------------------------------
    llm_steps = []
    if "search_documents" in text:
        llm_steps.append("search_documents")
    if "download_document" in text:
        llm_steps.append("download_document")
    if "list_documents" in text:
        llm_steps.append("list_documents")

    llm_steps = list(dict.fromkeys(llm_steps))  # dedupe, preserve order

    # --------------------------------------------------
    # 2️⃣ Intent classification (STRICT)
    # --------------------------------------------------
    discovery_phrases = [
        "show me all available documents",
        "show me all documents",
        "list all documents",
        "what documents do i have",
        "what all documents do you have",
        "available documents",
        "what files are available",
        "document list",
        "list of documents",
        "doc list",
        "list doc"
        "doc metadata",
        "metadata list"
    ]

    content_phrases = [
        "marks",
        "score",
        "sgpa",
        "transaction",
        "details",
        "latest",
        "extract",
        "from documents",
        "from my documents",
        "insurance",
        "less than",
        "min","minimum","max","maximum","all the details"
    ]

    download_phrases = [
        "download",
        "file",
        "send me",
        "also the file",
        "give me the file",
        "copy of",
        "pdf",
        "save",
        "future use",
        "link"
    ]

    is_discovery = any(p in question_l for p in discovery_phrases)
    is_content = any(p in question_l for p in content_phrases)
    is_download = any(p in question_l for p in download_phrases)

    # --------------------------------------------------
    # 🔴 RULE 1: PURE DISCOVERY WINS (ABSOLUTE)
    # --------------------------------------------------
    if is_discovery and not is_content and not is_download:
        return ["list_documents"]

    # --------------------------------------------------
    # 🔴 RULE 2: TRUST LLM FOR DISCOVERY IF NO CONTENT
    # --------------------------------------------------
    if (
        "list_documents" in llm_steps
        and "search_documents" not in llm_steps
        and not is_content
        and not is_download
    ):
        return ["list_documents"]

    # --------------------------------------------------
    # 3️⃣ Build steps deterministically
    # --------------------------------------------------
    steps = []

    if is_content:
        steps.append("search_documents")

    if is_download:
        if "search_documents" not in steps:
            steps.append("search_documents")
        steps.append("download_document")

    # --------------------------------------------------
    # 🔴 RULE 3: SAFE FALLBACK (ONLY IF NOTHING MATCHES)
    # --------------------------------------------------
    if not steps:
        return ["search_documents"]

    return steps


# ------------------------------------------------------------
# 🔵 PUBLIC API (PLANNER)
# ------------------------------------------------------------

@traceable(
    name="generate_plan",
    run_type="llm",
    tags=["planner"]
)
def generate_plan(question: str) -> List[str]:
    """
    Planner:
    - LLM decides WHAT steps to run
    - Output is normalized deterministically
    """

    response = call_claude_simple(
        PLAN_PROMPT.format(question=question)
    )

    print("RAW PLANNER OUTPUT:")
    print(response)

    steps = _extract_steps(response, question)

    if not steps:
        steps = ["search_documents"]

    return steps