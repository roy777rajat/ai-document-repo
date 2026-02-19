from langchain.tools import tool
from utils import search_documents
from llm import call_claude_simple

@tool
def search_documents_tool(input) -> str:
    """Retrieve FULL CONTENT and detailed information from documents. Use this to answer questions about document content, get details, summaries, or extract information. Do NOT use download_document_tool for content retrieval.
    
    Use this tool when user asks:
    - 'Give me all details from [document name]'
    - 'What is in [document]?'
    - 'Find information about [topic]'
    - 'Show me content from [document]'
    - 'Extract details from [document]'
    
    Input format: 'query="search text", top_k=5'
    """
    if isinstance(input, str):
        # Parse the input string like 'query="text", top_k=5'
        pairs = [p.strip() for p in input.split(',')]
        kwargs = {}
        for pair in pairs:
            if '=' in pair:
                key, value = pair.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                if key == 'top_k':
                    try:
                        value = int(value)
                    except:
                        value = 5
                kwargs[key] = value
        query = kwargs.get('query')
        top_k = kwargs.get('top_k', 5)
    elif isinstance(input, dict):
        query = input.get('query')
        top_k = input.get('top_k', 5)
    else:
        return "Error: Invalid input format"
    
    if not query:
        return "Error: query is required"
    
    results = search_documents(query, top_k)
    if results:
        # For detailed content requests, return comprehensive results
        output = f"🔍 Found {len(results)} relevant document(s):\n\n"
        
        for idx, res in enumerate(results, 1):
            output += f"【Document {idx}】 {res['filename']}\n"
            output += f"───────────────────────────\n"
            output += f"{res['text']}\n\n"
        
        # Add summary of findings
        summary_prompt = f"Please summarize these findings in 2-3 sentences highlighting key points:\n\n{output}"
        summary = call_claude_simple(summary_prompt)
        
        output += f"📝 Summary:\n{summary}\n"
        return output
    else:
        return "❌ No relevant documents found for your query."