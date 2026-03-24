import requests
import json
import os
from dotenv import load_dotenv
from wiki_learner import learn_new_fact  # Reuse the DB saving logic

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

def verify_with_gemini(claim_text):
    """
    Asks Gemini to verify the claim.
    If successful, saves the result to the local database (Auto-Learning).
    """
    if not API_KEY:
        print("Error: GOOGLE_API_KEY not found.")
        return None

    print(f"Asking Gemini: {claim_text}")
    
    # Simple Prompt Engineering
    prompt = f"""
    You are a Fact Checking AI. Verify this claim: "{claim_text}"
    
    Rules:
    1. Status must be "True", "False", or "Uncertain".
    2. Provide a detailed explanation verification (minimum 50 words, maximum 150 words).
    3. Return RESPONSE AS RAW JSON ONLY. No markdown.
    
    Format:
    {{
        "verdict": "True/False",
        "reasoning": "Explanation here..."
    }}
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Gemini API Error {response.status_code}: {response.text}")
        response.raise_for_status()
        
        data = response.json()
        
        # Extract text from Gemini response structure
        # Response -> candidates[0] -> content -> parts[0] -> text
        text_response = data['candidates'][0]['content']['parts'][0]['text']
        
        # Clean up Markdown code blocks if present ( ```json ... ``` )
        clean_json = text_response.replace('```json', '').replace('```', '').strip()
        
        result = json.loads(clean_json)
        
        verdict = result.get('verdict', 'Uncertain')
        reasoning = result.get('reasoning', 'No reasoning provided.')
        
        # --- AUTO-LEARNING ---
        # Save to local DB so next time it's instant!
        # We save the "claim" as the key, so exact matches work instantly.
        db_text = claim_text
        db_reasoning = f"{reasoning}"
        
        learn_new_fact(db_text, verdict, db_reasoning)
        
        return {
            "verdict": verdict,
            "confidence": 98.0, # High confidence in Gemini
            "reasoning": f"AI Aanalysis (Gemini Pro):\n{reasoning}"
        }

    except Exception as e:
        print(f"Gemini Error: {e}")
        return None
