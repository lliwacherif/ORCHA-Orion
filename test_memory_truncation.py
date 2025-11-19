#!/usr/bin/env python3
"""
Test script for memory truncation functionality.
"""

def truncate_memory_to_tokens(memory_content: str, max_tokens: int = 1000) -> str:
    """
    Truncate memory content to approximately max_tokens, keeping the LATEST content.
    Uses a rough approximation: 1 token ≈ 4 characters for English text.
    """
    if not memory_content:
        return memory_content
    
    # Rough approximation: 1 token ≈ 4 characters
    max_chars = max_tokens * 4
    
    if len(memory_content) <= max_chars:
        # No truncation needed
        return memory_content
    
    # Truncate from the beginning, keep the latest (end) content
    # Add indicator that content was truncated
    truncated = "..." + memory_content[-max_chars:]
    
    return truncated

# Test cases
print("=" * 60)
print("Memory Truncation Test")
print("=" * 60)

# Test 1: Short memory (no truncation)
short_memory = "User prefers formal communication. Works in insurance. Based in Paris."
result1 = truncate_memory_to_tokens(short_memory, max_tokens=1000)
print(f"\n✅ Test 1: Short memory (no truncation)")
print(f"   Original: {len(short_memory)} chars")
print(f"   Result:   {len(result1)} chars")
print(f"   Truncated: {result1 != short_memory}")
assert result1 == short_memory, "Short memory should not be truncated"

# Test 2: Long memory (truncation needed)
long_memory = "A" * 10000  # 10,000 characters
result2 = truncate_memory_to_tokens(long_memory, max_tokens=1000)
max_expected = 1000 * 4 + 3  # +3 for "..."
print(f"\n✅ Test 2: Long memory (truncation needed)")
print(f"   Original: {len(long_memory)} chars")
print(f"   Result:   {len(result2)} chars")
print(f"   Max expected: {max_expected} chars")
print(f"   Starts with '...': {result2.startswith('...')}")
assert result2.startswith("..."), "Truncated memory should start with '...'"
assert len(result2) <= max_expected, f"Result should be <= {max_expected} chars"

# Test 3: Realistic memory scenario
realistic_memory = """User prefers formal communication style and detailed explanations. Works in the insurance industry, specifically in risk assessment and underwriting. Interested in AI applications for document processing and claims automation. Based in Paris, France. Prefers responses in French when discussing technical insurance topics. Has expressed interest in machine learning models for fraud detection. Currently working on a project involving OCR integration for processing insurance documents. Appreciates structured data and clear explanations.""" * 10
result3 = truncate_memory_to_tokens(realistic_memory, max_tokens=1000)
print(f"\n✅ Test 3: Realistic memory")
print(f"   Original: {len(realistic_memory)} chars (~{len(realistic_memory)//4} tokens)")
print(f"   Result:   {len(result3)} chars (~{len(result3)//4} tokens)")
print(f"   Truncated: {result3 != realistic_memory}")
print(f"   Preview (last 100 chars): ...{result3[-100:]}")

# Test 4: Exactly at limit
exact_memory = "A" * 4000  # Exactly 1000 tokens
result4 = truncate_memory_to_tokens(exact_memory, max_tokens=1000)
print(f"\n✅ Test 4: Exact limit (4000 chars = ~1000 tokens)")
print(f"   Original: {len(exact_memory)} chars")
print(f"   Result:   {len(result4)} chars")
print(f"   No truncation: {result4 == exact_memory}")
assert result4 == exact_memory, "Exact limit should not be truncated"

# Test 5: Empty memory
empty_memory = ""
result5 = truncate_memory_to_tokens(empty_memory, max_tokens=1000)
print(f"\n✅ Test 5: Empty memory")
print(f"   Result: '{result5}'")
assert result5 == "", "Empty memory should remain empty"

print("\n" + "=" * 60)
print("✅ All tests passed!")
print("=" * 60)
print("\n📊 Summary:")
print(f"   Max tokens: 1000")
print(f"   Max chars: {1000 * 4}")
print(f"   Strategy: Keep LATEST content (truncate from beginning)")
print(f"   Indicator: Adds '...' prefix when truncated")




