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
You are a helpful assistant for managing family documents. Use the available tools to answer questions about documents, search for information, or provide downloads.

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}
""")
    
    # Create agent
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
    
    print("Welcome to the Family Docs Agent. Ask me anything about your documents.")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        
        try:
            response = agent_executor.invoke({"input": user_input})
            print("Agent:", response["output"])
        except Exception as e:
            print("Error:", str(e))

if __name__ == "__main__":
    main()