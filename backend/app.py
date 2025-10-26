from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import os
import asyncio
import json
import sys
import io
import threading
import queue
import time
from backend.crew_orchestrator import get_policy_crew
from backend.masumi_payment import verify_payment
from backend.config import MAX_FILE_SIZE, ALLOWED_EXTENSIONS

app = FastAPI(
    title="Live Data Analysis by Masumi (ADA)",
    description="AI-Driven Cybersecurity Policy Analyzer with On-Chain Monetization",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PaymentVerification(BaseModel):
    payment_id: str

@app.get("/")
async def root():
    return {
        "service": "Live Data Analysis by Masumi (ADA)",
        "status": "operational",
        "endpoints": {
            "analyze": "/analyze_policy/",
            "verify_payment": "/verify_payment/",
            "health": "/health/"
        }
    }

@app.get("/health")
@app.get("/health/")
async def health_check():
    return {
        "status": "healthy",
        "service": "ADA Policy Analyzer",
        "ai_ready": True,
        "payment_ready": True
    }

@app.post("/analyze_policy/")
async def analyze_policy(
    file: UploadFile,
    premium: bool = Form(False),
    payment_id: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    llm_provider: str = Form("openai")
):
    """
    Analyze a cybersecurity policy document.
    
    - Free tier: Returns compliance score and gap list
    - Premium tier: Includes AI-generated recommendations and detailed report
    - Supports custom API keys and multiple LLM providers (OpenAI, Gemini)
    """
    
    # Validate file
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Max 10MB allowed.")
    
    # Get file extension and handle edge cases
    filename = file.filename or "policy.txt"
    file_ext = os.path.splitext(filename)[1].lower()
    
    # If no extension, assume .txt
    if not file_ext:
        file_ext = ".txt"
    
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check payment for premium features
    if premium:
        if not payment_id:
            raise HTTPException(
                status_code=402, 
                detail="Payment required for premium analysis"
            )
        
        if not verify_payment(payment_id):
            raise HTTPException(
                status_code=402, 
                detail="Payment verification failed"
            )
    
    try:
        # Read file content
        content = await file.read()
        
        # Debug file reading
        print(f"DEBUG: File size: {len(content)} bytes")
        print(f"DEBUG: File extension: {file_ext}")
        
        # Handle different file types
        if file_ext in ['.txt']:
            policy_text = content.decode('utf-8', errors='ignore')
        else:
            # For now, just treat other formats as text
            # In production, you'd use libraries like PyPDF2 for PDFs
            policy_text = content.decode('utf-8', errors='ignore')
        
        # More debug
        print(f"DEBUG: Decoded text length: {len(policy_text)}")
        print(f"DEBUG: First 200 chars of policy: {policy_text[:200]}")
        
        if not policy_text or len(policy_text) < 10:
            raise HTTPException(
                status_code=400,
                detail="File appears to be empty or too small"
            )
        
        # Get the crew and analyze (with custom API key if provided)
        if api_key and llm_provider:
            crew = get_policy_crew(api_key=api_key, provider=llm_provider)
        else:
            crew = get_policy_crew()
        results = crew.analyze_policy(policy_text, premium=premium)
        
        # Return results with detailed error info if failed
        if not results.get("success", True):
            return {
                **results,
                "error_message": results.get("message", "Unknown error"),
                "error_type": results.get("error_type", "UnknownError"),
                "technical_details": results.get("error", "No details available")
            }
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR in analyze_policy endpoint: {error_trace}")
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"Analysis failed: {str(e)}",
                "error_type": type(e).__name__,
                "technical_details": str(e),
                "full_trace": error_trace
            }
        )

@app.post("/verify_payment/")
async def verify_payment_endpoint(payment: PaymentVerification):
    """
    Verify a Masumi network payment.
    """
    is_valid = verify_payment(payment.payment_id)
    
    return {
        "payment_id": payment.payment_id,
        "verified": is_valid,
        "status": "confirmed" if is_valid else "pending"
    }

@app.get("/compliance_standards/")
async def get_compliance_standards():
    """
    Get list of supported compliance standards.
    """
    return {
        "standards": [
            {
                "name": "NIST 800-53",
                "version": "Rev 5",
                "controls": 8
            },
            {
                "name": "ISO 27001",
                "version": "2022",
                "controls": 6
            },
            {
                "name": "DPDP Act",
                "version": "2023",
                "requirements": 3
            }
        ]
    }

@app.post("/analyze_policy_stream/")
async def analyze_policy_stream(
    file: UploadFile,
    premium: bool = Form(False),
    payment_id: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    llm_provider: str = Form("openai")
):
    """Stream analysis progress with real-time updates"""
    
    async def event_generator():
        message_queue = queue.Queue()
        
        try:
            # Step 1: Validate and read file
            yield f"data: {json.dumps({'step': 1, 'message': 'Uploading and validating document...', 'progress': 10})}\n\n"
            await asyncio.sleep(0.5)
            
            content = await file.read()
            if not content:
                yield f"data: {json.dumps({'error': 'Empty file'})}\n\n"
                return
            
            # Get file extension
            filename = file.filename or "policy.txt"
            file_ext = os.path.splitext(filename)[1].lower()
            if not file_ext:
                file_ext = ".txt"
                
            if file_ext not in ALLOWED_EXTENSIONS:
                yield f"data: {json.dumps({'error': f'Invalid file type. Allowed: {ALLOWED_EXTENSIONS}'})}\n\n"
                return
            
            policy_text = content.decode('utf-8', errors='ignore')
            yield f"data: {json.dumps({'step': 1, 'message': 'Document validated successfully', 'progress': 20})}\n\n"
            
            # Check payment for premium
            if premium:
                if not payment_id:
                    yield f"data: {json.dumps({'error': 'Payment required for premium analysis'})}\n\n"
                    return
                if not verify_payment(payment_id):
                    yield f"data: {json.dumps({'error': 'Payment verification failed'})}\n\n"
                    return
            
            # Step 2: Start analysis with output capture
            def run_crew_analysis():
                old_stdout = sys.stdout
                sys.stdout = output_buffer = io.StringIO()
                
                try:
                    # Get crew with selected LLM
                    if api_key and llm_provider:
                        crew = get_policy_crew(api_key=api_key, provider=llm_provider)
                    else:
                        crew = get_policy_crew()
                    
                    last_position = 0
                    result = None
                    
                    def execute_crew():
                        nonlocal result
                        result = crew.analyze_policy(policy_text, premium=premium)
                    
                    crew_thread = threading.Thread(target=execute_crew)
                    crew_thread.start()
                    
                    # Monitor output while crew is running
                    while crew_thread.is_alive():
                        current_output = output_buffer.getvalue()
                        if len(current_output) > last_position:
                            new_text = current_output[last_position:]
                            last_position = len(current_output)
                            
                            # Parse output for agent activity
                            if "Cybersecurity Policy Reader" in new_text:
                                message_queue.put({
                                    'step': 2, 
                                    'message': 'Policy Reader Agent extracting security sections...', 
                                    'progress': 35
                                })
                            elif "Compliance Standards Auditor" in new_text:
                                message_queue.put({
                                    'step': 3, 
                                    'message': 'Compliance Auditor evaluating standards...', 
                                    'progress': 55
                                })
                            elif "Security Improvement Consultant" in new_text and premium:
                                message_queue.put({
                                    'step': 4, 
                                    'message': 'AI Consultant generating recommendations...', 
                                    'progress': 75
                                })
                        
                        time.sleep(0.5)
                    
                    crew_thread.join()
                    
                    # Send final result
                    message_queue.put({
                        'complete': True,
                        'result': result,
                        'progress': 100
                    })
                    
                finally:
                    sys.stdout = old_stdout
            
            # Run analysis in background thread
            analysis_thread = threading.Thread(target=run_crew_analysis)
            analysis_thread.start()
            
            # Stream messages from queue
            while analysis_thread.is_alive() or not message_queue.empty():
                try:
                    message = message_queue.get(timeout=0.5)
                    yield f"data: {json.dumps(message)}\n\n"
                    await asyncio.sleep(0.1)
                except queue.Empty:
                    await asyncio.sleep(0.5)
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
