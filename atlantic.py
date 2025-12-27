import requests
import time
import json
from config import ATLANTIC_API_KEY

# Base URL API Atlantic
BASE_URL = "https://atlantich2h.com/deposit"

def get_headers():
    return {'Content-Type': 'application/x-www-form-urlencoded'}

def create_deposit_qris(nominal, user_id):
    """
    Membuat Tagihan QRIS.
    """
    url = f"{BASE_URL}/create"
    reff_id = f"DEP-{user_id}-{int(time.time())}"
    
    # --- PERBAIKAN DISINI ---
    payload = {
        'api_key': ATLANTIC_API_KEY,
        'reff_id': reff_id,
        'nominal': nominal,
        'type': 'ewallet', 
        'metode': 'qris'   # GANTI DARI 'method' KE 'metode'
    }
    
    try:
        # DEBUG LOG (Agar muncul di journalctl)
        print(f"[ATLANTIC] Requesting Deposit: {nominal} for {user_id}")
        
        resp = requests.post(url, data=payload, headers=get_headers())
        
        # DEBUG LOG RESPONSE
        print(f"[ATLANTIC] Response Raw: {resp.text}")
        
        return resp.json()
    except Exception as e:
        print(f"[ATLANTIC] Error: {e}") # Log error sistem
        return {"status": False, "message": str(e)}

def check_deposit_status(trx_id):
    """
    Cek Status Transaksi.
    """
    url = f"{BASE_URL}/status"
    payload = {
        'api_key': ATLANTIC_API_KEY,
        'id': trx_id
    }
    
    try:
        resp = requests.post(url, data=payload, headers=get_headers())
        return resp.json()
    except Exception as e:
        print(f"[ATLANTIC] Check Status Error: {e}")
        return {"status": False, "message": str(e)}

def cancel_deposit(trx_id):
    """
    Membatalkan Tagihan.
    """
    url = f"{BASE_URL}/cancel"
    payload = {
        'api_key': ATLANTIC_API_KEY,
        'id': trx_id
    }
    try:
        resp = requests.post(url, data=payload, headers=get_headers())
        return resp.json()
    except Exception as e:
        return {"status": False, "message": str(e)}