import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-nano")

# Google Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Masumi Network Configuration
MASUMI_API_URL = os.getenv("MASUMI_API_URL", "https://api.masumi.network")
MASUMI_API_KEY = os.getenv("MASUMI_API_KEY", "")

# Application Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".doc", ".docx"}

# Compliance Standards
COMPLIANCE_STANDARDS = ["NIST 800-53", "ISO 27001", "DPDP Act 2023"]

# Pricing
PREMIUM_REPORT_PRICE_ADA = 5.0  # 5 ADA tokens for full report
