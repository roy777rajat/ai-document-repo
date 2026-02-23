from langchain.tools import tool
from utils import generate_presigned_url


# """Generate a PRESIGNED DOWNLOAD LINK ONLY. Use this ONLY when user explicitly asks to download or get a link. Do NOT use this for reading document content.
    
#     Use this tool ONLY when user asks:
#     - 'Download [document]'
#     - 'Get download link for [document]'
#     - 'I want to download [document]'
#     - 'Give me the file for [document]'
    
#     Do NOT use this when user asks for content, details, or information FROM the document.
#     Use search_documents_tool for that instead.
    
#     Input format: 'document_id="id", filename="filename.pdf"' OR 'filename="filename.pdf"'
#     If only filename is provided, will look up the document_id automatically.
#     """

@tool
def download_document_tool(input) -> str:
    """
  Generate a PRESIGNED DOWNLOAD LINK ONLY. Use this ONLY when user explicitly asks to download or get a link. Do NOT use this for reading document content.
    
    Use this tool ONLY when user asks:
    - 'Download [document]'
    - 'Get download link for [document]'
    - 'I want to download [document]'
    - 'Give me the file for [document]'
    
    Do NOT use this when user asks for content, details, or information FROM the document.
    Use search_documents_tool for that instead.
    
    Input format: 'document_id="id", filename="filename.pdf"' OR 'filename="filename.pdf"'
    If only filename is provided, will look up the document_id automatically.

    """

    # """Generate a secure, time-limited download link for a document file.
    # This tool is strictly for FILE ACCESS, not for understanding or
    # answering questions about document content.

    # Functional intent and usage rules:

    # 1. Purpose of this Tool
    #    - This tool provides a PRESIGNED download URL that allows the user
    #      to download the original document file (e.g., PDF).
    #    - It does NOT read, summarize, explain, or extract information
    #      from the document.

    # 2. When the Tool SHOULD Be Used
    #    - Use this tool ONLY when the user explicitly expresses download intent,
    #      such as:
    #        * "Download the document"
    #        * "Get the download link for Sem-2.pdf"
    #        * "I want to download my prescription"
    #        * "Give me the file for this document"
    #    - The user intent must clearly be about obtaining the file itself,
    #      not its contents.

    # 3. When the Tool SHOULD NOT Be Used
    #    - Do NOT use this tool when the user asks:
    #        * Questions about document content
    #        * To summarize or explain a document
    #        * To search within a document
    #        * To extract values or details from a document
    #    - In such cases, use the semantic search tool instead.

    # 4. Input Handling
    #    - The tool accepts either:
    #        * A document_id and filename, OR
    #        * A filename alone
    #    - If only the filename is provided, the system will automatically
    #      resolve the corresponding document_id using document metadata.

    # 5. Output Behavior
    #    - Returns a time-limited presigned URL that grants read-only access
    #      to the document file.
    #    - The link expires automatically for security purposes.

    # 6. How This Tool Fits in the Overall Flow
    #    - This tool is typically invoked AFTER:
    #        * The user has discovered a document via metadata listing, or
    #        * The user already knows the exact document they want
    #    - It should never be part of a content-question answering flow.

    # In short:
    # - This tool answers: "How can I download the file?"
    # - It does NOT answer: "What does the document say?"

    # Strictly separating download intent from content intent ensures
    # predictable agent behavior, better security, and a clearer user experience.
    # """


    import re

    print("---------- I am entering download_document_tool -----------------")
    print("RAW INPUT:", repr(input))

    document_id = None
    filename = None

    # -------------------------------------------------
    # 1️⃣ Normalize input
    # -------------------------------------------------
    if isinstance(input, dict):
        document_id = input.get("document_id")
        filename = input.get("filename")

    elif isinstance(input, str):
        # Robust regex extraction
        doc_id_match = re.search(r'document_id\s*=\s*"([^"]+)"', input)
        filename_match = re.search(r'filename\s*=\s*"([^"]+)"', input)

        if doc_id_match:
            document_id = doc_id_match.group(1)

        if filename_match:
            filename = filename_match.group(1)

    else:
        return "Error: Invalid input format"

    print("PARSED document_id:", document_id)
    print("PARSED filename:", filename)

    # -------------------------------------------------
    # 2️⃣ Resolve document_id if missing
    # -------------------------------------------------
    if filename and not document_id:
        from utils import get_all_document_metadata

        print("🔍 Resolving document_id from filename")
        metadata = get_all_document_metadata()

        for doc in metadata:
            if doc.get("filename") == filename:
                pk = doc.get("PK", "")
                if pk.startswith("DOC#"):
                    document_id = pk[4:]
                break

        if not document_id:
            return f"Error: Document '{filename}' not found"

    # -------------------------------------------------
    # 3️⃣ Final validation
    # -------------------------------------------------
    if not document_id or not filename:
        return "Error: document_id and filename are required"

    # -------------------------------------------------
    # 4️⃣ Generate presigned URL
    # -------------------------------------------------
    try:
        url = generate_presigned_url(document_id, filename)
        return f"Download URL: {url}"
    except Exception as e:
        return f"Error generating URL: {str(e)}"