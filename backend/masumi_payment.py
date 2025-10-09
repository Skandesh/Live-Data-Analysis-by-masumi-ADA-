import requests

def verify_payment(payment_id: str):
    try:
        resp = requests.get(f"https://api.masumi.network/payment/{payment_id}")
        if resp.status_code == 200 and resp.json().get("status") == "CONFIRMED":
            return True
        return False
    except:
        return False
