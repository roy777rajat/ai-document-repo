#!/usr/bin/env python3
"""
Test script to check what documents are available in the system
"""

import sys
import os

# Add utils to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_broad_search():
    """Test broader search to see all available documents"""

    print("=" * 70)
    print("🧪 Testing Broad Search for SGPA Documents")
    print("=" * 70)

    # Import the tool directly
    from tools.search_documents import search_documents_tool

    # Test broader search
    query = 'query="SGPA", top_k=10'

    print(f"\n📋 Tool Input: {query}")
    print("-" * 70)

    try:
        result = search_documents_tool(query)

        print("\n✅ Tool Response:")
        print("-" * 70)
        print(result)
        print("-" * 70)

        # Count documents found
        if "Found" in result:
            import re
            match = re.search(r"Found (\d+) relevant document", result)
            if match:
                doc_count = int(match.group(1))
                print(f"\n📊 Found {doc_count} documents")

                # Extract document names
                import re
                doc_names = re.findall(r"【Document \d+】 ([^\n]+)", result)
                print("Document names found:")
                for name in doc_names:
                    print(f"  - {name}")

    except Exception as e:
        print(f"❌ Error running test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_broad_search()