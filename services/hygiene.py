from typing import List, Dict

HYGIENE_QUESTIONS = [
    "Do you have Multi-Factor Authentication (MFA) enabled on critical accounts? (yes/no)",
    "Do you use unique passwords of 12 or more characters per account? (yes/no)",
    "Do you regularly install OS and software updates? (yes/no)",
    "Do you have up-to-date antivirus/endpoint protection? (yes/no)",
    "Do you maintain regular backups of important data (offline or cloud)? (yes/no)",
    "Have you had phishing-awareness training in the last 12 months? (yes/no)"
]

def normalize_yes(ans: str) -> bool:
    if not ans:
        return False
    return ans.strip().lower() in ("y", "yes", "true", "1", "yeah", "yep")

# --- ADD THIS NEW FUNCTION ---
def normalize_no(ans: str) -> bool:
    if not ans:
        return False
    return ans.strip().lower() in ("n", "no", "false", "0", "nope", "nay")
# -----------------------------

def score_hygiene(answers: List[str]) -> Dict:
    details = []
    yes_count = 0
    
    # Use zip_longest to handle cases where answers list might be incomplete
    from itertools import zip_longest
    for q, a in zip_longest(HYGIENE_QUESTIONS, answers):
        if q is None: continue
        ok = normalize_yes(a)
        details.append({"question": q, "answer": a, "ok": ok})
        if ok:
            yes_count += 1

    score = round((yes_count / len(HYGIENE_QUESTIONS)) * 10, 1)
    weaknesses = [d["question"] for d in details if not d["ok"]]
    
    return {
        "score": score, 
        "weaknesses": weaknesses, 
        "details": details
    }