import plan_generator


# ------------------------------------------------------------
# SIMPLE RUNNER
# ------------------------------------------------------------
def run_test_case(question: str):
    print("\n" + "=" * 80)
    print("User Question:")
    print(question)
    print("-" * 80)

    steps = plan_generator.generate_plan(question)

    print("Final Planner Output:")
    print(steps)
    print("=" * 80)


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
if __name__ == "__main__":
    print("\n🔵 Running Planner Visual Tests...\n")

    # ---------------------------------------------------------
    # TEST 1 — CONTENT ONLY
    # ---------------------------------------------------------
    run_test_case(
        "Can you please share the details from Sem-1.pdf?"
    )

    # ---------------------------------------------------------
    # TEST 2 — DOWNLOAD ONLY
    # ---------------------------------------------------------
    run_test_case(
        "Please give me the download link for Sem-1.pdf"
    )

    # ---------------------------------------------------------
    # TEST 3 — DISCOVERY ONLY
    # ---------------------------------------------------------
    run_test_case(
        "Show me all available documents"
    )

    # ---------------------------------------------------------
    # TEST 4 — CONTENT + DOWNLOAD (CRITICAL)
    # ---------------------------------------------------------
    run_test_case(
        "Can you please share me the semester 1 content document and then provide download link so that I can just click the link and download"
    )

    # ---------------------------------------------------------
    # TEST 5 — FREE-FORM / NATURAL LANGUAGE
    # ---------------------------------------------------------
    run_test_case(
        "I want to understand my semester 3 results and keep the file for later"
    )

    # ---------------------------------------------------------
    # TEST 6 — VERY SHORT / AMBIGUOUS
    # ---------------------------------------------------------
    run_test_case(
        "Sem 2 pdf"
    )

    # ---------------------------------------------------------
    # TEST 7 — CASUAL CHAT STYLE (WHATSAPP-LIKE)
    # ---------------------------------------------------------
    run_test_case(
        "hey can you send me sem 4 marks and also the file pls"
    )

    # ---------------------------------------------------------
    # TEST 8 — LISTING VARIATION
    # ---------------------------------------------------------
    run_test_case(
        "What all documents do you have?"
    )


    # ---------------------------------------------------------
    # TEST 9 — 
    # ---------------------------------------------------------
    run_test_case(
        "Can you please compare from all semester academic marsheet where SGPA is maximum and share the details about that doucument and give a one copy download link of that document."
    )

    # ---------------------------------------------------------
    # TEST 10 — 
    # ---------------------------------------------------------
    run_test_case(
        "Can you please compare from all semester academic marsheet where SGPA is maximum and share the details about that doucument and give a one copy link of that document."
    )

    # ---------------------------------------------------------
    # TEST 11 — 
    # ---------------------------------------------------------
    run_test_case(
        "Can you please give me the medicine name as SOS mentioned and prescribed by Reliable diagnostic by Doctor Poushali for Aishiki? And provide a download link?"
    )


    run_test_case(
        "Can you please share the latest 3 HSBC Transaction from you documents?"
    )

    print("\n🔵 Planner visual tests completed.\n")