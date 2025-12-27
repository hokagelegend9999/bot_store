import requests
from config import ATLANTIC_API_KEY

PRICE_LIST_URL = "https://atlantich2h.com/layanan/price_list"

def get_headers():
    return {'Content-Type': 'application/x-www-form-urlencoded'}

def get_atlantic_price_list(layanan_type="prabayar"):
    payload = {'api_key': ATLANTIC_API_KEY, 'type': layanan_type}
    try:
        resp = requests.post(PRICE_LIST_URL, data=payload, headers=get_headers(), timeout=20)
        return resp.json()
    except Exception as e:
        print(f"[ATLANTIC] Error: {e}")
        return {"status": False, "message": str(e)}

def get_grouped_providers(data_list):
    """Memisahkan Game dari Provider Utama"""
    # List Provider Utama yang akan kita tampilkan di menu atas
    MAIN_PROVIDERS = [
        'TELKOMSEL', 'INDOSAT', 'XL', 'AXIS', 'TRI', 'THREE', 
        'SMARTFREN', 'PLN', 'BY.U', 'LIFEMEDIA', 'WIFI.ID'
    ]
    
    other_set = set()
    
    for item in data_list:
        if item.get('status') != 'available': continue
        prov = item.get('provider', '').upper().strip()
        if not prov: continue
        
        # Jika TIDAK ada di list utama, masukkan ke "Lainnya/Game"
        if prov not in MAIN_PROVIDERS:
            other_set.add(prov)
            
    return sorted(list(other_set))

# --- FUNGSI FILTER & KATEGORI ---

def get_categories_by_provider(data_list, provider_name):
    """Mengambil kategori berdasarkan nama provider apa adanya"""
    categories = set()
    target_provider = provider_name.upper().strip()
    
    for item in data_list:
        item_prov = item.get('provider', '').upper().strip()
        
        # Logika Pencocokan:
        # Jika targetnya "TRI" atau "THREE", kita ambil dua-duanya biar aman
        if target_provider in ["TRI", "THREE"]:
             if item_prov in ["TRI", "THREE"] and item.get('status') == 'available':
                 categories.add(item.get('category'))
        else:
            # Untuk provider lain (Telkomsel, XL, dll) harus sama persis
            if item_prov == target_provider and item.get('status') == 'available':
                categories.add(item.get('category'))
            
    return sorted(list(categories))

def filter_products_final(data_list, provider, category):
    """
    Filter produk final.
    PERBAIKAN: Tidak lagi mengubah TRI menjadi THREE secara paksa.
    """
    target_provider = provider.upper().strip()
    
    # KITA HAPUS BARIS INI: if provider == "TRI": provider = "THREE"
    
    filtered = []
    for p in data_list:
        # Cek status dulu
        if p.get('status') != 'available':
            continue
            
        p_prov = p.get('provider', '').upper().strip()
        p_cat = p.get('category')
        
        # Logika Fleksibel untuk TRI
        is_provider_match = False
        if target_provider in ["TRI", "THREE"]:
            # Jika user minta TRI, kita kasih data TRI maupun THREE
            if p_prov in ["TRI", "THREE"]:
                is_provider_match = True
        else:
            # Provider lain harus match persis
            if p_prov == target_provider:
                is_provider_match = True
                
        # Cek Kategori
        if is_provider_match and p_cat == category:
            filtered.append(p)
            
    return filtered