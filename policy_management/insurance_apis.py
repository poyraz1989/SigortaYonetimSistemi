import random
import time

# Sigorta şirketi adlarını sabitler olarak tanımlayalım
INSURANCE_COMPANIES = {
    'doga': 'Doğa Sigorta',
    'allianz': 'Allianz Sigorta',
    'turkiye': 'Türkiye Sigorta',
}

def get_quote(company_code, customer_data, policy_type):
    """
    Belirtilen sigorta şirketinden fiyat teklifi (quote) almayı simüle eder.
    Gerçek uygulamada, buraya API çağrıları gelecektir.
    """
    
    # 0.5 saniye gecikme simülasyonu (Gerçek API yanıt süreleri)
    time.sleep(0.5) 

    # Hata simülasyonu (rastgele bir şirketin teklif vermemesi)
    if random.random() < 0.1 and company_code != 'doga': # %10 ihtimalle teklif vermesin
         return {
            'company': INSURANCE_COMPANIES.get(company_code),
            'price': None,
            'status': 'error',
            'message': f"API bağlantı hatası veya {policy_type} için teklif verilemiyor."
         }

    # Fiyat simülasyonu (policy_type'a göre farklı baz fiyatlar)
    base_price = 5000 if policy_type == 'Kasko' else 1500

    # Rastgele bir fiyatlandırma simülasyonu
    price = base_price * (1 + random.uniform(-0.2, 0.4))
    
    return {
        'company': INSURANCE_COMPANIES.get(company_code),
        'price': round(price, 2),
        'status': 'success',
        'policy_type': policy_type
    }