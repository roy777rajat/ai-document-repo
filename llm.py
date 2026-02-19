import json
import os
import boto3
from botocore.exceptions import NoRegionError

# Respect AWS_REGION environment variable; default to eu-west-1 if not set
AWS_REGION = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "eu-west-1"

try:
    bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)
except NoRegionError:
    raise RuntimeError("AWS region not configured. Set AWS_REGION environment variable.")

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