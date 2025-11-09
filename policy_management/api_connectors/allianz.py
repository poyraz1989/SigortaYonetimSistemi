import requests
import json
import random
import time
from django.conf import settings

# Allianz'ın size vereceği (varsayımsal) API adresi
ALLIANZ_API_URL = "https://api.gercek.allianz.com.tr/v1/teklif/kasko"
COMPANY_NAME = "Allianz Sigorta"

def get_quote(customer_data, policy_type):
    """
    Allianz Sigorta'dan Kasko/Trafik teklifi alır.
    """
    
    # -----------------------------------------------------------------
    # ADIM 1: GERÇEK API ÇAĞRISI İSKELETİ (Gelecekte burayı dolduracaksınız)
    # -----------------------------------------------------------------
    
    # headers = {
    #     "Authorization": f"Bearer {settings.ALLIANZ_API_KEY}",
    #     "Content-Type": "application/json"
    # }
    
    # payload = {
    #     "tc_kimlik": customer_data.get('tckn'),
    #     "plaka": customer_data.get('plaka'),
    #     "urun_kodu": "KASKO" if policy_type == "Kasko" else "TRAFIK"
    # }

    # try:
    #     response = requests.post(ALLIANZ_API_URL, headers=headers, data=json.dumps(payload), timeout=10)
    #     response.raise_for_status() # HTTP 4xx veya 5xx hatası varsa hata fırlat
        
    #     data = response.json()
    #     fiyat = data['teklifDetay']['toplamPrim']
        
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
    # ADIM 2: SİMÜLASYON KODU (Refactor tamamlanana kadar bu çalışacak)
    # -----------------------------------------------------------------
    print(f"[Simülasyon] {COMPANY_NAME} API çağrılıyor...")
    time.sleep(0.5)
    base_price = 5000 if policy_type == 'Kasko' else 1500
    price = base_price * (1 + random.uniform(-0.1, 0.5)) # Allianz simülasyonu
    
    return {
        'company': COMPANY_NAME,
        'price': round(price, 2),
        'status': 'success',
        'policy_type': policy_type
    }