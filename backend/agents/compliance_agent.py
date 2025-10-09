def check_compliance(policy_data: dict):
    present = list(policy_data.values()).count("Present")
    score = int((present / len(policy_data)) * 100)
    gaps = [k for k, v in policy_data.items() if v == "Missing"]
    return {"score": score, "gaps": gaps}
