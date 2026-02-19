from langchain.tools import tool
from utils import get_all_document_metadata

@tool
def get_all_document_metadata_tool(tool_input=None) -> str:
    """Retrieve all document metadata from DynamoDB."""
    try:
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