import json
import boto3

bedrock = boto3.client("bedrock-runtime")

MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"

def call_claude_with_tools(messages, tools):
    """
    Calls Claude with tool calling support.
    """
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": messages,
        "max_tokens": 1000,
        "temperature": 0.0,
        "tools": tools
    }
    
    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body)
    )
    
    raw_output = response["body"].read()
    parsed = json.loads(raw_output)
    
    return parsed

def call_claude_simple(prompt):
    """
    Simple call for summarization.
    """
    wrapped_prompt = f"""
{prompt}

Respond with a well-formatted summary.
"""
    
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [{"role": "user", "content": wrapped_prompt}],
        "max_tokens": 1000,
        "temperature": 0.0
    }
    
    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body)
    )
    
    raw_output = response["body"].read()
    parsed = json.loads(raw_output)
    
    text = parsed["content"][0]["text"]
    return text