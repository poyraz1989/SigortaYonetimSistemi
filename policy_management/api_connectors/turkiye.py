import requests
import json
import random
import time
from django.conf import settings

TURKIYE_API_URL = "https://api.gercek.turkiyesigorta.com.tr/quote"
COMPANY_NAME = "Türkiye Sigorta"

def get_quote(customer_data, policy_type):
    """
    Türkiye Sigorta'dan Kasko/Trafik teklifi alır.
    """
    
    # -----------------------------------------------------------------
    # GERÇEK API ÇAĞRISI İSKELETİ (Gelecekte burayı dolduracaksınız)
    # -----------------------------------------------------------------
    
    # ... (Buraya Türkiye Sigorta'nın API mantığı gelecek) ...
    
    # -----------------------------------------------------------------
    # SİMÜLASYON KODU (Şimdilik bu çalışacak)
    # -----------------------------------------------------------------
    print(f"[Simülasyon] {COMPANY_NAME} API çağrılıyor...")
    time.sleep(0.7) # Türkiye Sigorta (daha yavaş)
    base_price = 5000 if policy_type == 'Kasko' else 1500
    price = base_price * (1 + random.uniform(0.1, 0.6)) # Türkiye Sigorta (daha yüksek)
    
    return {
        'company': COMPANY_NAME,
        'price': round(price, 2),
        'status': 'success',
        'policy_type': policy_type
    }