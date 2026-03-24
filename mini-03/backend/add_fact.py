import sqlite3
import os

DB_FILE = "claims.db"

def add_fact():
    print("\n--- ADD NEW VERIFIED FACT ---")
    text = input("Enter the Claim/Fact Text: ").strip()
    if not text:
        print("Error: Text cannot be empty.")
        return

    print("\nVerdict Options: True, False, Uncertain")
    verdict = input("Enter Verdict: ").strip()
    
    reasoning = input("\nEnter Reasoning/Explanation: ").strip()
    if not reasoning:
        print("Error: Reasoning cannot be empty.")
        return

    # Connect to DB
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        # Insert
        c.execute('INSERT INTO facts (text, verdict, reasoning) VALUES (?, ?, ?)', (text, verdict, reasoning))
        conn.commit()
        conn.close()
        print(f"\n[SUCCESS] Fact added to database!")
        print("IMPORTANT: You must restart the backend server for this new fact to be recognized by the AI.")
        
    except Exception as e:
        print(f"Error adding to database: {e}")

if __name__ == "__main__":
    while True:
        add_fact()
        cont = input("\nAdd another? (y/n): ").lower()
        if cont != 'y':
            break
