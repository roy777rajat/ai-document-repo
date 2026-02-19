import os
import importlib.util
from langchain_aws import ChatBedrock
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import ChatPromptTemplate


def load_tools():
    tools_dir = os.path.join(os.path.dirname(__file__), 'tools')
    tools = []

    for filename in os.listdir(tools_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3]
            spec = importlib.util.spec_from_file_location(module_name, os.path.join(tools_dir, filename))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                # LangChain @tool functions expose .name and .description
                if hasattr(attr, 'name') and hasattr(attr, 'description') and callable(getattr(attr, 'run', None)):
                    tools.append(attr)

    return tools


def run_agent(user_input: str) -> str:
    """Run the same agent logic as `main.py` and return the final answer string.

    This is intentionally synchronous and blocking to match the console usage.
    """
    tools = load_tools()

    llm = ChatBedrock(
        model_id=os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-haiku-20240307-v1:0'),
        region_name=os.getenv('AWS_REGION', 'eu-west-1'),
        model_kwargs={"temperature": float(os.getenv('MODEL_TEMPERATURE', '0.0'))}
    )

    prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant for managing family documents. Use the available tools to answer questions.

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

Begin!

Question: {input}
Thought:{agent_scratchpad}
""")

    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=int(os.getenv('AGENT_MAX_ITER', '3')),
        early_stopping_method='generate'
    )

    response = agent_executor.invoke({"input": user_input})
    return response.get('output', '')
