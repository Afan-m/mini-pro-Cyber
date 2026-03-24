import wikipedia
import sqlite3
import random

DB_FILE = "claims.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def learn_new_fact(text, verdict="True", reasoning="Source: Wikipedia"):
    """
    Saves a new fact to the local database (The 'Learning' Step).
    """
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # specific check to avoid duplicates
        c.execute("SELECT id FROM facts WHERE text = ?", (text,))
        if c.fetchone():
            conn.close()
            return False # Already learned
            
        c.execute("INSERT INTO facts (text, verdict, reasoning) VALUES (?, ?, ?)", 
                 (text, verdict, reasoning))
        conn.commit()
        conn.close()
        print(f"[LEARNING] Learned new fact: {text[:50]}...")
        return True
    except Exception as e:
        print(f"Learning Error: {e}")
        return False

from local_verifier import verify_against_context

def search_and_learn(query):
    """
    Searches Wikipedia, extracts sentences, and verifies the claim against them.
    Saves the *BEST* evidence to the database.
    """
    try:
        print(f"Searching Wikipedia for: {query}")
        search_results = wikipedia.search(query, results=1)
        
        if not search_results:
            return None
            
        page_title = search_results[0]
        # Fetch more content to ensure we find the answer
        summary = wikipedia.summary(page_title, sentences=5)
        
        if not summary:
            return None
            
        # Split into sentences (basic)
        sentences = [s.strip() for s in summary.split('.') if len(s) > 10]
        
        if not sentences:
            return None
            
        # --- VERIFICATION STEP ---
        # Instead of just returning the whole text, we check:
        # "Which sentence actually proves/disproves this?"
        verification = verify_against_context(query, sentences)
        
        if not verification:
            return None
            
        best_evidence = verification['evidence']
        verdict = verification['verdict']
        confidence = verification['confidence']
        
        # AUTO-LEARN: Save specific evidence
        fact_text = f"{page_title}: {best_evidence}"
        reasoning = f"Verified against Wikipedia: {best_evidence}"
        
        learn_new_fact(fact_text, verdict, reasoning)
        
        return {
            "verdict": "True" if verdict == "True" else "Uncertain", # Bias towards trusted source
            "confidence": confidence,
            "reasoning": f"Analysis of Verified Source ({page_title}):\n\"{best_evidence}\"\n\n(Fact saved to system memory)"
        }
        
    except wikipedia.exceptions.DisambiguationError as e:
        return {
            "verdict": "Uncertain",
            "confidence": 0.0,
            "reasoning": f"Topic ambiguous. Did you mean: {', '.join(e.options[:3])}?"
        }
    except Exception as e:
        print(f"Wiki Error: {e}")
        return None
