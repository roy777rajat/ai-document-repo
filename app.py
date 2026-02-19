from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import os
from concurrent.futures import ThreadPoolExecutor

from agent_runner import run_agent
from tools.search_documents import search_documents_tool
from tools.download_document import download_document_tool

app = FastAPI(title="Family Docs Agent API")

executor = ThreadPoolExecutor(max_workers=int(os.getenv('API_MAX_WORKERS', '2')))


class QueryRequest(BaseModel):
    question: str
    options: Optional[dict] = None


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


@app.get("/health")
def health():
    return {"status": "ok", "service": "family-docs-agent"}


@app.post("/api/v1/query")
def api_query(req: QueryRequest):
    if not req.question:
        raise HTTPException(status_code=400, detail="question is required")

    # Run agent in threadpool to avoid blocking event loop
    future = executor.submit(run_agent, req.question)
    result = future.result()

    return {"answer": result}


@app.post("/api/v1/search")
def api_search(req: SearchRequest):
    input_str = f'query="{req.query}", top_k={req.top_k}'
    result = search_documents_tool(input_str)
    return {"results": result}


@app.get("/api/v1/download")
def api_download(filename: Optional[str] = None, document_id: Optional[str] = None):
    if not filename and not document_id:
        raise HTTPException(status_code=400, detail="filename or document_id is required")

    if filename and not document_id:
        input_str = f'filename="{filename}"'
    elif document_id and filename:
        input_str = f'document_id="{document_id}", filename="{filename}"'
    else:
        input_str = f'document_id="{document_id}", filename="{filename or ""}"'

    result = download_document_tool(input_str)
    if isinstance(result, str) and result.startswith("Error:"):
        raise HTTPException(status_code=500, detail=result)

    # download_document_tool returns a text string; try to extract URL
    return {"download_url": result}
