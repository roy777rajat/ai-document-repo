from langchain.tools import tool
from utils import get_all_document_metadata


# """Retrieve all document metadata from DynamoDB, You can see all doucument file name, document ID and other details related to document metadata.
    
#     Use this tool ONLY when user asks:
#     - 'To See the full document list'
#     - 'Get all documents metadata list'
#     """

@tool
def get_all_document_metadata_tool(tool_input=None) -> str:
    """
    Retrieve a complete list of available documents and their metadata
    to help users understand what documents exist in the system.

    Functional intent and usage rules:

    1. Purpose of this Tool
       - This tool is meant for DISCOVERY, not content retrieval.
       - It provides a high-level inventory of documents stored in the system,
         including document identifiers and descriptive metadata.
       - It does NOT return document content, summaries, or answers.

    2. What This Tool Returns
       - A list of all documents stored in DynamoDB, including:
         * Document ID
         * Filename
         * Any associated metadata (e.g., upload details, category, tags)
       - This allows users to:
         * See what documents are available
         * Know the exact filenames or IDs for follow-up queries
         * Decide which document they want to explore or download next

    3. When the Tool SHOULD Be Used
       - Use this tool ONLY when the user explicitly asks to:
         * "See the full document list"
         * "Show all documents"
         * "List all available documents"
         * "Get all document metadata"
         * "What documents do I have?"

    4. When the Tool SHOULD NOT Be Used
       - Do NOT use this tool when the user asks:
         * Questions about document content
         * To summarize, explain, or extract information
         * To download a specific document
       - In such cases, content-search or download tools must be used instead.

    5. How This Tool Fits in the Overall Flow
       - This tool helps users orient themselves when they are unsure
         what documents exist in the system.
       - It often acts as a first step before:
         * Content-based queries
         * Semantic search
         * Download requests

    In short:
    - This tool answers: "What documents are available?"
    - It does NOT answer: "What is inside a document?"

    Keeping this separation ensures predictable, explainable agent behavior
    and avoids unnecessary or incorrect tool usage.
    """
    try:
        
        print("----------I am entering into get_all_document_metadata tool call -----------------")

        metadata = get_all_document_metadata()
        if metadata:
            table_str = "Document Metadata:\n"
            table_str += "| Document ID | Filename | Sender | Subject | Received At | Status |\n"
            table_str += "|-------------|----------|--------|---------|-------------|--------|\n"
            for item in metadata:
                table_str += f"| {item.get('document_id', '')} | {item.get('filename', '')} | {item.get('sender_email', '')} | {item.get('subject', '')} | {item.get('received_at', '')} | {item.get('status', '')} |\n"
            return table_str
        else:
            return "No metadata found."
    except Exception as e:
        return f"Error retrieving metadata: {str(e)}"