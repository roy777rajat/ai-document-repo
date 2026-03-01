# get_all_document_metadata.py

from langchain.tools import tool
import time


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
                "message": "No metadata found.",
                "trace": {
                    "document_count": 0,
                    "latency_ms": latency_ms,
                    "status": "success",
                },
            }

        # --------------------------------------------------------
        # Build user-facing table (UNCHANGED BEHAVIOR)
        # --------------------------------------------------------
        table_str = "Document Metadata:\n"
        table_str += "| Document ID | Filename | Sender | Subject | Received At | Status |\n"
        table_str += "|-------------|----------|--------|---------|-------------|--------|\n"

        for item in metadata:
            table_str += (
                f"| {item.get('document_id', '')} "
                f"| {item.get('filename', '')} "
                f"| {item.get('sender_email', '')} "
                f"| {item.get('subject', '')} "
                f"| {item.get('received_at', '')} "
                f"| {item.get('status', '')} |\n"
            )

        return {
            "status": "success",
            "answer": table_str,
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