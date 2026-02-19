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
    
    Input format: 'document_id="id", filename="filename.pdf"'
    """
    if isinstance(input, str):
        # Parse the input string like 'document_id="id", filename="file"'
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
    
    if not document_id or not filename:
        return "Error: document_id and filename are required"
    
    try:
        url = generate_presigned_url(document_id, filename)
        return f"Download URL: {url}"
    except Exception as e:
        return f"Error generating URL: {str(e)}"