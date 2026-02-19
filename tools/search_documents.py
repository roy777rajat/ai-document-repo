from langchain.tools import tool
from utils import search_documents
from llm import call_claude_simple
import re

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
    query = None
    top_k = 5
    
    # Handle dict input
    if isinstance(input, dict):
        query = input.get('query')
        top_k = input.get('top_k', 5)
    # Handle string input with multiple parsing strategies
    elif isinstance(input, str):
        # Strategy 1: Try regex pattern for quoted query
        if 'query=' in input:
            # Match: query="anything" or query='anything' or query=anything
            match = re.search(r'query\s*=\s*["\']?([^",]+)["\']?(?:\s*,|$)', input)
            if match:
                query = match.group(1).strip()
                # Try to extract top_k if present
                top_k_match = re.search(r'top_k\s*=\s*(\d+)', input)
                if top_k_match:
                    top_k = int(top_k_match.group(1))
        
        # Strategy 2: If still no query, treat entire input as query
        if not query:
            cleaned = input.replace('query=', '').replace('"', '').strip()
            if cleaned and ',' in cleaned:
                query = cleaned.split(',')[0].strip()
            elif cleaned:
                query = cleaned
    
    # Final validation
    if not query or query.strip() == '':
        return ("❌ Error: No search query provided.\n\n"
                "Please provide a search query. Examples:\n"
                "- 'SGPA Roll No from Sem-2'\n"
                "- 'medical report details'\n"
                "- 'academic record data'")
    
    print(f"\n🔍 Searching for: '{query}' (top_k={top_k})")
    
    try:
        results = search_documents(query, top_k)
        print(f"✅ Found {len(results) if results else 0} result(s)")
        
        if results:
            # For detailed content requests, return comprehensive results
            output = f"✅ Found {len(results)} relevant document(s):\n\n"
            
            for idx, res in enumerate(results, 1):
                output += f"【Document {idx}】 {res.get('filename', 'Unknown')}\n"
                output += f"{'─' * 40}\n"
                output += f"{res.get('text', 'No content')}\n\n"
            
            # Add summary of findings
            summary_prompt = f"Please summarize these findings in 2-3 sentences highlighting key points:\n\n{output}"
            summary = call_claude_simple(summary_prompt)
            
            output += f"📝 Summary:\n{summary}\n"
            return output
        else:
            return ("❌ No relevant documents found in the repository.\n\n"
                   "Possible reasons:\n"
                   "1. No documents have been indexed yet (need to upload via Lambda)\n"
                   "2. Your search query doesn't match any document content\n"
                   "3. Documents may not be in Redis vector store yet\n\n"
                   "Next steps:\n"
                   "- Upload documents to S3 bucket 'family-docs-raw'\n"
                   "- Trigger the email ingestor Lambda\n"
                   "- Wait for vector processor Lambda to index documents")
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error during search: {error_msg}")
        return (f"❌ Error searching documents: {error_msg}\n\n"
               f"Troubleshooting:\n"
               f"1. Check if Redis is connected and running\n"
               f"2. Verify AWS credentials are configured\n"
               f"3. Ensure documents have been indexed in Redis\n"
               f"4. Check Bedrock model access for embeddings")
