import json
import re
from typing import Dict, List, Any

def load_controls() -> Dict[str, Any]:
    """Load compliance controls from JSON file."""
    import os
    try:
        # Try multiple possible paths
        possible_paths = [
            "backend/data/controls.json",
            "data/controls.json",
            "../backend/data/controls.json",
            os.path.join(os.path.dirname(__file__), "..", "data", "controls.json")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, "r") as f:
                    return json.load(f)
        
        print(f"WARNING: controls.json not found in any expected location")
        # Fallback if file not found
        return {
            "nist_controls": [],
            "iso_controls": [],
            "dpdp_requirements": []
        }
    except Exception as e:
        print(f"ERROR loading controls: {e}")
        return {
            "nist_controls": [],
            "iso_controls": [],
            "dpdp_requirements": []
        }

def extract_sections(policy_text: str) -> Dict[str, str]:
    """Extract key sections from policy text."""
    sections = {
        "Access Control": "",
        "Data Protection": "",
        "Incident Response": "",
        "Authentication": "",
        "Audit and Logging": "",
        "Encryption": "",
        "Backup and Recovery": "",
        "Compliance": ""
    }
    
    # Simple keyword-based extraction
    for section_name in sections:
        # Look for section headers
        pattern = rf"({section_name}|{section_name.lower()}|{section_name.upper()})[:\s]*(.*?)(?=\n\n|\Z)"
        match = re.search(pattern, policy_text, re.IGNORECASE | re.DOTALL)
        if match:
            sections[section_name] = match.group(2)[:500]  # Limit to 500 chars
        else:
            # Check if keywords are mentioned
            keywords = section_name.lower().split()
            for keyword in keywords:
                if keyword in policy_text.lower():
                    sections[section_name] = "Keywords found but no dedicated section"
                    break
    
    return sections

def check_compliance(policy_text: str, sections: Dict[str, str]) -> Dict[str, Any]:
    """Check policy against compliance controls."""
    controls = load_controls()
    results = {
        "nist_compliance": [],
        "iso_compliance": [],
        "dpdp_compliance": [],
        "score": 0,
        "gaps": [],
        "strengths": []
    }
    
    policy_lower = policy_text.lower()
    
    # Check NIST controls
    for control in controls.get("nist_controls", []):
        found = False
        for keyword in control["keywords"]:
            if keyword.lower() in policy_lower:
                found = True
                break
        
        if found:
            results["nist_compliance"].append({
                "control_id": control["id"],
                "name": control["name"],
                "status": "Present"
            })
            results["strengths"].append(f"NIST {control['id']}: {control['name']}")
        else:
            results["nist_compliance"].append({
                "control_id": control["id"],
                "name": control["name"],
                "status": "Missing"
            })
            results["gaps"].append(f"NIST {control['id']}: {control['name']}")
    
    # Check ISO controls
    for control in controls.get("iso_controls", []):
        found = False
        for keyword in control["keywords"]:
            if keyword.lower() in policy_lower:
                found = True
                break
        
        if found:
            results["iso_compliance"].append({
                "control_id": control["id"],
                "name": control["name"],
                "status": "Present"
            })
            results["strengths"].append(f"ISO {control['id']}: {control['name']}")
        else:
            results["iso_compliance"].append({
                "control_id": control["id"],
                "name": control["name"],
                "status": "Missing"
            })
            results["gaps"].append(f"ISO {control['id']}: {control['name']}")
    
    # Check DPDP requirements
    for req in controls.get("dpdp_requirements", []):
        found = False
        for keyword in req["keywords"]:
            if keyword.lower() in policy_lower:
                found = True
                break
        
        if found:
            results["dpdp_compliance"].append({
                "requirement_id": req["id"],
                "name": req["name"],
                "status": "Present"
            })
            results["strengths"].append(f"DPDP {req['id']}: {req['name']}")
        else:
            results["dpdp_compliance"].append({
                "requirement_id": req["id"],
                "name": req["name"],
                "status": "Missing"
            })
            results["gaps"].append(f"DPDP {req['id']}: {req['name']}")
    
    # Calculate score
    total_controls = (len(controls.get("nist_controls", [])) + 
                     len(controls.get("iso_controls", [])) + 
                     len(controls.get("dpdp_requirements", [])))
    
    if total_controls > 0:
        present_controls = len(results["strengths"])
        results["score"] = int((present_controls / total_controls) * 100)
    
    return results

def generate_recommendations(compliance_results: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate recommendations based on compliance gaps."""
    recommendations = []
    
    # Priority mapping
    priority_controls = {
        "AC-1": "Critical",
        "AC-2": "High",
        "IA-2": "Critical",
        "AU-1": "High",
        "IR-1": "Critical",
        "SC-1": "High",
        "A.5.1.1": "Critical",
        "A.9.1.1": "High",
        "A.16.1.1": "Critical",
        "DPDP-1": "High",
        "DPDP-2": "High",
        "DPDP-3": "Critical"
    }
    
    for gap in compliance_results.get("gaps", []):
        control_id = gap.split(":")[0].split()[-1]
        control_name = gap.split(":")[1].strip() if ":" in gap else gap
        
        priority = priority_controls.get(control_id, "Medium")
        
        # Generate specific recommendations
        recommendation = {
            "control": gap,
            "priority": priority,
            "recommendation": f"Implement {control_name}",
            "details": ""
        }
        
        # Add specific details based on control type
        if "access control" in control_name.lower():
            recommendation["details"] = "Establish clear access control policies defining user roles, permissions, and the principle of least privilege."
        elif "mfa" in control_name.lower() or "multi-factor" in control_name.lower():
            recommendation["details"] = "Deploy multi-factor authentication for all user accounts, especially for privileged access."
        elif "incident" in control_name.lower():
            recommendation["details"] = "Develop a comprehensive incident response plan with clear roles, responsibilities, and escalation procedures."
        elif "audit" in control_name.lower():
            recommendation["details"] = "Implement centralized logging and monitoring with regular audit log reviews."
        elif "encryption" in control_name.lower():
            recommendation["details"] = "Implement encryption for data at rest and in transit using industry-standard algorithms."
        elif "backup" in control_name.lower() or "recovery" in control_name.lower():
            recommendation["details"] = "Establish regular backup procedures and test recovery processes periodically."
        elif "consent" in control_name.lower():
            recommendation["details"] = "Implement a consent management system to track and manage user consent for data processing."
        elif "retention" in control_name.lower():
            recommendation["details"] = "Define clear data retention periods and automatic deletion procedures for different data categories."
        else:
            recommendation["details"] = f"Review industry best practices for {control_name} and implement appropriate controls."
        
        recommendations.append(recommendation)
    
    # Sort by priority
    priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))
    
    return recommendations

def create_compliance_summary(compliance_results: Dict[str, Any]) -> str:
    """Create a text summary of compliance results."""
    summary = f"""
COMPLIANCE ANALYSIS SUMMARY
===========================

Overall Compliance Score: {compliance_results['score']}%

Strengths ({len(compliance_results['strengths'])} controls found):
{chr(10).join('- ' + s for s in compliance_results['strengths'][:5])}

Critical Gaps ({len(compliance_results['gaps'])} controls missing):
{chr(10).join('- ' + g for g in compliance_results['gaps'][:5])}

Standards Evaluated:
- NIST 800-53
- ISO 27001
- DPDP Act 2023
"""
    return summary
