import re
import sqlite3
from urllib.parse import urlparse
import time

# --- Database for Trust/Block Lists ---
DB_FILE = "claims.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# --- 1. Source Credibility Checking ---
def check_source_credibility(text):
    """
    Extracts URLs from text and checks them against local White/Blacklists.
    Returns: (risk_score, details_list)
    """
    urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', text)
    if not urls:
        return 0, [] # No risk if no source provided

    risk_score = 0
    details = []
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for url in urls:
        try:
            domain = urlparse(url).netloc.lower()
            
            # Check Blacklist
            cursor.execute("SELECT risk_level FROM blacklisted_sources WHERE domain LIKE ?", (f"%{domain}%",))
            blacklist_match = cursor.fetchone()
            if blacklist_match:
                risk_score = 100
                details.append(f"CRITICAL: Link to blacklisted source detected ({domain})")
                continue

            # Check Whitelist
            cursor.execute("SELECT trust_score FROM trusted_sources WHERE domain LIKE ?", (f"%{domain}%",))
            whitelist_match = cursor.fetchone()
            if whitelist_match:
                trust = whitelist_match['trust_score']
                details.append(f"SAFE: Verified trusted source ({domain}) - Trust Score: {trust}")
                # trusted sources lower the risk
                risk_score -= 20 
            else:
                # Unknown source
                risk_score += 10
                details.append(f"WARNING: Unverified source link ({domain})")
                
        except Exception as e:
            print(f"URL Parse Error: {e}")

    conn.close()
    return max(0, min(100, risk_score)), details

# --- 2. Adversarial / Pattern Analysis ---
def detect_adversarial_text(text):
    """
    Analyzes text for 'spammy' or 'sensational' patterns common in fake news.
    """
    issues = []
    risk_score = 0
    
    # Check 1: Excessive Caps Lock (Shouting)
    caps_count = sum(1 for c in text if c.isupper())
    if len(text) > 20 and (caps_count / len(text) > 0.4):
        risk_score += 30
        issues.append("Suspicious Pattern: Excessive use of CAPS LOCK")

    # Check 2: Excessive Punctuation (!!! ???)
    if "!!" in text or "??" in text:
        risk_score += 15
        issues.append("Suspicious Pattern: Excessive punctuation (!!/??)")

    # Check 3: Sensational Keywords
    sensational_words = ["shocking", "you won't believe", "secret", "miracle", "exposed", "banned"]
    for word in sensational_words:
        if word in text.lower():
            risk_score += 10
            issues.append(f"Clickbait Language: '{word}'")

    return max(0, min(100, risk_score)), issues

# --- 3. Rate Limiting (DOS Prevention) ---
def check_rate_limit(ip_address, limit=10, window_seconds=60):
    """
    Simple sliding window rate limiter using the database.
    """
    if ip_address == "127.0.0.1": 
        return True # Dev mode allow

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clean old logs
    cursor.execute("DELETE FROM request_logs WHERE timestamp < ?", (time.time() - window_seconds,))
    
    # Count recent requests
    cursor.execute("SELECT COUNT(*) FROM request_logs WHERE ip_address = ?", (ip_address,))
    count = cursor.fetchone()[0]
    
    if count >= limit:
        conn.close()
        return False
    
    # Log this request
    cursor.execute("INSERT INTO request_logs (ip_address, timestamp) VALUES (?, ?)", (ip_address, time.time()))
    conn.commit()
    conn.close()
    return True

def analyze_security_risk(text, ip_address="0.0.0.0"):
    """
    Main entry point for Cyber Security analysis.
    """
    # 1. Check Rate Limit
    if not check_rate_limit(ip_address):
        return {
            "risk_score": 100,
            "verdict": "BLOCKED",
            "details": ["Security Alert: Rate limit exceeded for this IP."]
        }
    
    # 2. Check Source
    source_risk, source_details = check_source_credibility(text)
    
    # 3. Check Text Patterns
    text_risk, text_details = detect_adversarial_text(text)
    
    total_risk = min(100, source_risk + text_risk)
    
    return {
        "risk_score": total_risk,
        "details": source_details + text_details
    }

def validate_input_quality(text):
    """
    Checks for gibberish or non-sensical input.
    Returns (is_valid: bool, reason: str)
    """
    clean_text = text.strip()
    
    # 1. Too Short
    if len(clean_text) < 4:
        return False, "Input is too short."
        
    # 2. Long single word without spaces (e.g. "fduuyrcxfhtt")
    # Real English words rarely exceed 15 letters without spaces unless technical.
    # We'll lower this to 10 for better protection against mashing.
    if " " not in clean_text and len(clean_text) > 10:
        if not clean_text.startswith("http"):
            return False, "Input detected as random character sequence. Please write the question correctly."
            
    # 3. Repeated Characters (e.g. "aaaaaaaaa")
    if re.search(r'(.)\1{3,}', clean_text):
        return False, "Excessive character repetition detected. Please type correctly."
        
    # 4. Low Vowel Ratio (simple heuristic for random mashing)
    # English text usually has ~30% vowels. If < 20% for a long word, it's suspicious.
    if len(clean_text) > 8 and not clean_text.startswith("http"):
        vowels = set("aeiouAEIOU")
        vowel_count = sum(1 for c in clean_text if c in vowels)
        ratio = vowel_count / len(clean_text)
        if ratio < 0.2: 
             return False, "Input looks like gibberish. Please write properly or use valid words."
             
    return True, "Valid"
