from typing import List
from llm import call_claude_simple
import re


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
# 🔵 HARDENED STEP EXTRACTOR (INTENT-AWARE)
# ------------------------------------------------------------
def _extract_steps(text: str, question: str) -> List[str]:
    """
    Extract execution steps from ANY LLM output format
    and prune based on user intent.
    """

    text = text.lower()
    question_l = question.lower()

    candidates = []

    if "search_documents" in text:
        candidates.append("search_documents")

    if "download_document" in text:
        candidates.append("download_document")

    if "list_documents" in text:
        candidates.append("list_documents")

    # --------------------------------------------------
    # Deduplicate while preserving order
    # --------------------------------------------------
    seen = set()
    ordered = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            ordered.append(c)

    # --------------------------------------------------
    # PURE DISCOVERY
    # --------------------------------------------------
    if any(k in question_l for k in [
        "what documents",
        "show me all",
        "available documents",
        "what all documents",
    ]):
        return ["list_documents"]

    # --------------------------------------------------
    # Detect filename
    # --------------------------------------------------
    has_filename = bool(
        re.search(r"\b[\w\-]+\.(pdf|docx?|pptx?)\b", question_l)
    )

    # --------------------------------------------------
    # Detect analytical / comparative intent
    # --------------------------------------------------
    is_analytical = any(k in question_l for k in [
        "compare",
        "maximum",
        "highest",
        "best",
        "which semester",
        "where sgpa",
    ])

    # --------------------------------------------------
    # CONTENT-ONLY → remove download leakage
    # --------------------------------------------------
    if (
        "download" not in question_l
        and "link" not in question_l
        and "keep" not in question_l
        and "download_document" in ordered
        and not is_analytical
    ):
        ordered = [s for s in ordered if s != "download_document"]

    # --------------------------------------------------
    # Enforce ordering (search → download)
    # --------------------------------------------------
    if "download_document" in ordered and "search_documents" in ordered:
        ordered = ["search_documents", "download_document"]

    # --------------------------------------------------
    # 🔴 HARD RULE FOR THIS SYSTEM
    # Download is NEVER standalone
    # --------------------------------------------------
    if ordered == ["download_document"]:
        return ["search_documents", "download_document"]

    # --------------------------------------------------
    # Download without filename:
    # - analytical → KEEP search + download
    # - non-analytical → search first
    # --------------------------------------------------
    if "download_document" in ordered and not has_filename:
        return ["search_documents", "download_document"]

    return ordered


# ------------------------------------------------------------
# 🔵 PUBLIC API
# ------------------------------------------------------------
def generate_plan(question: str) -> List[str]:
    response = call_claude_simple(
        PLAN_PROMPT.format(question=question)
    )

    print("🧪 RAW PLANNER OUTPUT:")
    print(response)

    steps = _extract_steps(response, question)

    if not steps:
        # Ultra-safe fallback
        return ["search_documents"]

    return steps