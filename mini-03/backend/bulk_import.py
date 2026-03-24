import sqlite3
import json
import os

DB_FILE = "claims.db"
IMPORT_FILE = "import_facts.json"

def bulk_import():
    if not os.path.exists(IMPORT_FILE):
        print(f"Error: {IMPORT_FILE} not found.")
        return

    try:
        with open(IMPORT_FILE, 'r') as f:
            new_facts = json.load(f)
            
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        count = 0
        for fact in new_facts:
            # check if text is dummy example
            if fact['text'] == "Example Fact 2":
                continue
                
            # Optional: Check duplicates
            c.execute("SELECT id FROM facts WHERE text = ?", (fact['text'],))
            if c.fetchone():
                print(f"Skipping duplicate: {fact['text'][:30]}...")
                continue
                
            c.execute('INSERT INTO facts (text, verdict, reasoning) VALUES (?, ?, ?)', 
                     (fact['text'], fact['verdict'], fact['reasoning']))
            count += 1
            
        conn.commit()
        conn.close()
        print(f"\n[SUCCESS] Imported {count} new facts from {IMPORT_FILE} into the database.")
        print("REMINDER: Restart the backend server to apply changes.")
        
    except json.JSONDecodeError:
        print(f"Error: {IMPORT_FILE} is not valid JSON. Please check the syntax.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    bulk_import()
