# ============================================================
# LangSmith smoke test (LOCAL DEV — Personal Access Token)
# ============================================================

import os
import json
import boto3


def load_langsmith_key_from_secrets():
    secret_name = "dev/python/api"
    region_name = "eu-west-1"

    client = boto3.client("secretsmanager", region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)

    secret_string = response.get("SecretString")
    secret_json = json.loads(secret_string)

    return secret_json["LANGCHAIN_API_KEY"]


# ---- ENV VARS (set before import) ----
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "ai-document-agent-dev"
os.environ["LANGCHAIN_ENDPOINT"] = "https://eu.api.smith.langchain.com"
os.environ["LANGSMITH_ENDPOINT"] = "https://eu.api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = load_langsmith_key_from_secrets()

# ---- Import AFTER env vars ----
from langsmith import traceable


@traceable(
    name="langsmith_smoke_test",
    tags=["smoke-test", "local-vscode"]
)
def test_langsmith():
    return {
        "status": "ok",
        "message": "LangSmith integration is working from VSCode",
        "environment": "local"
    }


if __name__ == "__main__":
    print("🚀 Running LangSmith smoke test...")
    print("✅ Result:", test_langsmith())