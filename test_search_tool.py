# test_search_tool.py

from tools.search_documents import search_documents_tool


def run_test():
    print("\n================ TEST: search_documents_tool ================\n")

    result = search_documents_tool.run({
        "input": {
            "query": "Share the top 3 transactions from HSBC statement pdf?",
            "top_k": 5
        }
    })

    print("RAW TOOL OUTPUT:")
    print("------------------------------------------------------------")
    print(result)
    print("------------------------------------------------------------\n")


if __name__ == "__main__":
    run_test()
