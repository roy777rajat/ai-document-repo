from langchain.tools import tool
from utils import generate_presigned_url

@tool
def download_document_tool(input) -> str:
    """Generate a PRESIGNED DOWNLOAD LINK ONLY. Use this ONLY when user explicitly asks to download or get a link. Do NOT use this for reading document content.
    
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
    if isinstance(input, str):
        # Parse the input string like 'document_id="id", filename="file"' or just 'filename="file"'
        pairs = [p.strip() for p in input.split(',')]
        kwargs = {}
        for pair in pairs:
            if '=' in pair:
                key, value = pair.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                kwargs[key] = value
        document_id = kwargs.get('document_id')
        filename = kwargs.get('filename')
    elif isinstance(input, dict):
        document_id = input.get('document_id')
        filename = input.get('filename')
    else:
        return "Error: Invalid input format"
    
    # If we have filename but no document_id, look it up
    if filename and not document_id:
        try:
            from utils import get_all_document_metadata
            metadata = get_all_document_metadata()
            for doc in metadata:
                if doc.get('filename') == filename:
                    # Extract document_id from PK (format: "DOC#123")
                    pk = doc.get('PK', '')
                    if pk.startswith('DOC#'):
                        document_id = pk[4:]  # Remove "DOC#" prefix
                    break
            if not document_id:
                return f"Error: Could not find document_id for filename '{filename}'"
        except Exception as e:
            return f"Error looking up document_id: {str(e)}"
    
    if not document_id or not filename:
        return "Error: document_id and filename are required"
    
    try:
        url = generate_presigned_url(document_id, filename)
        return f"Download URL: {url}"
    except Exception as e:
        return f"Error generating URL: {str(e)}"