import os
import random
import logging
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from twilio.rest import Client

from agent_runner import run_agent
from tools.search_documents import search_documents_tool
from tools.download_document import download_document_tool


# ============================================================
# Logging Configuration
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("family-docs-agent-api")


# ============================================================
# FastAPI App
# ============================================================
app = FastAPI(title="Family Docs Agent API")

executor = ThreadPoolExecutor(
    max_workers=int(os.getenv("API_MAX_WORKERS", "2"))
)


# ============================================================
# Twilio Configuration
# ============================================================
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    logger.info("Twilio client initialized")
else:
    logger.warning("Twilio credentials not configured")


# ============================================================
# Request Models
# ============================================================
class QueryRequest(BaseModel):
    question: str
    options: Optional[dict] = None


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


# ============================================================
# Health Check
# ============================================================
@app.get("/health")
def health():
    logger.debug("Health check called")
    return {"status": "ok", "service": "family-docs-agent"}


# ============================================================
# Main Agent API
# ============================================================
@app.post("/api/v1/query")
def api_query(req: QueryRequest):
    if not req.question:
        logger.warning("Query API called without question")
        raise HTTPException(status_code=400, detail="question is required")

    logger.info("Agent query received")

    future = executor.submit(run_agent, req.question)
    result = future.result()

    logger.info("Agent query completed")

    return {"answer": result}


# ============================================================
# Search API
# ============================================================
@app.post("/api/v1/search")
def api_search(req: SearchRequest):
    logger.info("Search API called")

    input_str = f'query="{req.query}", top_k={req.top_k}'
    result = search_documents_tool(input_str)

    logger.info("Search API completed")

    return {"results": result}


# ============================================================
# Download API
# ============================================================
@app.get("/api/v1/download")
def api_download(filename: Optional[str] = None, document_id: Optional[str] = None):
    logger.info("Download API called")

    if not filename and not document_id:
        logger.warning("Download API missing parameters")
        raise HTTPException(
            status_code=400,
            detail="filename or document_id is required"
        )

    if filename and not document_id:
        input_str = f'filename="{filename}"'
    elif document_id and filename:
        input_str = f'document_id="{document_id}", filename="{filename}"'
    else:
        input_str = f'document_id="{document_id}", filename="{filename or ""}"'

    result = download_document_tool(input_str)

    if isinstance(result, str) and result.startswith("Error:"):
        logger.error("Download API failed")
        raise HTTPException(status_code=500, detail=result)

    logger.info("Download API completed")

    return {"download_url": result}


# ============================================================
# Random Number API (Dummy Test Endpoint)
# ============================================================
@app.post("/api/v1/random")
def api_random():
    rand = random.randint(1, 1000)
    logger.info(f"Random API generated value: {rand}")

    return {"random_number": rand}


# ============================================================
# WhatsApp Webhook
# ============================================================
@app.post("/api/v1/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    if not twilio_client:
        logger.error("WhatsApp webhook called but Twilio not configured")
        raise HTTPException(status_code=500, detail="Twilio not configured")

    form = await request.form()
    user_message = form.get("Body")
    from_number = form.get("From")

    logger.info(f"WhatsApp message received from {from_number}")

    if not user_message or not from_number:
        logger.warning("WhatsApp webhook missing Body or From")
        return "OK"

    # --------------------------------------------------------
    # Dummy command for testing connectivity
    # --------------------------------------------------------
    if user_message.strip().lower() == "random":
        rand = random.randint(1, 1000)
        answer = f"🎲 Random number: {rand}"
        logger.info("Random command handled via WhatsApp")
    else:
        logger.info("Routing message to AI agent")
        future = executor.submit(run_agent, user_message)
        answer = future.result()

    if not answer:
        logger.warning("Agent returned empty response")
        answer = "Sorry, I couldn’t find an answer to that."

    logger.info("Sending WhatsApp reply")

    twilio_client.messages.create(
        from_=TWILIO_WHATSAPP_NUMBER,
        to=from_number,
        body=answer
    )

    logger.info("WhatsApp reply sent successfully")

    return "OK"
