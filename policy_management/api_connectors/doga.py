import requests
import json
import random
import time
from django.conf import settings

# Doğa'nın size vereceği (varsayımsal) API adresi
DOGA_API_URL = "https://api.gercek.dogasigorta.com.tr/teklif_al"
COMPANY_NAME = "Doğa Sigorta"

def get_quote(customer_data, policy_type):
    """
    Doğa Sigorta'dan Kasko/Trafik teklifi alır.
    """
    
    # -----------------------------------------------------------------
    # GERÇEK API ÇAĞRISI İSKELETİ (Gelecekte burayı dolduracaksınız)
    # -----------------------------------------------------------------
    
    # payload = {
    #     "kullanici_adi": settings.DOGA_API_USER,
    #     "sifre": settings.DOGA_API_PASS,
    #     "musteri_detay": customer_data,
    #     "police_tipi": policy_type
    # }

    # try:
    #     response = requests.post(DOGA_API_URL, json=payload, timeout=10)
    #     response.raise_for_status()
    #     data = response.json()
    #     fiyat = data['prim']
        
    #     return {
    #         'company': COMPANY_NAME, 'price': fiyat,
    #         'status': 'success', 'policy_type': policy_type
    #     }
    # except requests.exceptions.RequestException as e:
    #     return {
    #         'company': COMPANY_NAME, 'price': None,
    #         'status': 'error', 'message': f"API Bağlantı Hatası: {e}"
    #     }
    # -----------------------------------------------------------------


    # -----------------------------------------------------------------
    # SİMÜLASYON KODU (Şimdilik bu çalışacak)
    # -----------------------------------------------------------------
    print(f"[Simülasyon] {COMPANY_NAME} API çağrılıyor...")
    time.sleep(0.3) # Doğa daha hızlı (simülasyon)
    base_price = 5000 if policy_type == 'Kasko' else 1500
    price = base_price * (1 + random.uniform(-0.2, 0.2)) # Doğa (daha rekabetçi)
    
    return {
        'company': COMPANY_NAME,
        'price': round(price, 2),
        'status': 'success',
        'policy_type': policy_type
    }