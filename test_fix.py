import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from backend.crew_orchestrator import get_policy_crew

# Read sample policy
with open('sample_policy.txt', 'r') as f:
    policy_text = f.read()

print("=== Testing Fixed Analysis ===\n")

# Test free tier
print("1. Testing FREE tier analysis...")
crew = get_policy_crew()
result = crew.analyze_policy(policy_text, premium=False)

print(f"\nFREE TIER RESULT:")
print(f"  Success: {result.get('success')}")
print(f"  Score: {result.get('score')}%")
print(f"  Strengths: {len(result.get('strengths', []))}")
print(f"  Gaps: {len(result.get('gaps', []))}")
print(f"  Sections found: {len(result.get('sections_found', []))}")

if result.get('strengths'):
    print(f"\n  First 3 strengths:")
    for s in result['strengths'][:3]:
        print(f"    - {s}")

if result.get('gaps'):
    print(f"\n  First 3 gaps:")
    for g in result['gaps'][:3]:
        print(f"    - {g}")

print("\n" + "="*50)

# Test premium tier
print("\n2. Testing PREMIUM tier analysis...")
result_premium = crew.analyze_policy(policy_text, premium=True)

print(f"\nPREMIUM TIER RESULT:")
print(f"  Success: {result_premium.get('success')}")
print(f"  Score: {result_premium.get('score')}%")
print(f"  Has recommendations: {bool(result_premium.get('recommendations'))}")
if result_premium.get('recommendations'):
    print(f"  Number of recommendations: {len(result_premium['recommendations'])}")
    print(f"\n  First recommendation:")
    rec = result_premium['recommendations'][0]
    print(f"    Control: {rec.get('control')}")
    print(f"    Priority: {rec.get('priority')}")
    print(f"    Details: {rec.get('details')[:100]}...")
