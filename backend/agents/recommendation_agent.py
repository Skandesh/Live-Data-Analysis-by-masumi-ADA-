def recommend_improvements(result: dict):
    recs = []
    for gap in result["gaps"]:
        recs.append(f"Implement {gap} policy based on NIST 800-53 and ISO 27001 standards.")
    return {
        "score": result["score"],
        "recommendations": recs,
        "standards": ["NIST 800-53", "ISO 27001", "DPDP 2023"]
    }
