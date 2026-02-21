from langchain.tools import tool
from utils import search_documents
from llm import call_claude_simple

import re
import math
from typing import List, Dict, Tuple


# ============================================================
# TOKENIZATION
# ============================================================

def tokenize(text: str) -> List[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\. ]", " ", text)
    return [t for t in text.split() if len(t) > 2]


# ============================================================
# INEQUALITY EXTRACTION (VALUE CONDITIONS)
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
            print(f"\n📐 Inequality detected: {op} {m.group(1)}")
            return op, float(m.group(1))
    return None


def satisfies_inequality(text: str, op: str, value: float) -> bool:
    numbers = [float(n) for n in re.findall(r"\d+\.\d+|\d+", text)]
    for n in numbers:
        if (
            (op == "<" and n < value) or
            (op == ">" and n > value) or
            (op == "<=" and n <= value) or
            (op == ">=" and n >= value)
        ):
            return True
    return False


# ============================================================
# DOCUMENT SELECTOR EXTRACTION (CONTEXT-AWARE)
# ============================================================

def extract_document_selectors(query: str) -> set[int]:
    """
    Extract document selectors ONLY when numbers are tied
    to document-referencing context (e.g. sem, semester, part, doc).
    """
    query = query.lower()

    matches = re.findall(
        r"(?:sem|semester|document|doc|part)\s*(\d+)",
        query
    )

    selectors = {int(n) for n in matches}
    print(f"\n🎯 Document selectors resolved: {selectors}")
    return selectors


def filename_satisfies_selectors(filename: str, selectors: set[int]) -> bool:
    if not selectors:
        return True
    fname_nums = set(map(int, re.findall(r"\d+", filename)))
    return bool(fname_nums & selectors)


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

@tool
def search_documents_tool(input) -> str:
    """
    Constraint-aware semantic document search with inequality support.
    """

    query = input.get("query") if isinstance(input, dict) else str(input)
    top_k = input.get("top_k", 5) if isinstance(input, dict) else 5

    print(f"\n🔍 VECTOR SEARCH → '{query}'")
    raw = search_documents(query, top_k)
    print(f"🧠 Vector returned {len(raw)} chunks")

    inequality = extract_inequality(query)
    selectors = extract_document_selectors(query)

    constrained = []
    for r in raw:
        if not filename_satisfies_selectors(r["filename"], selectors):
            continue

        if inequality:
            op, val = inequality
            if not satisfies_inequality(r["text"], op, val):
                continue

        r["score"] = score_chunk(query, r["text"])
        constrained.append(r)

    if not constrained:
        return "❌ No documents satisfy query constraints."

    grouped = group_documents(constrained)
    confidence = compute_confidence(grouped)

    context = ""
    for fname, data in grouped.items():
        context += f"\n📄 {fname}\n"
        for c in data["chunks"]:
            context += c + "\n"

    answer = call_claude_simple(
        f"Answer the question using ONLY the context below.\n\n{context}\n\nQuestion: {query}"
    )

    return f"""
ANSWER:
{answer}

CONFIDENCE:
{confidence}
""".strip()
