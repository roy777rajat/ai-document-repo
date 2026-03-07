# get_all_document_metadata.py

from langchain.tools import tool
import time
from datetime import datetime

from utils import get_all_document_metadata


@tool
def get_all_document_metadata_tool(tool_input=None) -> str:
    """
    Retrieve a complete list of available documents and their metadata.
    Discovery-only tool.
    """

    start_ts = time.perf_counter()

    try:
        print("---------- ENTER get_all_document_metadata_tool ----------")

        metadata = get_all_document_metadata()

        latency_ms = round((time.perf_counter() - start_ts) * 1000, 2)

        if not metadata:

            return {
                "status": "success",
                "answer": "📭 No documents found in the system.",
                "trace": {
                    "document_count": 0,
                    "latency_ms": latency_ms,
                    "status": "success",
                },
            }

        # --------------------------------------------------------
        # SORT BY RECEIVED DATE DESC
        # --------------------------------------------------------

        def parse_date(item):
            try:
                return datetime.fromisoformat(item.get("received_at", "").replace("Z", ""))
            except:
                return datetime.min

        metadata = sorted(metadata, key=parse_date, reverse=True)

        # --------------------------------------------------------
        # BUILD CHAT FRIENDLY OUTPUT
        # --------------------------------------------------------

        output = f"📄 Available Documents ({len(metadata)})\n\n"

        for idx, item in enumerate(metadata, start=1):

            filename = item.get("filename", "Unknown")
            sender = item.get("sender_email", "Unknown")
            subject = item.get("subject", "N/A")
            received = item.get("received_at", "N/A")

            output += (
                f"{idx}️⃣ {filename} 📋\n"
                f"   Sender: {sender}\n"
                f"   Subject: {subject}\n"
                f"   Received: {received}\n\n"
            )

        return {
            "status": "success",
            "answer": output,
            "trace": {
                "document_count": len(metadata),
                "latency_ms": latency_ms,
                "status": "success",
            },
        }

    except Exception as e:

        latency_ms = round((time.perf_counter() - start_ts) * 1000, 2)

        return {
            "status": "error",
            "message": str(e),
            "trace": {
                "document_count": 0,
                "latency_ms": latency_ms,
                "status": "error",
            },
        }