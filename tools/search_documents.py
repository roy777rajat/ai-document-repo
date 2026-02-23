from langchain.tools import tool
from utils import search_documents
from llm import call_claude_simple

import re
import math
from typing import List, Dict, Tuple

# 🔵 LangCache helpers (clean separation)
from lang_cache_utils import langcache_store, langcache_lookup


# ============================================================
# TOKENIZATION
# ============================================================

def tokenize(text: str) -> List[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\. ]", " ", text)
    return [t for t in text.split() if len(t) > 2]


# ============================================================
# INEQUALITY EXTRACTION
# ============================================================

def extract_inequality(query: str) -> Tuple[str, float] | None:
    patterns = [
        (r"less than\s+(\d+\.?\d*)", "<"),
        (r"greater than\s+(\d+\.?\d*)", ">"),
        (r"below\s+(\d+\.?\d*)", "<"),
        (r"above\s+(\d+\.?\d*)", ">"),
        (r"<=\s*(\d+\.?\d*)", "<="),
        (r">=\s*(\d+\.?\d*)", ">="),
        (r"<\s*(\d+\.?\d*)", "<"),
        (r">\s*(\d+\.?\d*)", ">"),
    ]

    for pattern, op in patterns:
        m = re.search(pattern, query.lower())
        if m:
            print(f"\n📐 Inequality detected → {op} {m.group(1)}")
            return op, float(m.group(1))
    return None


def satisfies_inequality(text: str, op: str, value: float) -> bool:
    numbers = [float(n) for n in re.findall(r"\d+\.\d+|\d+", text)]
    return any(
        (op == "<" and n < value) or
        (op == ">" and n > value) or
        (op == "<=" and n <= value) or
        (op == ">=" and n >= value)
        for n in numbers
    )


# ============================================================
# DOCUMENT SELECTORS
# ============================================================

def extract_document_selectors(query: str) -> dict:
    q = query.lower()

    filenames = set(re.findall(r"\b[a-z0-9\-_]+\.pdf\b", q))
    numbers = set(map(int, re.findall(r"\d+", q)))

    print(f"\n🎯 Document selectors resolved:")
    print(f"   filenames → {filenames}")
    print(f"   numbers   → {numbers}")

    return {"filenames": filenames, "numbers": numbers}


def filename_matches(filename: str, selectors: dict) -> bool:
    fname = filename.lower()

    for f in selectors["filenames"]:
        if f in fname:
            return True

    if selectors["numbers"]:
        fname_nums = set(map(int, re.findall(r"\d+", fname)))
        return bool(fname_nums & selectors["numbers"])

    return True


# ============================================================
# SCORING
# ============================================================

def score_chunk(query: str, chunk: str) -> float:
    q_tokens = tokenize(query)
    c_tokens = tokenize(chunk)

    if not q_tokens or not c_tokens:
        return 0.0

    overlap = len(set(q_tokens) & set(c_tokens)) / len(q_tokens)
    token_density = sum(1 for t in c_tokens if t in q_tokens) / len(c_tokens)
    numeric_density = len(re.findall(r"\d+\.\d+|\d+", chunk)) / len(c_tokens)
    length_penalty = math.log(len(c_tokens) + 1)

    return (overlap * 3 + token_density * 8 + numeric_density * 5) / length_penalty


# ============================================================
# GROUPING & CONFIDENCE
# ============================================================

def group_documents(chunks: List[Dict]) -> Dict[str, Dict]:
    grouped = {}
    for c in chunks:
        f = c["filename"]
        grouped.setdefault(f, {"chunks": [], "score": 0.0})
        grouped[f]["chunks"].append(c["text"])
        grouped[f]["score"] += c["score"]
    return grouped


def compute_confidence(grouped: Dict[str, Dict]) -> Dict[str, float]:
    max_score = max(d["score"] for d in grouped.values())
    return {k: round(v["score"] / max_score, 3) for k, v in grouped.items()}


# ============================================================
# TOOL
# ============================================================

#  """
#     Semantic document search with filename filtering,
#     inequality enforcement, chunk re-ranking,
#     document grouping, and confidence scoring.
#     """

@tool
def search_documents_tool(input) -> str:
    """
    Interpret the user's intent and retrieve the correct document CONTENT,
    not just matching filenames or keywords.

    Functional behavior and intent handling:

    1. User Intent First (Not Filename Matching)
       - If a user mentions filenames such as:
         * "Sem-1.pdf"
         * "Sema-1.pdf and Sem-2.pdf"
         * "details from sem 1 and sem 3"
       - The system does NOT treat this as a request to return filenames.
       - Instead, it understands that the user is asking for the
         CONTENT INSIDE those documents.

    2. Filename as a Constraint, Not the Result
       - Filenames and numeric references (e.g., 1, 2, 3) are interpreted
         as selection constraints to narrow down relevant documents.
       - Once a document is selected via filename or number inference,
         the FULL semantic content of that document is still retrieved,
         re-ranked, grouped, and passed to the LLM.
       - The system never answers using filenames alone.

    3. Semantic Content Retrieval
       - Even when filenames are explicitly mentioned, the system performs
         semantic search over document chunks to retrieve meaningful content.
       - This ensures that answers are grounded in actual document text,
         not metadata.

    4. Mixed Intent Handling
       - Supports mixed queries such as:
         * "Explain SGPA from Sem-1 and Sem-3"
         * "Share all details from sem 2 pdf"
         * "SGPA less than 7 in Sem-1"
       - In these cases:
         * Filenames → document scope
         * Inequalities → numeric filtering
         * Natural language → semantic intent
       - All constraints are applied BEFORE answer generation.

    5. Context Preservation for Answering
       - After filtering and re-ranking, the system builds a complete
         evidence context from the selected document chunks.
       - This full context (not filenames) is passed to the LLM so that:
         * Answers are factual
         * No hallucinated information is introduced
         * The response reflects the actual document content

    6. Safe Defaults
       - If a user provides only a filename with no clear question,
         the system assumes the intent is to understand or extract
         information from that document.
       - If no supporting content is found, the system explicitly
         states that the answer is not available in the documents.

    In short:
    - Filenames guide WHERE to look.
    - Semantic search determines WHAT to read.
    - Re-ranking decides WHAT matters most.
    - The LLM answers ONLY from retrieved content.

    This ensures correct, explainable behavior even when users
    provide partial, ambiguous, or shorthand queries.
    """

    query = input.get("full_question") if isinstance(input, dict) else str(input)
    top_k = input.get("top_k", 5) if isinstance(input, dict) else 5

    print(f"\n🔍 VECTOR SEARCH → '{query}'")

    raw = search_documents(query, top_k)
    print(f"🧠 Vector returned {len(raw)} chunks (NOT documents)")

    selectors = extract_document_selectors(query)
    inequality = extract_inequality(query)

    filtered = []
    for r in raw:
        if not filename_matches(r["filename"], selectors):
            continue

        if inequality:
            op, val = inequality
            if not satisfies_inequality(r["text"], op, val):
                continue

        r["score"] = score_chunk(query, r["text"])
        filtered.append(r)

    if not filtered:
        return "❌ No documents satisfy query constraints."

    grouped = group_documents(filtered)
    confidence = compute_confidence(grouped)

    # -------------------------------
    # BUILD FINAL CONTEXT (LLM ONLY)
    # -------------------------------
    context = ""
    for fname, data in grouped.items():
        context += f"\n📄 {fname}\n"
        for c in data["chunks"]:
            context += c + "\n"

    final_prompt = f"""
Answer the question using ONLY the context below.
If the answer is not supported, say so clearly.

Context:
{context}

Question:
{query}
"""

    # ============================================================
    # 🔵 LANGCACHE → LLM BOUNDARY (FIXED)
    # ============================================================

    # IMPORTANT:
    # LangCache must receive a SHORT prompt (<=1024 chars).
    # We use the USER QUESTION as the semantic cache key.
    langcache_key = f"Q: {query.strip()}"

    print(f"🔎 CHECKING LANGCACHE (key='{langcache_key[:1023]}...')")

    cached_answer = langcache_lookup(langcache_key)

    if cached_answer:
        print("⚡ LANGCACHE HIT → RETURNING CACHED ANSWER")
        answer = cached_answer
    else:
        print("🤖 LANGCACHE MISS → CALLING CLAUDE")
        answer = call_claude_simple(final_prompt)
        langcache_store(langcache_key, answer)

    return f"""
ANSWER:
{answer}

CONFIDENCE:
{confidence}
""".strip()