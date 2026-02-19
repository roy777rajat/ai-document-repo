#!/usr/bin/env python3
"""
Test script to verify multi-semester query handling
"""

import sys
import os

# Add utils to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_multi_semester():
    """Test multi-semester query handling"""

    print("=" * 70)
    print("🧪 Testing Multi-Semester Query Handling")
    print("=" * 70)

    # Import the tool directly
    from tools.search_documents import search_documents_tool

    # Test multi-semester query
    query = 'query="Sem-1 and Sem-4 SGPA", top_k=5'

    print(f"\n📋 Tool Input: {query}")
    print("-" * 70)

    try:
        result = search_documents_tool(query)

        print("\n✅ Tool Response (first 2000 chars):")
        print("-" * 70)
        print(result[:2000])
        print("-" * 70)

        # Check if it found multiple documents
        if "Found" in result:
            import re
            match = re.search(r"Found (\d+) relevant document", result)
            if match:
                doc_count = int(match.group(1))
                print(f"\n📊 Found {doc_count} documents")

                # Extract document names
                doc_names = re.findall(r"【Document \d+】 ([^\n]+)", result)
                print("Document names found:")
                for name in doc_names:
                    print(f"  - {name}")

                # Check if extraction mentions both semesters
                if "Sem-1" in result and "Sem-4" in result:
                    print("✅ Extraction mentions both Sem-1 and Sem-4")
                else:
                    print("⚠️  Extraction may not cover both semesters")

    except Exception as e:
        print(f"❌ Error running test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_multi_semester()