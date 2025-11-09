# policy_management/utils.py

import os
from datetime import datetime, timedelta

# Poliçe PDF'inden veriyi çıkarmayı simüle eden fonksiyon
def extract_policy_data_mock(uploaded_file):
    """
    Yüklenen PDF dosya adına göre poliçe bilgilerini simüle eder.
    Gerçek uygulamada, burada OCR/NLP kütüphaneleri kullanılır.
    """
    
    filename = uploaded_file.name.lower()
    
    # 1. Poliçe Numarası
    policy_number = f"POL-{datetime.now().strftime('%Y%m%d%H%M')}"
    
    # 2. Tarihler (Bugünden başlayıp 1 yıl sonra bitecek varsayalım)
    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=365)
    
    # 3. Prim Tutarı
    premium_amount = 0.00
    
    # Dosya adına göre simülasyon farklılıkları ekleyelim:
    if "kasko" in filename:
        policy_number = "KSK-123456789"
        premium_amount = 7500.50
        
    elif "trafik" in filename:
        policy_number = "TRF-987654321"
        premium_amount = 2500.75
        
    else:
        # Diğer poliçeler (Örn: DASK)
        policy_number = "DASK-101010101"
        premium_amount = 1500.00


    return {
        'policy_number': policy_number,
        'start_date': start_date.strftime('%Y-%m-%d'), # Form bekler: YYYY-MM-DD
        'end_date': end_date.strftime('%Y-%m-%d'),     # Form bekler: YYYY-MM-DD
        'premium_amount': premium_amount
    }