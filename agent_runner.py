# agent_runner.py

import os
import json
import boto3
import uuid
import time
from typing import List, Dict, Any

# ============================================================
# 🔴 CHANGED: LangSmith Secrets + Env Bootstrap (AUTHORITATIVE)
# ============================================================

def _load_langsmith_key_from_secrets():
    """
    Load LangSmith API key from AWS Secrets Manager.
    MUST be called before importing langsmith.
    """
    secret_name = "dev/python/api"
    region_name = "eu-west-1"

    client = boto3.client("secretsmanager", region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)

    secret_string = response.get("SecretString")
    secret_json = json.loads(secret_string)

    return secret_json["LANGCHAIN_API_KEY"]


def _init_langsmith_env():
    """
    Initialize LangSmith exactly like the working smoke test.
    """
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "ai-document-agent-dev"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://eu.api.smith.langchain.com"
    os.environ["LANGSMITH_ENDPOINT"] = "https://eu.api.smith.langchain.com"
    os.environ["LANGCHAIN_API_KEY"] = _load_langsmith_key_from_secrets()


# 🔴 CRITICAL: init BEFORE importing langsmith
_init_langsmith_env()

# 🔴 Import AFTER env vars are set
from langsmith import traceable

# ============================================================
# 🔵 Planner
# ============================================================
from plan_generator import generate_plan

# ============================================================
# 🔵 Tools (DIRECT, ATOMIC)
# ============================================================
from tools.search_documents import search_documents_tool
from tools.download_document import download_document_tool
from tools.get_all_document_metadata import get_all_document_metadata_tool

# ============================================================
# 🔵 Tool Registry
# ============================================================
TOOL_REGISTRY = {
    "search_documents": search_documents_tool,
    "download_document": download_document_tool,
    "list_documents": get_all_document_metadata_tool,
}

# ============================================================
# 🔵 MAIN AGENT ENTRY (Planner → Executor)
# ============================================================

@traceable(
    name="run_agent",
    run_type="chain",
    tags=["production", "planner-executor"]
)
def run_agent(
    user_input: str,
    *,
    channel: str = "unknown",
    user_id: str = "anonymous"
) -> str:
    """
    Production-grade agent execution:
    - Planner decides WHAT steps to run
    - Executor runs steps strictly in order
    - NO ReAct
    """

    trace_id = str(uuid.uuid4())
    start_ts = time.perf_counter()

    print(f"\n🧠 TRACE_ID = {trace_id}")
    print("🧠 GENERATING PLAN")

    # --------------------------------------------------------
    # STEP 1: PLAN
    # --------------------------------------------------------
    plan = generate_plan(user_input)

    if not plan:
        return "❌ Unable to determine how to answer your question."

    print(f"🧠 EXECUTION PLAN → {plan}")

    outputs: List[str] = []
    context: Dict[str, Any] = {}

    # --------------------------------------------------------
    # STEP 2: EXECUTE PLAN
    # --------------------------------------------------------
    for step in plan:
        tool = TOOL_REGISTRY.get(step)

        if not tool:
            outputs.append(f"⚠️ Unknown step ignored: {step}")
            continue

        print(f"\n🟢 EXECUTING STEP → {step}")
        step_start = time.perf_counter()

        try:
            if step == "download_document":
                resolved = context.get("resolved_filenames", [])

                if not resolved:
                    outputs.append("❌ No authoritative document available for download.")
                    continue

                filename = resolved[0]
                assert filename in resolved, "FATAL: download document mismatch"

                result = tool.run(f'filename="{filename}"')
            else:
                # Rule: full user question always passed unchanged
                result = tool.run(user_input)

            if isinstance(result, dict):
                context.update(result)
                if "answer" in result:
                    outputs.append(result["answer"])
            else:
                outputs.append(result)

        except Exception as e:
            outputs.append(f"❌ Error executing {step}: {str(e)}")

        step_end = time.perf_counter()
        print(
            f"⏱️ STEP {step} completed in "
            f"{round((step_end - step_start) * 1000, 2)} ms"
        )

    # --------------------------------------------------------
    # STEP 3: FINAL RESPONSE
    # --------------------------------------------------------
    total_ms = round((time.perf_counter() - start_ts) * 1000, 2)

    final_answer = "\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n".join(outputs)

    followups = context.get("followup_questions", [])
    if followups:
        final_answer += "\n\n💡 You can also ask:\n"
        for q in followups:
            final_answer += f"- {q}\n"

    final_answer += f"\n⏱️ Response Time: {total_ms} ms"
    final_answer += f"\n🧵 Trace ID: {trace_id}"

    # 🔴 IMPORTANT: allow async trace flush
    time.sleep(1.5)

    return final_answer