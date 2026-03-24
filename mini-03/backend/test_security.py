from cyber_guard import analyze_security_risk, validate_input_quality, check_rate_limit
import time

def test_security():
    print("=== CYBER SECURITY SYSTEM TEST ===\n")

    # 1. Test Gibberish Detection
    print("[1] Testing Gibberish Detection...")
    gibberish = "ggqhbuvqhrviuieruvberubu"
    is_valid, reason = validate_input_quality(gibberish)
    print(f"Input: '{gibberish}'")
    print(f"Result: {'PASS' if is_valid else 'FAIL (Blocked)'} - Reason: {reason}\n")

    # 2. Test Adversarial Pattern (CapsLock + Clicking)
    print("[2] Testing Adversarial Detection (Sensationalism)...")
    adversarial = "SHOCKING TRUTH!! YOU WON'T BELIEVE WHAT HAPPENED!!!"
    report = analyze_security_risk(adversarial, "1.1.1.1")
    print(f"Input: '{adversarial}'")
    print(f"Risk Score: {report['risk_score']}/100")
    print(f"Issues: {report['details']}\n")

    # 3. Test Source Credibility (Blacklist)
    print("[3] Testing Source Credibility (Blacklist)...")
    blacklisted = "Check this out: http://fakenews.com/story"
    report = analyze_security_risk(blacklisted, "2.2.2.2")
    print(f"Input: '{blacklisted}'")
    print(f"Risk Score: {report['risk_score']}/100")
    print(f"Issues: {report['details']}\n")

    # 4. Test Rate Limiting
    print("[4] Testing Rate Limiting (IP: 9.9.9.9)...")
    ip = "9.9.9.9"
    for i in range(12): # Limit is 10
        allowed = check_rate_limit(ip, limit=10, window_seconds=60)
        status = "Allowed" if allowed else "BLOCKED"
        if i >= 9:
            print(f"Request {i+1}: {status}")

if __name__ == "__main__":
    test_security()
