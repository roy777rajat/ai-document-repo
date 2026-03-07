import requests
import time
import csv
from datetime import datetime

API_URL = "http://localhost:8000/api/v1/query"


# ---------------------------------------------------
# TEST SUITE
# ---------------------------------------------------

TEST_QUERIES = [

# Document discovery
"Please share whatever the document list you have",
"Share all the documents metadata list",
"What documents are available in the system",

# Downloads
"Download the file Sem-1.pdf",
"Provide the download link for Sem-3.pdf",
"Download link for Latest Increment Letter.pdf",

# Document ID
"Download document with id 3e91f6c9-642f-415a-bfb8-2d3cff0a9b61",

# Medical
"What medicine was prescribed by Doctor Poushali for Aishiki",
"Share SOS medicine mentioned in Reliable diagnostic prescription for Aishiki",
"Provide details from Aishiki Reliable prescription document",

# Semester
"Share details from Sem-1.pdf",
"I want to understand my semester 3 results",
"Which semester has lowest SGPA for Rajat",

# Financial
"Share top 3 transactions from HSBC statement",
"What are the latest 3 HSBC transactions",

# Insurance
"Share insurance details for vehicle registration WB02AK5172",
"Vehicle insurance policy details for car WB02AK5172",

# Employment
"Summarize  offer letter",
"Share details from  Latest Increment Letter",

# Identity
"Show passport details",
"Share PAN card details",

# Complex
"Find semester document where Rajat got lowest SGPA and give download link",
"Show HSBC transactions and allow download of statement",
"Find insurance policy document and provide download link",

# Edge
"Sem-1",
"WB02AK5172",
"HSBC",
"Insurance",
"Prescription"

]


# ---------------------------------------------------
# RUN TESTS
# ---------------------------------------------------

results = []

print("\n🚀 Starting Agent Evaluation\n")

for i, question in enumerate(TEST_QUERIES, start=1):

    print(f"\nTest {i}: {question}")

    payload = {"question": question}

    start = time.time()

    try:

        response = requests.post(API_URL, json=payload)

        latency = round(time.time() - start, 3)

        answer = response.json().get("answer", "")

        print("Latency:", latency, "seconds")

        results.append({
            "test_id": i,
            "question": question,
            "latency_seconds": latency,
            "answer": answer[:500]  # truncate for csv
        })

    except Exception as e:

        print("ERROR:", str(e))

        results.append({
            "test_id": i,
            "question": question,
            "latency_seconds": "ERROR",
            "answer": str(e)
        })


# ---------------------------------------------------
# SAVE CSV REPORT
# ---------------------------------------------------

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

filename = f"agent_eval_report_{timestamp}.csv"

with open(filename, "w", newline="", encoding="utf-8") as f:

    writer = csv.DictWriter(
        f,
        fieldnames=["test_id", "question", "latency_seconds", "answer"]
    )

    writer.writeheader()

    writer.writerows(results)


print("\n✅ Evaluation Completed")
print("Report saved to:", filename)