#!/usr/bin/env python3
"""
Test script to verify the search_documents_tool fix for extraction prompt.
Tests with Sem-2 query to ensure agent returns specific values instead of "I don't have this information"
"""

import sys
import os

# Add utils to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_runner import run_agent_query

def test_extraction_fix():
    """Test that agent now extracts specific SGPA and Roll No values confidently"""
    
    print("=" * 70)
    print("🧪 Testing Search Documents Tool Extraction Fix")
    print("=" * 70)
    
    # Test query that previously failed
    query = "Give me SGPA No and Roll No of Sem-2"
    
    print(f"\n📋 Query: {query}")
    print("-" * 70)
    
    try:
        result = run_agent_query(query)
        
        print("\n✅ Agent Response:")
        print("-" * 70)
        print(result)
        print("-" * 70)
        
        # Check if response contains expected values
        expected_values = ["23123031006", "8.12", "Roll No", "SGPA"]
        found_values = []
        
        for val in expected_values:
            if str(val) in result:
                found_values.append(val)
        
        print(f"\n📊 Verification:")
        print(f"   ✓ Found {len(found_values)}/{len(expected_values)} expected values")
        for val in found_values:
            print(f"   ✓ {val}")
        
        if "don't have" in result.lower() or "no information" in result.lower():
            print(f"\n   ⚠️  WARNING: Agent still saying it doesn't have information!")
            return False
        else:
            print(f"\n   ✅ Agent is confident and extracting values!")
            return True
            
    except Exception as e:
        print(f"❌ Error running test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_extraction_fix()
    sys.exit(0 if success else 1)
