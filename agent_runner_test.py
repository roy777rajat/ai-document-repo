"""
Manual test runner for agent_runner.py

Run:
    python agent_runner_test.py

Purpose:
- Validate planner → orchestrator → agent flow
- Ensure NO infinite loops
- Verify multi-step execution works
"""

from agent_runner import run_agent
import time


def run_test_case(question: str):
    print("\n" + "=" * 80)
    print("🧪 TEST QUESTION")
    print("=" * 80)
    print(question)

    start = time.perf_counter()

    try:
        answer = run_agent(question)
    except Exception as e:
        print("\n❌ ERROR DURING EXECUTION")
        print(str(e))
        return

    end = time.perf_counter()
    elapsed_ms = round((end - start) * 1000, 2)

    print("\n" + "-" * 80)
    print("✅ AGENT OUTPUT")
    print("-" * 80)
    print(answer)

    print("\n⏱️ RESPONSE TIME:", elapsed_ms, "ms")
    print("=" * 80 + "\n")


if __name__ == "__main__":

    print("\n🚀 STARTING AGENT RUNNER TESTS\n")

#     # ---------------------------------------------------------
#     # TEST 1 — CONTENT ONLY
#     # ---------------------------------------------------------
    run_test_case(
        "Can you please share the details from Sem-1.pdf?"
    )

#     # ---------------------------------------------------------
#     # TEST 2 — DOWNLOAD ONLY
#     # ---------------------------------------------------------
    run_test_case(
        "Please give me the download link for Sem-1.pdf"
    )

#    # ---------------------------------------------------------
#    # TEST 3 — DISCOVERY ONLY
#    # ---------------------------------------------------------
    run_test_case(
        "Show me all available documents"
    )

#     # ---------------------------------------------------------
#     # TEST 4 — CONTENT + DOWNLOAD (CRITICAL TEST)
#     # ---------------------------------------------------------
    run_test_case(
        "Can you please share me the semester 1 content document and then provide download link so that I can just click the link and download"
    )

    # # ---------------------------------------------------------
    # # TEST 5 — FREE-FORM / NATURAL LANGUAGE (REALISTIC)
    # # ---------------------------------------------------------
    run_test_case(
        "I want to understand my semester 3 results and keep the file for later"
    )


    # ---------------------------------------------------------
    # TEST 6 — FREE-FORM / NATURAL LANGUAGE (REALISTIC)
    # ---------------------------------------------------------
    run_test_case(
        "Can you please share the latest 3 HSBC Transaction from you documents?"
    )

    # ---------------------------------------------------------
    # TEST 7 — Handle multiple doc
    # ---------------------------------------------------------
    run_test_case(
        "can you please give the adhar card , Pan Card, Offer letter salary amount of Rajat Roy"
    )

    print("🎉 ALL TESTS COMPLETED")