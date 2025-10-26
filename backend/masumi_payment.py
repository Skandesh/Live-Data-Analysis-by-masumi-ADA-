import requests
from backend.config import MASUMI_API_URL, MASUMI_API_KEY
import logging

logger = logging.getLogger(__name__)

def verify_payment(payment_id: str) -> bool:
    """
    Verify payment status with Masumi network.
    
    Args:
        payment_id: The payment transaction ID
        
    Returns:
        True if payment is confirmed, False otherwise
    """
    try:
        # For development/demo purposes, accept test payment IDs
        if payment_id.startswith("TEST_") or payment_id == "demo":
            logger.info(f"Test payment accepted: {payment_id}")
            return True
        
        # Real Masumi API call
        headers = {
            "Authorization": f"Bearer {MASUMI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        resp = requests.get(
            f"{MASUMI_API_URL}/payment/{payment_id}",
            headers=headers,
            timeout=10
        )
        
        if resp.status_code == 200:
            data = resp.json()
            status = data.get("status", "").upper()
            
            if status in ["CONFIRMED", "COMPLETED", "SUCCESS"]:
                logger.info(f"Payment verified: {payment_id}")
                return True
            else:
                logger.warning(f"Payment not confirmed: {payment_id}, status: {status}")
        else:
            logger.error(f"Payment verification failed: HTTP {resp.status_code}")
            
        return False
        
    except requests.RequestException as e:
        logger.error(f"Payment verification error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in payment verification: {str(e)}")
        return False

def create_payment_request(amount_ada: float, description: str) -> dict:
    """
    Create a payment request on Masumi network.
    
    Args:
        amount_ada: Amount in ADA tokens
        description: Payment description
        
    Returns:
        Payment request details including payment_id
    """
    try:
        headers = {
            "Authorization": f"Bearer {MASUMI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "amount": amount_ada,
            "currency": "ADA",
            "description": description,
            "service": "ADA Policy Analyzer"
        }
        
        resp = requests.post(
            f"{MASUMI_API_URL}/payment/create",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if resp.status_code in [200, 201]:
            return resp.json()
        else:
            logger.error(f"Failed to create payment request: HTTP {resp.status_code}")
            return {"error": "Failed to create payment request"}
            
    except Exception as e:
        logger.error(f"Error creating payment request: {str(e)}")
        return {"error": str(e)}
