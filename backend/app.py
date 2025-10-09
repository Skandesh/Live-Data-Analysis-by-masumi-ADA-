from fastapi import FastAPI, UploadFile, Form
from agents.reader_agent import extract_policy_sections
from agents.compliance_agent import check_compliance
from agents.recommendation_agent import recommend_improvements
from masumi_payment import verify_payment

app = FastAPI(title="Live Data Analysis by Masumi (ADA)")

@app.post("/analyze_policy/")
async def analyze_policy(file: UploadFile, payment_id: str = Form(None)):
    content = (await file.read()).decode("utf-8")
    policy_data = extract_policy_sections(content)
    compliance_result = check_compliance(policy_data)

    if not payment_id:
        return {"score": compliance_result["score"], "gaps": compliance_result["gaps"]}

    if verify_payment(payment_id):
        recommendations = recommend_improvements(compliance_result)
        return {"full_report": recommendations}
    else:
        return {"error": "Payment not verified"}
