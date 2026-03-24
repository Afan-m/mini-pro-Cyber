from gemini_learner import verify_with_gemini
import os
from dotenv import load_dotenv

# Force load .env to ensure key is present
load_dotenv()

print("--- Testing Gemini API Connection ---")
api_key = os.getenv("GOOGLE_API_KEY")
print(f"API Key present: {'Yes' if api_key else 'No'}")

if not api_key:
    print("CRITICAL: No API Key found in environment variables.")
    exit(1)

test_claim = "The moon is made of green cheese."
print(f"\nSending Test Claim: '{test_claim}'")

try:
    result = verify_with_gemini(test_claim)
    
    if result:
        print("\n[SUCCESS] API Response Received:")
        print(f"Verdict: {result['verdict']}")
        print(f"Reasoning: {result['reasoning'][:100]}...")
    else:
        print("\n[FAILURE] API returned None. Check logs or quota.")

except Exception as e:
    print(f"\n[ERROR] Exception occurred: {e}")
