# Buat file: nano cek_json.py
import requests
import json

url = "https://okeconnect.com/harga/json?id=905ccd028329b0a"
print("⏳ Sedang download JSON...")

try:
    r = requests.get(url, timeout=15)
    data = r.json()
    print(f"✅ Data Terambil! Total Produk: {len(data)}")
    
    # Cek Sample Data Pertama
    print("\n🔍 CONTOH ITEM PERTAMA:")
    first_item = data[0]
    print(json.dumps(first_item, indent=4))
    
    # Cek field 'produk'
    print("\n🔍 CEK FIELD PENTING:")
    if 'produk' in first_item:
        print("✅ Field 'produk' DITEMUKAN (Ini dipakai untuk kategori)")
    else:
        print("❌ Field 'produk' TIDAK ADA (Perlu ganti logic filter)")
        
except Exception as e:
    print(f"Error: {e}")