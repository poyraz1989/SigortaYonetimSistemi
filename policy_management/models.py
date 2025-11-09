from django.db import models
from django.contrib.auth.models import AbstractUser

# Kendi kullanıcı modelimizi tanımlıyoruz
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Yönetici'),
        ('agent', 'Acente'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='agent', verbose_name="Kullanıcı Rolü")

    class Meta:
        verbose_name = "Kullanıcı"
        verbose_name_plural = "Kullanıcılar"
        
    # Python bu bloğun boş olduğunu bildiği için "pass" anahtar kelimesini kullanmalıyız
    pass


# -----------------------------------------------------
# MÜŞTERİ MODELİ (Customer)
# -----------------------------------------------------

class Customer(models.Model):
    # Tip seçenekleri
    CUSTOMER_TYPE_CHOICES = (
        ('individual', 'Bireysel'),
        ('corporate', 'Kurumsal'),
    )

    customer_id = models.AutoField(primary_key=True)
    
    # 1. TEMEL VE KİMLİK BİLGİLERİ
    name = models.CharField(max_length=150, verbose_name="Adı / Ünvanı")
    
    # TCKN: Yeni alan (unique ve null=True, boş değerler için geçici çözüm)
    tckn = models.CharField(
        max_length=11, 
        unique=True, 
        null=True,     
        blank=True,    
        verbose_name="TCKN"
    )
    
    # TCKN/VKN ESKİ ALANI (Artık formda yok, benzersizlik kısıtlaması kaldırıldı)
    # Bu alanın benzersizlik kısıtlamasını kaldırdık, çünkü formu kullanmıyorsunuz
    # ve eski verilerde boş kalıp IntegrityError veriyordu.
    tckn_vkn = models.CharField(
        max_length=15, 
        null=True, 
        blank=True,
        verbose_name="TCKN/VKN (Eski Alan)" 
    )
    
    customer_type = models.CharField(
        max_length=10, 
        choices=CUSTOMER_TYPE_CHOICES, 
        default='individual',
        verbose_name="Müşteri Tipi"
    )

    # 2. İLETİŞİM BİLGİLERİ
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefon")
    email = models.EmailField(max_length=255, blank=True, null=True, verbose_name="E-posta")
    
    # Adres Bilgileri
    address_street = models.CharField(max_length=255, null=True, blank=True, verbose_name="Sokak/Cadde")
    address_city = models.CharField(max_length=100, null=True, blank=True, verbose_name="İl")
    address_state = models.CharField(max_length=100, null=True, blank=True, verbose_name="İlçe")
    address_zipcode = models.CharField(max_length=10, null=True, blank=True, verbose_name="Posta Kodu")

    # 3. İLİŞKİ VE ZAMAN
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Doğum Tarihi")
    
    agent = models.ForeignKey(
        'policy_management.CustomUser', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='customers',
        verbose_name="Sorumlu Acente"
    )
    
    # Oluşturma ve Güncelleme Tarihi (Yeni kayıtlar için otomatik dolacak)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Son Güncelleme")


    class Meta:
        verbose_name = "Müşteri"
        verbose_name_plural = "Müşteriler"

    def __str__(self):
        # Müşterinin TCKN'si doluysa onu, boşsa "TCKN Yok" yazısını göster.
        identifier = self.tckn if self.tckn else "TCKN Yok" 
        return f"{self.name} ({identifier})"

# -----------------------------------------------------
# POLİÇE MODELİ (Policy)
# -----------------------------------------------------

class Policy(models.Model):
    # Durum seçenekleri
    STATUS_CHOICES = (
        ('active', 'Aktif'),
        ('expired', 'Süresi Doldu'),
        ('cancelled', 'İptal Edildi'),
    )
    
    policy_id = models.AutoField(primary_key=True)
    policy_number = models.CharField(max_length=50, unique=True, verbose_name="Poliçe Numarası")
    policy_type = models.CharField(max_length=50, verbose_name="Sigorta Tipi (Kasko, Trafik vb.)")
    
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.CASCADE, 
        related_name='policies',
        verbose_name="Müşteri"
    )
    
    start_date = models.DateField(verbose_name="Başlangıç Tarihi")
    end_date = models.DateField(verbose_name="Bitiş Tarihi")
    premium_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prim Tutarı")

    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='active',
        verbose_name="Poliçe Durumu"
    ) 
    
    document = models.FileField(
        upload_to='policies/documents/', 
        blank=True, 
        null=True,
        verbose_name='Poliçe Dökümanı (PDF)'
    )
    
    issued_by_agent = models.ForeignKey(
        'policy_management.CustomUser', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='issued_policies',
        verbose_name="Düzenleyen Acente"
    )
    

    class Meta:
        verbose_name = "Poliçe"
        verbose_name_plural = "Poliçeler"
        
    def __str__(self):
        return f"Poliçe No: {self.policy_number} ({self.customer.name})"


# -----------------------------------------------------
# FİYAT TEKLİFİ MODELİ (Quote)
# -----------------------------------------------------
class Quote(models.Model):
    """Sigorta şirketlerinden alınan her bir teklifi tutar."""
    
    QUOTE_TYPES = [
        ('Kasko', 'Kasko'),
        ('Trafik', 'Trafik Sigortası'),
        ('DASK', 'DASK/Konut'),
    ]

    company_name = models.CharField(max_length=100, verbose_name="Sigorta Şirketi")
    policy_type = models.CharField(max_length=50, choices=QUOTE_TYPES, verbose_name="Sigorta Tipi") 
    
    premium_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Prim Tutarı")
    error_message = models.TextField(blank=True, null=True)
    
    issued_by_agent = models.ForeignKey(
        'policy_management.CustomUser', 
        on_delete=models.SET_NULL, 
        null=True, 
        verbose_name="Teklifi Alan Acente"
    )
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Müşteri"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    
    class Meta:
        verbose_name = "Fiyat Teklifi"
        verbose_name_plural = "Fiyat Teklifleri"

    def __str__(self):
        return f"{self.company_name} - {self.policy_type} ({self.premium_amount or 'Hata'})"