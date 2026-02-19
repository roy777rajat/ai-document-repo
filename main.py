import os
import importlib.util
from langchain_aws import ChatBedrock
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import ChatPromptTemplate
from langchain.tools import BaseTool

# Dynamically load tools from tools directory
def load_tools():
    tools_dir = os.path.join(os.path.dirname(__file__), 'tools')
    tools = []
    
    for filename in os.listdir(tools_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3]  # remove .py
            spec = importlib.util.spec_from_file_location(module_name, os.path.join(tools_dir, filename))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get all tool functions (those decorated with @tool)
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if hasattr(attr, 'name') and hasattr(attr, 'description') and callable(getattr(attr, 'run', None)):
                    tools.append(attr)
    
    return tools

def main():
    # Load tools
    tools = load_tools()
    
    # Initialize Bedrock LLM
    llm = ChatBedrock(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        region_name="eu-west-1",
        model_kwargs={
            "temperature": 0.0
        }
    )
    
    # Create prompt
    prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant for managing family documents. Use the available tools to answer questions.

⚠️ IMPORTANT TOOL SELECTION RULES:

1. USE search_documents_tool WHEN:
   - User asks for content, details, or information FROM a document
   - User wants to "show me", "tell me", "what is", "get details from", "extract from"
   - Example: "Give me all details from Sem-2.pdf" → USE search_documents_tool
   - Example: "What's in the medical report?" → USE search_documents_tool

2. USE download_document_tool ONLY WHEN:
   - User explicitly asks to DOWNLOAD or GET A LINK
   - User wants to save/download the actual file
   - Example: "Download Sem-2.pdf" → USE download_document_tool
   - Example: "Give me download link" → USE download_document_tool
   - Input can be just 'filename="Sem-2.pdf"' - tool will look up document_id automatically

3. NEVER use download_document_tool to retrieve content or details from documents.
   Always use search_documents_tool for content retrieval.

🔍 SEARCH STRATEGY FOR MULTIPLE ITEMS:
When user asks for information from multiple documents or semesters:
- DO ONE COMPREHENSIVE SEARCH with a broad query like "SGPA" or "academic records"
- Set top_k higher (e.g., 10) to get all relevant documents
- Extract specific information for all requested items in one pass
- Example: "Give me Sem-1 and Sem-4 SGPA" → search "SGPA" with top_k=10, NOT separate searches

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do. First identify if user wants CONTENT (use search) or DOWNLOAD LINK (use download).
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question
Alawys mention the file name in this manner Sem-1.pdf,Sem-2.pdf as an example, where you get the data.
Begin!

Question: {input}
Thought:{agent_scratchpad}
""")
    
    # Create agent
    agent = create_react_agent(llm, tools, prompt)
    # CRITICAL: Increased max_iterations from default 15 to 30 to handle complex searches
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True, 
        handle_parsing_errors=True,
        max_iterations=30,  # Increased from default 15
        early_stopping_method="generate"
    )
    
    print("\n" + "="*60)
    print("Welcome to the Family Docs Agent!")
    print("Ask me anything about your documents:")
    print("  Examples:")
    print("  - 'Give me SGPA and Roll No from Sem-2'")
    print("  - 'What details are in the medical report?'")
    print("  - 'Show me academic records'")
    print("  - 'Download Sem-2.pdf'")
    print("\nType 'exit' or 'quit' to leave")
    print("="*60 + "\n")
    
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("\nGoodbye! Thank you for using Family Docs Agent.")
            break
        
        if not user_input:
            print("Please enter a question or command.")
            continue
        
        try:
            print("\n⏳ Processing your request...\n")
            response = agent_executor.invoke({"input": user_input})
            print("\n" + "="*60)
            print("Agent Response:")
            print("="*60)
            print(response["output"])
            print("="*60)
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ Error occurred: {error_msg}")
            print("\nPlease try again or check if:")
            print("- AWS credentials are configured")
            print("- Redis connection is available")
            print("- Documents have been indexed")

if __name__ == "__main__":
    main()