from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import os
from concurrent.futures import ThreadPoolExecutor
import requests

from agent_runner import run_agent
from tools.search_documents import search_documents_tool
from tools.download_document import download_document_tool

from twilio.rest import Client

app = FastAPI(title="Family Docs Agent API")

executor = ThreadPoolExecutor(max_workers=int(os.getenv('API_MAX_WORKERS', '2')))

# ------------------------------------------------------------
# Twilio setup
# ------------------------------------------------------------
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


# ------------------------------------------------------------
# Request models
# ------------------------------------------------------------
class QueryRequest(BaseModel):
    question: str
    options: Optional[dict] = None


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


# ------------------------------------------------------------
# Health
# ------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "service": "family-docs-agent"}


# ------------------------------------------------------------
# Main Agent API (UNCHANGED)
# ------------------------------------------------------------
@app.post("/api/v1/query")
def api_query(req: QueryRequest):
    if not req.question:
        raise HTTPException(status_code=400, detail="question is required")

    future = executor.submit(run_agent, req.question)
    result = future.result()

    return {"answer": result}


# ------------------------------------------------------------
# Search API (UNCHANGED)
# ------------------------------------------------------------
@app.post("/api/v1/search")
def api_search(req: SearchRequest):
    input_str = f'query="{req.query}", top_k={req.top_k}'
    result = search_documents_tool(input_str)
    return {"results": result}


# ------------------------------------------------------------
# Download API (UNCHANGED)
# ------------------------------------------------------------
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

    return {"download_url": result}


# ------------------------------------------------------------
# WhatsApp Webhook (NEW)
# ------------------------------------------------------------
@app.post("/api/v1/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    if not twilio_client:
        raise HTTPException(status_code=500, detail="Twilio not configured")

    form = await request.form()

    user_message = form.get("Body")
    from_number = form.get("From")

    if not user_message or not from_number:
        return "OK"

    # Run agent safely in threadpool
    future = executor.submit(run_agent, user_message)
    answer = future.result()

    if not answer:
        answer = "Sorry, I couldn’t find an answer to that."

    # Send response back to WhatsApp
    twilio_client.messages.create(
        from_=TWILIO_WHATSAPP_NUMBER,
        to=from_number,
        body=answer
    )

    return "OK"


import random


@app.post("/api/v1/random")
def api_random():
    """
    Dummy endpoint to generate a random number.
    """
    return {
        "random_number": random.randint(1, 1000)
    }
