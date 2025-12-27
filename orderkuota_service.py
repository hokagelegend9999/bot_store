import requests
import logging
import time
import re  # Penting untuk menangkap T# (Server ID)
from config import (
    OKECONNECT_MEMBER_ID, 
    OKECONNECT_PIN, 
    OKECONNECT_PASSWORD, 
    OKECONNECT_TRX_URL,
    OKECONNECT_PRICE_URL
)

# --- KONFIGURASI CACHE (ANTI-LIMIT) ---
_PRICE_CACHE = []            
_LAST_FETCH_TIME = 0         
CACHE_DURATION = 3600        

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}

# ==========================================
# 1. AMBIL DAFTAR HARGA
# ==========================================
def get_okeconnect_price(force_update=False):
    global _PRICE_CACHE, _LAST_FETCH_TIME
    
    current_time = time.time()
    is_expired = (current_time - _LAST_FETCH_TIME) > CACHE_DURATION
    
    if _PRICE_CACHE and not is_expired and not force_update:
        return _PRICE_CACHE

    try:
        print(f"[PPOB] 🔄 Update Harga dari Server... (Last: {int(current_time - _LAST_FETCH_TIME)}s ago)")
        response = requests.get(OKECONNECT_PRICE_URL, headers=HEADERS, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                _PRICE_CACHE = data        
                _LAST_FETCH_TIME = current_time
                print(f"[PPOB] ✅ Berhasil update {len(data)} produk.")
                return data
            else:
                logging.error(f"[PPOB] Format JSON tidak sesuai: {type(data)}")
                return _PRICE_CACHE 
        elif response.status_code == 429:
            logging.warning("[PPOB] ⚠️ Terkena Limit (429). Menggunakan cache.")
            return _PRICE_CACHE
        else:
            logging.error(f"[PPOB] Gagal ambil harga. HTTP: {response.status_code}")
            return _PRICE_CACHE
            
    except Exception as e:
        logging.error(f"[PPOB] Error Connection: {e}")
        return _PRICE_CACHE

# ==========================================
# 2. KIRIM TRANSAKSI (LOGIKA DIPERBAIKI)
# ==========================================
def request_orderkuota_trx(kode_produk, nomor_tujuan, ref_id):
    # Sesuai dokumentasi: product, dest, refID, memberID, pin, password
    params = {
        'memberID': OKECONNECT_MEMBER_ID,
        'pin': OKECONNECT_PIN,
        'password': OKECONNECT_PASSWORD,
        'product': kode_produk,
        'dest': nomor_tujuan,
        'refID': ref_id
    }
    
    result = {
        "success": False,
        "msg": "",
        "server_id": None,
        "raw": ""
    }

    try:
        print(f"[PPOB] 🚀 Mengirim Trx: {kode_produk} -> {nomor_tujuan} (Ref: {ref_id})")
        # Timeout 60s karena respon PPOB kadang lambat
        response = requests.get(OKECONNECT_TRX_URL, params=params, headers=HEADERS, timeout=60)
        text_respon = response.text
        
        print(f"[PPOB] 📩 Respon Server: {text_respon}")
        
        result["raw"] = text_respon
        result["msg"] = text_respon 
        
        # --- PERBAIKAN REGEX (PENCARIAN ID) ---
        # Menangkap variasi: "T#123", "T# 123", "TrxID: 123"
        # Ini mencegah bot "buta" terhadap ID Server
        match = re.search(r"(?:T\#|ID)[\s:]*(\d+)", text_respon, re.IGNORECASE)
        
        if match:
            server_id = match.group(1)
            result["success"] = True
            result["server_id"] = server_id
            print(f"[PPOB] ✅ Transaksi Sukses! Server ID: {server_id}")
        else:
            # Fallback: Jika tidak ada T#, tapi ada kata sukses/diproses
            text_upper = text_respon.upper()
            if "BERHASIL" in text_upper or "DIPROSES" in text_upper or "SUKSES" in text_upper:
                result["success"] = True
                print("[PPOB] ⚠️ Transaksi dianggap masuk (No ID Found).")
            elif "GAGAL" in text_upper or "SALAH" in text_upper or "CUKUP" in text_upper:
                result["success"] = False
            else:
                # Respon ambigu, anggap sukses sementara agar user cek manual, jangan langsung vonis gagal
                result["success"] = True 
                result["msg"] += " (Cek Manual)"
        
        return result

    except requests.exceptions.Timeout:
        result["msg"] = "TIMEOUT (Sedang Diproses, Cek Status Berkala)"
        # Jangan set success=False agar bot bisa mencoba cek status nanti
        return result
    except Exception as e:
        logging.error(f"[PPOB] Error Trx: {e}")
        result["msg"] = f"ERROR SISTEM: {str(e)}"
        return result

# ==========================================
# 3. CEK STATUS TRANSAKSI (FINAL FIX - SUPPORT DATA LENGKAP)
# ==========================================
def check_orderkuota_status(ref_id, server_id=None, nomor_tujuan=None, kode_produk=None):
    """
    Cek Status sesuai dokumentasi OkeConnect:
    Wajib bawa: memberID, pin, password, check=1, refID, dest, product
    Agar tidak kena 'Kode tidak ditemukan'.
    """
    base_params = {
        'memberID': OKECONNECT_MEMBER_ID,
        'pin': OKECONNECT_PIN,
        'password': OKECONNECT_PASSWORD,
        'check': '1', 
    }
    
    # --- SKENARIO UTAMA: Sesuai Dokumentasi (Parameter Lengkap) ---
    # Ini yang akan dijalankan bot sekarang karena datanya sudah lengkap
    if ref_id and nomor_tujuan and kode_produk:
        print(f"[PPOB] 🔍 Cek Sesuai Docs (RefID+Dest+Prod)...")
        params = base_params.copy()
        params['refID'] = ref_id
        params['dest'] = nomor_tujuan   # Parameter 'dest'
        params['product'] = kode_produk # Parameter 'product' (bukan 'produk')
        
        try:
            res = requests.get(OKECONNECT_TRX_URL, params=params, headers=HEADERS, timeout=10)
            # Jika server menjawab status (bukan error kode), kembalikan
            if "Kode tidak ditemukan" not in res.text:
                return res.text
        except: pass

    # --- SKENARIO CADANGAN 1: Pakai REF ID Saja ---
    if ref_id:
        print(f"[PPOB] 🔍 Cek Cadangan (RefID Only)...")
        params = base_params.copy()
        params['refID'] = ref_id
        try:
            res = requests.get(OKECONNECT_TRX_URL, params=params, headers=HEADERS, timeout=10)
            if "Kode tidak ditemukan" not in res.text:
                return res.text
        except: pass

    # --- SKENARIO CADANGAN 2: Pakai SERVER ID (Param 'id') ---
    if server_id:
        print(f"[PPOB] 🔍 Cek Cadangan (Server ID)...")
        params = base_params.copy()
        params['id'] = server_id
        try:
            res = requests.get(OKECONNECT_TRX_URL, params=params, headers=HEADERS, timeout=10)
            return res.text 
        except Exception as e:
            return f"Error Koneksi: {e}"

    return "DATA TIDAK LENGKAP (Cek Web Report Manual)"
# ==========================================
# 4. CEK PROFIL / SALDO
# ==========================================
def get_okeconnect_profile():
    url_balance = "https://h2h.okeconnect.com/balance"
    params = {
        'memberID': OKECONNECT_MEMBER_ID,
        'pin': OKECONNECT_PIN,
        'password': OKECONNECT_PASSWORD
    }
    
    try:
        response = requests.get(url_balance, params=params, headers=HEADERS, timeout=10)
        text_respon = response.text

        if "Saldo" in text_respon or "Sisa" in text_respon:
            return text_respon
        elif "Gagal" in text_respon:
            return f"Error Provider: {text_respon}"
        else:
            return text_respon 

    except Exception as e:
        logging.error(f"[PPOB] Error Profile: {e}")
        return None