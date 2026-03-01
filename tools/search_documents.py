# search_documents.py

from langchain.tools import tool
from typing import List, Dict, Tuple
import re
import math



from utils import search_documents
from llm import call_claude_simple

# 🔵 LangCache helpers
from lang_cache_utils import langcache_store, langcache_lookup


# ============================================================
# TOKENIZATION
# ============================================================

def tokenize(text: str) -> List[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\. ]", " ", text)
    return [t for t in text.split() if len(t) > 2]


# ============================================================
# QUERY KEYWORDS
# ============================================================

def extract_query_keywords(query: str) -> set:
    stopwords = {
        "give", "please", "provide", "me", "the", "and", "for",
        "by", "of", "is", "are", "with", "as", "can", "you"
    }
    tokens = tokenize(query)
    return {t for t in tokens if t not in stopwords}


def document_covers_query(
    doc_chunks: List[str],
    query_keywords: set,
    min_hits: int = 2
) -> bool:
    text = " ".join(doc_chunks).lower()
    hits = sum(1 for kw in query_keywords if kw in text)
    return hits >= min_hits


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

    ranking_match = re.search(r"\b(top|first|last|max|min|avg)\s+(\d+)\b", q)
    ranking_number = int(ranking_match.group(2)) if ranking_match else None

    filenames = set(re.findall(r"\b[a-z0-9\-_]+\.pdf\b", q))
    all_numbers = set(map(int, re.findall(r"\d+", q)))

    if ranking_number is not None:
        all_numbers.discard(ranking_number)

    return {
        "filenames": filenames,
        "numbers": all_numbers,
        "limit": ranking_number
    }


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
# 🔴 TOOL (INSTRUMENTED)
# ============================================================

@tool
def search_documents_tool(input) -> dict:
    """
    Semantic document search with authoritative document selection.
    """

    query = None
    top_k = 5

    if isinstance(input, dict):
        query = input.get("full_question") or input.get("query")
        top_k = input.get("top_k", 5)
    elif isinstance(input, str):
        query = input.strip()

    if not query or not isinstance(query, str):
        return {"answer": "❌ Error: search query is missing or invalid."}

    # --------------------------------------------------------
    # VECTOR SEARCH
    # --------------------------------------------------------
    raw = search_documents(query, top_k)

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
        return {"answer": "❌ No documents satisfy query constraints."}

    grouped = group_documents(filtered)
    confidence = compute_confidence(grouped)

    # --------------------------------------------------------
    # AUTHORITATIVE DOCUMENT SELECTION
    # --------------------------------------------------------
    query_keywords = extract_query_keywords(query)

    eligible_docs = []
    for fname, data in grouped.items():
        if document_covers_query(data["chunks"], query_keywords):
            eligible_docs.append((fname, data))

    if not eligible_docs:
        return {
            "answer": "❌ No document contains sufficient information to answer the question."
        }

    eligible_docs.sort(key=lambda x: x[1]["score"], reverse=True)
    authoritative_docs = [eligible_docs[0][0]]

    # --------------------------------------------------------
    # CONTEXT BUILD (AUTHORITATIVE ONLY)
    # --------------------------------------------------------
    context_text = ""
    for fname in authoritative_docs:
        for c in grouped[fname]["chunks"]:
            context_text += c + "\n"

    final_prompt = f"""
Answer the question using ONLY the context below.

Context:
{context_text}

Question:
{query}
"""

    # --------------------------------------------------------
    # CACHE → LLM
    # --------------------------------------------------------
    langcache_key = f"Q: {query.strip()}"
    cached_answer = langcache_lookup(langcache_key)

    cache_hit = cached_answer is not None

    if cache_hit:
        answer = cached_answer
    else:
        answer = call_claude_simple(final_prompt)
        langcache_store(langcache_key, answer)

    # --------------------------------------------------------
    # RETURN (TRACE-SAFE)
    # --------------------------------------------------------
    return {
        "answer": f"""
ANSWER:
{answer}

CONFIDENCE (retrieval-only):
{confidence}

TARGET (Actual docs):
{authoritative_docs}
""".strip(),
        "resolved_filenames": authoritative_docs,
        "confidence": confidence,

        # 🔴 TRACE SIGNALS (SAFE)
        "trace": {
            "authoritative_docs": authoritative_docs,
            "confidence": confidence,
            "cache_hit": cache_hit,
            "answer_length_chars": len(answer),
        }
    }