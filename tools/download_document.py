# download_document.py

from langchain.tools import tool
import re



from utils import generate_presigned_url


@tool
def download_document_tool(input) -> str:
    """
    Generate a PRESIGNED DOWNLOAD LINK ONLY.
    """

    print("---------- ENTER download_document_tool ----------")
    print("RAW INPUT:", repr(input))

    document_id = None
    filename = None
    resolution_strategy = "unknown"

    # -------------------------------------------------
    # 1️⃣ Normalize input
    # -------------------------------------------------
    if isinstance(input, dict):
        document_id = input.get("document_id")
        filename = input.get("filename")
        resolution_strategy = "direct"

    elif isinstance(input, str):
        doc_id_match = re.search(r'document_id\s*=\s*"([^"]+)"', input)
        filename_match = re.search(r'filename\s*=\s*"([^"]+)"', input)

        if doc_id_match:
            document_id = doc_id_match.group(1)
            resolution_strategy = "direct"

        if filename_match:
            filename = filename_match.group(1)
            resolution_strategy = "direct"

    else:
        return "Error: Invalid input format"

    print("PARSED document_id:", document_id)
    print("PARSED filename:", filename)

    # -------------------------------------------------
    # 2️⃣ Resolve document_id if missing
    # -------------------------------------------------
    if filename and not document_id:
        from utils import get_all_document_metadata

        resolution_strategy = "metadata_lookup"
        metadata = get_all_document_metadata()

        for doc in metadata:
            if doc.get("filename") == filename:
                pk = doc.get("PK", "")
                if pk.startswith("DOC#"):
                    document_id = pk[4:]
                break

        if not document_id:
            return {
                "status": "error",
                "message": f"Document '{filename}' not found",
                "trace": {
                    "resolved_filename": filename,
                    "resolved_document_id": None,
                    "resolution_strategy": resolution_strategy,
                    "status": "error",
                },
            }

    # -------------------------------------------------
    # 3️⃣ Final validation
    # -------------------------------------------------
    if not document_id or not filename:
        return {
            "status": "error",
            "message": "document_id and filename are required",
            "trace": {
                "resolved_filename": filename,
                "resolved_document_id": document_id,
                "resolution_strategy": resolution_strategy,
                "status": "error",
            },
        }

    # -------------------------------------------------
    # 4️⃣ Generate presigned URL
    # -------------------------------------------------
    try:
        url = generate_presigned_url(document_id, filename)

        return {
            "status": "success",
            "download_url": url,  # NOT logged in LangSmith UI
            "trace": {
                "resolved_filename": filename,
                "resolved_document_id": document_id,
                "resolution_strategy": resolution_strategy,
                "status": "success",
            },
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "trace": {
                "resolved_filename": filename,
                "resolved_document_id": document_id,
                "resolution_strategy": resolution_strategy,
                "status": "error",
            },
        }