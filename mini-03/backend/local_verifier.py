from sentence_transformers import SentenceTransformer, util
import sqlite3
import os
import torch

# Initialize model (downloads on first run, cached afterwards)
# 'all-MiniLM-L6-v2' is small (~80MB) and fast
print("Loading Local AI Model (this may take a moment on first run)...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded successfully.")

# Database Config
DB_FILE = "claims.db"
knowledge_base = []
kb_embeddings = None

def get_model_status():
    """Returns the current status of the AI model."""
    if kb_embeddings is None:
        return {"status": "loading", "facts_loaded": 0}
    return {
        "status": "active", 
        "facts_loaded": len(knowledge_base),
        "model_type": "Sentence-BERT (Local)"
    }

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the SQL database and create tables if they don't exist."""
    print(f"Initializing SQL Database: {DB_FILE}")
    conn = get_db_connection()
    c = conn.cursor()
    # Create Facts Table
    c.execute('''CREATE TABLE IF NOT EXISTS facts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  text TEXT UNIQUE,
                  verdict TEXT,
                  reasoning TEXT)''')
                  
    # --- CYBER SECURITY TABLES ---
    c.execute('''CREATE TABLE IF NOT EXISTS trusted_sources
                 (id INTEGER PRIMARY KEY, domain TEXT UNIQUE, trust_score INTEGER)''')
                 
    c.execute('''CREATE TABLE IF NOT EXISTS blacklisted_sources
                 (id INTEGER PRIMARY KEY, domain TEXT UNIQUE, risk_level INTEGER)''')
                 
    c.execute('''CREATE TABLE IF NOT EXISTS request_logs
                 (id INTEGER PRIMARY KEY, ip_address TEXT, timestamp REAL)''')
    
    # Seed Initial Trusted Sources
    c.execute("INSERT OR IGNORE INTO trusted_sources (domain, trust_score) VALUES (?, ?)", ('nasa.gov', 100))
    c.execute("INSERT OR IGNORE INTO trusted_sources (domain, trust_score) VALUES (?, ?)", ('who.int', 100))
    c.execute("INSERT OR IGNORE INTO trusted_sources (domain, trust_score) VALUES (?, ?)", ('bbc.com', 90))
    c.execute("INSERT OR IGNORE INTO trusted_sources (domain, trust_score) VALUES (?, ?)", ('reuters.com', 95))
    
    # Seed Initial Blacklist
    c.execute("INSERT OR IGNORE INTO blacklisted_sources (domain, risk_level) VALUES (?, ?)", ('fakenews.com', 100))
    c.execute("INSERT OR IGNORE INTO blacklisted_sources (domain, risk_level) VALUES (?, ?)", ('conspiracy-theories.net', 100))
    
    conn.commit()
    
    # Check if empty, if so, seed it
    c.execute('SELECT count(*) FROM facts')
    if c.fetchone()[0] == 0:
        seed_db(conn)
    
    conn.close()

def seed_db(conn):
    """Populate database with initial facts."""
    print("Seeding database with default knowledge...")
    initial_facts = [
        ("Water boils at 100 degrees Celsius at sea level.", "True", "Scientific consensus confirms that the boiling point of water is 100°C at 1 atm pressure."),
        ("The Earth is flat.", "False", "Extensive satellite imagery, physics, and exploration confirm the Earth is an oblate spheroid."),
        ("Humans have landed on Mars.", "False", "As of 2024, humans have sent rovers to Mars, but no humans have landed there yet."),
        ("The Great Wall of China is visible from space with the naked eye.", "False", "NASA astronauts have confirmed that the Great Wall is generally not visible to the naked eye from low Earth orbit without aid."),
        ("Honey never spoils.", "True", "Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still edible."),
        ("Vaccines cause autism.", "False", "Multiple large-scale scientific studies have found no link between vaccines and autism. The original study suggesting this was fraudulent."),
        ("Goldfish have a three-second memory.", "False", "Research shows goldfish can remember things for months and can be trained to respond to light and sound."),
        ("Lightning never strikes the same place twice.", "False", "Lightning hits tall buildings and trees many times. The Empire State Building is hit about 25 times a year."),
        ("Humans use only 10% of their brains.", "False", "Brain scans show activity across the entire brain, even during sleep. This is a common myth."),
        ("Climate change is influenced by human activity.", "True", "99% of climate scientists agree that burning fossil fuels and deforestation are driving global warming."),
        ("5G causes COVID-19.", "False", "COVID-19 is caused by a virus (SARS-CoV-2). Radio waves from 5G towers cannot create or spread viruses."),
        ("The Eiffel Tower can grow taller in the summer.", "True", "Due to thermal expansion of the iron, the Eiffel Tower can grow by up to 15 cm (6 inches) in hot weather.")
    ]
    
    c = conn.cursor()
    c.executemany('INSERT INTO facts (text, verdict, reasoning) VALUES (?, ?, ?)', initial_facts)
    conn.commit()
    print("Database seeded successfully.")

def load_knowledge_base():
    global knowledge_base, kb_embeddings
    
    # Ensure DB exists
    init_db()
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM facts')
    rows = c.fetchall()
    
    # Convert rows to dict list for compatibility
    knowledge_base = [dict(row) for row in rows]
    conn.close()
    
    if not knowledge_base:
        print("Database is empty!")
        return

    # Pre-compute embeddings for all facts in DB
    texts = [fact['text'] for fact in knowledge_base]
    kb_embeddings = model.encode(texts, convert_to_tensor=True)
    print(f"Loaded {len(knowledge_base)} facts from SQL Database into memory.")

# Initial load
load_knowledge_base()

def verify_locally(claim_text, threshold=0.5):
    """
    Verifies a claim by finding the most similar fact in the knowledge base.
    Threshold: Minimum similarity score (0 to 1) to consider it a "match".
    """
    if not knowledge_base or kb_embeddings is None:
        return {
            "verdict": "Uncertain",
            "confidence": 0.0,
            "reasoning": "System Offline: Knowledge base not loaded."
        }

    # Encode user claim
    claim_embedding = model.encode(claim_text, convert_to_tensor=True)

    # Compute cosine similarity
    cosine_scores = util.cos_sim(claim_embedding, kb_embeddings)[0]

    # Find closest match
    best_score = float(torch.max(cosine_scores))
    best_idx = int(torch.argmax(cosine_scores))

    match_fact = knowledge_base[best_idx]
    
    print(f"Claim: '{claim_text}' matched with '{match_fact['text']}' (Score: {best_score:.4f})")

    if best_score < threshold:
        return {
            "verdict": "Uncertain",
            "confidence": round(best_score * 100, 1),
            "reasoning": "No matching facts found in the local knowledge base."
        }
    
    # If the stored fact is "False" (e.g. "Earth is flat" -> False),
    # and the user says "Earth is flat" (high match), then the verdict for the user's claim is "False".
    # BUT, if the stored fact is "True" (e.g. "Water boils at 100C" -> True),
    # and user says "Water boils at 100C", verdict is "True".
    # This logic assumes the DB contains CLAIMS and their Truth Value.
    
    return {
        "verdict": match_fact['verdict'],
        "confidence": round(best_score * 100, 1),
        "reasoning": f"Matched Claim: '{match_fact['text']}'\n\nReasoning: {match_fact['reasoning']}"
    }

def verify_against_context(claim_text, context_sentences):
    """
    Compares the claim against a list of sentences (context) and finds the best semantic match.
    Used for verifying against "Live Evidence" (like Wikipedia).
    """
    if not context_sentences:
        return None
        
    # Encode claim
    claim_em = model.encode(claim_text, convert_to_tensor=True)
    
    # Encode all context sentences
    context_em = model.encode(context_sentences, convert_to_tensor=True)
    
    # Compute scores
    scores = util.cos_sim(claim_em, context_em)[0]
    
    best_score = float(torch.max(scores))
    best_idx = int(torch.argmax(scores))
    
    best_sentence = context_sentences[best_idx]
    
    # Heuristic for Truth (Simple Similarity Threshold)
    # If high match -> Likely True
    # If medium match -> Related but Uncertain
    # If low match -> False/Unrelated
    
    verdict = "Uncertain"
    if best_score > 0.65:
        verdict = "True"
    elif best_score < 0.25:
        verdict = "False"
        
    return {
        "verdict": verdict,
        "confidence": round(best_score * 100, 1),
        "evidence": best_sentence
    }

import torch
