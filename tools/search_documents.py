from langchain.tools import tool
from utils import search_documents
from llm import call_claude_simple

@tool
def search_documents_tool(input) -> str:
    """Search for documents based on semantic similarity to the query."""
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
        summary_prompt = f"Summarize the following search results in bullet points or paragraphs, and in brackets mention the sources (document names):\n\n"
        for res in results:
            summary_prompt += f"- From {res['filename']}: {res['text'][:200]}...\n"
        summary = call_claude_simple(summary_prompt)
        return summary
    else:
        return "No relevant documents found."