import uuid
import time
from typing import List, Dict, Any

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
# 🔵 Tool Registry (EXTENSIBLE)
# ============================================================
TOOL_REGISTRY = {
    "search_documents": search_documents_tool,
    "download_document": download_document_tool,
    "list_documents": get_all_document_metadata_tool,
}


# ============================================================
# 🔵 MAIN AGENT ENTRY (Planner → Executor)
# ============================================================
def run_agent(user_input: str) -> str:
    """
    Production-grade agent execution:

    - Planner decides WHAT steps to run
    - Executor runs steps strictly in order
    - NO ReAct
    - NO dynamic step insertion
    - Executor manages execution DATA (context)
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

    # 🔵 EXECUTION CONTEXT (DATA FLOW ONLY)
    context: Dict[str, Any] = {}

    # --------------------------------------------------------
    # STEP 2: EXECUTE PLAN (STRICT ORDER)
    # --------------------------------------------------------
    for step in plan:
        tool = TOOL_REGISTRY.get(step)

        if not tool:
            outputs.append(f"⚠️ Unknown step ignored: {step}")
            continue

        print(f"\n🟢 EXECUTING STEP → {step}")
        step_start = time.perf_counter()

        try:
            # 🔥 TOOLS RECEIVE FULL QUESTION + CONTEXT
            if step == "download_document":
                filename = None
            if "resolved_filenames" in context and context["resolved_filenames"]:
                filename = context["resolved_filenames"][0]
                # Pass filename explicitly
                result = tool.run(f'filename="{filename}"')
            else:
                result = tool.run(user_input)

            # -------------------------------
            # CONTEXT MERGE (IF TOOL RETURNS DATA)
            # -------------------------------
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
    end_ts = time.perf_counter()
    total_ms = round((end_ts - start_ts) * 1000, 2)

    final_answer = "\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n".join(outputs)
    final_answer += f"\n\n⏱️ Response Time: {total_ms} ms"
    final_answer += f"\n🧵 Trace ID: {trace_id}"

    return final_answer