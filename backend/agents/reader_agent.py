def extract_policy_sections(policy_text: str):
    sections = {}
    keywords = ["Access Control", "Data Retention", "Incident Response", "Encryption"]
    for word in keywords:
        if word.lower() in policy_text.lower():
            sections[word] = "Present"
        else:
            sections[word] = "Missing"
    return sections
