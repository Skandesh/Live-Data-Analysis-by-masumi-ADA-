from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from typing import Dict, Any, Optional
import json
from backend.config import OPENAI_API_KEY, OPENAI_MODEL, GEMINI_API_KEY, GEMINI_MODEL
from backend.agents.tools import (
    extract_sections,
    check_compliance,
    generate_recommendations,
    create_compliance_summary
)

# Try to import Gemini, but don't fail if not available
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: Google Gemini not available. Install langchain-google-genai to use Gemini.")

class PolicyAnalysisCrew:
    def __init__(self, llm=None):
        """Initialize with a specific LLM or use default"""
        if llm is None:
            # Default to OpenAI
            self.llm = ChatOpenAI(
                model=OPENAI_MODEL,
                api_key=OPENAI_API_KEY,
                temperature=0.7
            )
        else:
            self.llm = llm
        self.setup_agents()
        
    def setup_agents(self):
        """Initialize the three specialized agents."""
    
        # Reader Agent - Extracts and structures policy content
        self.reader_agent = Agent(
            role="Cybersecurity Policy Reader",
            goal="Extract and identify key sections from security policies",
            backstory="""You are an expert cybersecurity policy analyst with years of experience 
            reading and interpreting security documentation. You excel at identifying important 
            sections like access control, data protection, incident response, and compliance 
            requirements in policy documents.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Compliance Agent - Maps policies to standards
        self.compliance_agent = Agent(
            role="Compliance Standards Auditor",
            goal="Evaluate policies against NIST 800-53, ISO 27001, and DPDP Act 2023",
            backstory="""You are a certified compliance auditor specializing in cybersecurity 
            frameworks. You have deep knowledge of NIST 800-53 controls, ISO 27001 requirements, 
            and India's DPDP Act 2023. You meticulously check policies for control implementation 
            and identify compliance gaps.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Recommendation Agent - Generates improvement suggestions
        self.recommendation_agent = Agent(
            role="Security Improvement Consultant",
            goal="Generate actionable recommendations to address compliance gaps",
            backstory="""You are a senior cybersecurity consultant who helps organizations 
            improve their security posture. You provide practical, prioritized recommendations 
            based on industry best practices and compliance requirements. Your suggestions are 
            specific, actionable, and tailored to address identified gaps.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def analyze_policy(self, policy_text: str, premium: bool = False) -> Dict[str, Any]:
        """
        Analyze a security policy document.
        
        Args:
            policy_text: The policy document text
            premium: Whether to generate full report with AI recommendations
            
        Returns:
            Analysis results with score and recommendations
        """
        
        # Task 1: Extract policy sections
        extraction_task = Task(
            description=f"""
            Analyze the following security policy document and identify key sections:
            
            {policy_text[:2000]}...
            
            Extract and summarize sections related to:
            - Access Control
            - Data Protection  
            - Incident Response
            - Authentication (including MFA)
            - Audit and Logging
            - Encryption
            - Backup and Recovery
            - Compliance
            
            For each section, provide a brief summary of what is covered.
            """,
            expected_output="Structured extraction of policy sections with summaries",
            agent=self.reader_agent
        )
        
        # Task 2: Check compliance
        compliance_task = Task(
            description=f"""
            Based on the policy content, evaluate compliance with:
            
            1. NIST 800-53 controls (AC-1, AC-2, AU-1, IA-1, IA-2, IR-1, SC-1, CP-1)
            2. ISO 27001 controls (A.5.1.1, A.9.1.1, A.9.2.1, A.12.1.1, A.16.1.1, A.18.1.1)
            3. DPDP Act 2023 requirements (Data Principal Rights, Retention, Consent)
            
            Identify which controls are:
            - Fully addressed
            - Partially addressed
            - Missing
            
            Calculate an overall compliance score (0-100%).
            """,
            expected_output="Compliance assessment with score and gap analysis",
            agent=self.compliance_agent
        )
        
        # Task 3: Generate recommendations (only for premium)
        recommendation_task = Task(
            description="""
            Based on the identified compliance gaps, provide specific recommendations:
            
            1. Prioritize gaps as Critical, High, Medium, or Low
            2. For each gap, suggest concrete implementation steps
            3. Provide templates or examples where applicable
            4. Create an implementation roadmap
            
            Focus on practical, actionable advice that addresses the most critical gaps first.
            """,
            expected_output="Prioritized list of recommendations with implementation guidance",
            agent=self.recommendation_agent
        )
        
        # Create crew with appropriate tasks
        if premium:
            crew = Crew(
                agents=[self.reader_agent, self.compliance_agent, self.recommendation_agent],
                tasks=[extraction_task, compliance_task, recommendation_task],
                process=Process.sequential,
                verbose=True
            )
        else:
            crew = Crew(
                agents=[self.reader_agent, self.compliance_agent],
                tasks=[extraction_task, compliance_task],
                process=Process.sequential,
                verbose=True
            )
        
        try:
            # Execute the crew
            print(f"DEBUG: Starting CrewAI analysis...")
            print(f"DEBUG: Policy text length: {len(policy_text)}")
            print(f"DEBUG: First 100 chars: {policy_text[:100]}")
            print(f"DEBUG: Premium mode: {premium}")
            
            result = crew.kickoff()
            
            print(f"DEBUG: CrewAI execution completed")
            
            # Process results with our tools for structured data
            sections = extract_sections(policy_text)
            compliance_results = check_compliance(policy_text, sections)
            
            print(f"DEBUG: Compliance score: {compliance_results['score']}")
            print(f"DEBUG: Strengths found: {len(compliance_results['strengths'])}")
            print(f"DEBUG: Gaps found: {len(compliance_results['gaps'])}")
            
            # Build response
            response = {
                "success": True,
                "score": compliance_results["score"],
                "gaps": compliance_results["gaps"][:10],  # Top 10 gaps
                "strengths": compliance_results["strengths"][:5],  # Top 5 strengths
                "summary": create_compliance_summary(compliance_results),
                "sections_found": list(sections.keys())
            }
            
            if premium:
                # Add AI-generated recommendations
                recommendations = generate_recommendations(compliance_results)
                response["recommendations"] = recommendations[:10]  # Top 10 recommendations
                response["ai_analysis"] = str(result)  # Full AI analysis
                response["compliance_details"] = {
                    "nist": compliance_results["nist_compliance"],
                    "iso": compliance_results["iso_compliance"],
                    "dpdp": compliance_results["dpdp_compliance"]
                }
            
            return response
            
        except Exception as e:
            print(f"ERROR in analyze_policy: {e}")
            import traceback
            error_traceback = traceback.format_exc()
            print(error_traceback)
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "error_details": error_traceback,
                "score": 0,
                "gaps": [],
                "strengths": [],
                "message": f"Analysis failed: {str(e)}"
            }

def get_policy_crew(api_key: Optional[str] = None, provider: str = "openai"):
    """
    Get or create the policy analysis crew with specified LLM.
    
    Args:
        api_key: Optional API key. If not provided, uses backend default from .env
        provider: LLM provider - "openai" (default) or "gemini"
    
    Returns:
        PolicyAnalysisCrew instance configured with the specified LLM
    """
    
    # Initialize LLM based on provider
    if provider == "gemini":
        if not GEMINI_AVAILABLE:
            print("Warning: Gemini not available, falling back to OpenAI")
            # Fall back to OpenAI
            llm = ChatOpenAI(
                model=OPENAI_MODEL,
                api_key=api_key or OPENAI_API_KEY,
                temperature=0.7
            )
        else:
            # Use provided key or fallback to backend Gemini key
            gemini_key = api_key or GEMINI_API_KEY
            if not gemini_key:
                print("Warning: No Gemini API key found, falling back to OpenAI")
                llm = ChatOpenAI(
                    model=OPENAI_MODEL,
                    api_key=OPENAI_API_KEY,
                    temperature=0.7
                )
            else:
                llm = ChatGoogleGenerativeAI(
                    model=GEMINI_MODEL,
                    google_api_key=gemini_key,
                    temperature=0.7
                )
    else:
        # OpenAI (default) - use provided key or fallback to backend key
        llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=api_key or OPENAI_API_KEY,
            temperature=0.7
        )
    
    return PolicyAnalysisCrew(llm=llm)
