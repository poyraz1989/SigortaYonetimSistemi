# policy_management/admin.py

from django.contrib import admin
from .models import Customer, Policy

# ------------------------------------
# 1. Customer ModelAdmin Sınıfı
# ------------------------------------
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    # Liste görünümünde gösterilecek sütunlar
    list_display = ('name', 'tckn_vkn', 'customer_type', 'email', 'agent')
    
    # Filtreleme seçenekleri
    list_filter = ('customer_type', 'agent')
    
    # Arama çubuğunda arama yapılacak alanlar
    search_fields = ('name', 'tckn_vkn', 'email', 'phone')
    
    # Detay sayfasında alanların gruplandırılması
    fieldsets = (
        (None, {
            'fields': ('name', 'tckn_vkn', 'customer_type', 'agent'),
        }),
        ('İletişim Bilgileri', {
            'fields': ('phone', 'email', 'address'),
            'classes': ('collapse',), # İsteğe bağlı: Bu bölümü varsayılan olarak kapalı getirir
        }),
    )

# ------------------------------------
# 2. Policy ModelAdmin Sınıfı
# ------------------------------------
@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    # status alanını liste ve filtrelerden geçici olarak çıkarın
    list_display = (
        'policy_number', 'customer', 'policy_type', 
        'start_date', 'end_date', 'premium_amount', 
        # 'status', # <-- Bu satırı SİLİN veya yorum yapın
        'document' 
    )
    list_filter = (
        'policy_type', 
        # 'status', # <-- Bu satırı SİLİN veya yorum yapın
        'start_date', 
    )
    search_fields = ('policy_number', 'customer__name', 'policy_type')
    
    # list_editable kısmından da status'ü çıkarın:
    list_editable = (
        'premium_amount', 
        # 'status', # <-- Bu satırı SİLİN veya yorum yapın
    )
    
    # customer_name alanını list_display'de kullanmak için özel metot
    def customer_name(self, obj):
        return obj.customer.name
    customer_name.short_description = 'Müşteri Adı' # Sütun başlığını ayarla