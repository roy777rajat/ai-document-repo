from langchain.tools import tool
from typing import List, Dict
import re
import math

from utils import search_documents
from llm import call_claude_simple
from lang_cache_utils import langcache_store, langcache_lookup


# ============================================================
# TOKENIZATION
# ============================================================

def tokenize(text: str):

    text = text.lower()

    text = re.sub(r"[^a-z0-9]", " ", text)

    return [t for t in text.split() if len(t) > 1]


# ============================================================
# CHUNK SCORING
# ============================================================

def score_chunk(query, chunk):

    q_tokens = tokenize(query)

    c_tokens = tokenize(chunk)

    if not q_tokens or not c_tokens:
        return 0

    overlap = len(set(q_tokens) & set(c_tokens)) / len(q_tokens)

    density = sum(t in q_tokens for t in c_tokens) / len(c_tokens)

    numeric = len(re.findall(r"\d+", chunk)) / len(c_tokens)

    length_penalty = math.log(len(c_tokens) + 1)

    return (overlap * 3 + density * 8 + numeric * 5) / length_penalty


# ============================================================
# DOCUMENT GROUPING
# ============================================================

def group_documents(chunks):

    grouped = {}

    for c in chunks:

        fname = c["filename"]

        grouped.setdefault(
            fname,
            {"chunks": [], "score": 0}
        )

        grouped[fname]["chunks"].append(c["text"])

        grouped[fname]["score"] += c["score"]

    return grouped


# ============================================================
# CONFIDENCE
# ============================================================

def compute_confidence(grouped):

    max_score = max(v["score"] for v in grouped.values())

    return {
        k: round(v["score"] / max_score, 3)
        for k, v in grouped.items()
    }


# ============================================================
# FILENAME EXTRACTION
# ============================================================

def extract_filenames(query):

    return re.findall(r"[a-zA-Z0-9_\-]+\.pdf", query.lower())


# ============================================================
# IDENTIFIER EXTRACTION
# ============================================================

def extract_identifiers(query):

    return re.findall(r"[A-Za-z0-9]{6,}", query)


# ============================================================
# SEMESTER DETECTION
# ============================================================

def extract_semester_number(query):

    m = re.search(r"(semester|sem)\s*[-]?\s*(\d+)", query.lower())

    if m:
        return m.group(2)

    return None


# ============================================================
# TOOL
# ============================================================

@tool
def search_documents_tool(input) -> dict:
    """
    Semantic document retrieval with deterministic document ranking.
    """

    query = None
    top_k = 20

    if isinstance(input, dict):

        query = input.get("full_question") or input.get("query")

        top_k = input.get("top_k", 20)

    elif isinstance(input, str):

        query = input.strip()

    if not query:
        return {"answer": "Invalid query"}

    # --------------------------------------------------------
    # VECTOR SEARCH
    # --------------------------------------------------------

    raw = search_documents(query, top_k)

    if not raw:
        return {"answer": "No documents found."}

    # --------------------------------------------------------
    # SCORE CHUNKS
    # --------------------------------------------------------

    for r in raw:

        r["score"] = score_chunk(query, r["text"])

    grouped = group_documents(raw)

    # --------------------------------------------------------
    # QUERY SIGNALS
    # --------------------------------------------------------

    filenames = extract_filenames(query)

    identifiers = extract_identifiers(query)

    semester_number = extract_semester_number(query)

    q_tokens = set(tokenize(query))

    # --------------------------------------------------------
    # DOCUMENT BOOSTING
    # --------------------------------------------------------

    for fname, data in grouped.items():

        fname_lower = fname.lower()

        full_text = " ".join(data["chunks"]).lower()

        # explicit filename match
        if any(f in fname_lower for f in filenames):
            data["score"] += 50

        # semester detection
        if semester_number and f"sem-{semester_number}" in fname_lower:
            data["score"] += 60

        # identifier in filename
        if any(i.lower() in fname_lower for i in identifiers):
            data["score"] += 25

        # identifier inside document text
        if any(i.lower() in full_text for i in identifiers):
            data["score"] += 30

        # keyword boost
        if any(t in fname_lower for t in q_tokens):
            data["score"] += 5

    # --------------------------------------------------------
    # RANK DOCUMENTS
    # --------------------------------------------------------

    ranked = sorted(
        grouped.items(),
        key=lambda x: x[1]["score"],
        reverse=True
    )

    authoritative_doc = ranked[0][0]

    top_docs = ranked[:3]

    # --------------------------------------------------------
    # CONTEXT BUILD
    # --------------------------------------------------------

    context = ""

    for fname, data in top_docs:

        for c in data["chunks"]:
            context += c + "\n"

    # --------------------------------------------------------
    # DOWNLOAD QUERIES
    # --------------------------------------------------------

    if "download" in query.lower():

        return {

            "answer": "Document located.",

            "resolved_filenames": [authoritative_doc],

            "confidence": compute_confidence(grouped),

            "trace": {
                "authoritative_doc": authoritative_doc
            }
        }

    # --------------------------------------------------------
    # PROMPT
    # --------------------------------------------------------

    prompt = f"""
Answer the question using the document content below.

DOCUMENT CONTENT:
{context}

QUESTION:
{query}

Provide the answer based only on the document text.
"""

    cache_key = f"Q:{query}"

    cached = langcache_lookup(cache_key)

    if cached:

        answer = cached
        cache_hit = True

    else:

        answer = call_claude_simple(prompt)

        langcache_store(cache_key, answer)

        cache_hit = False

    return {

        "answer": answer,

        "resolved_filenames": [authoritative_doc],

        "confidence": compute_confidence(grouped),

        "trace": {

            "authoritative_doc": authoritative_doc,

            "documents_used": [d[0] for d in top_docs],

            "cache_hit": cache_hit
        }
    }