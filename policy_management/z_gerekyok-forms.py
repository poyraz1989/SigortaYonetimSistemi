# policy_management/forms.py

from django import forms
from .models import Policy, Customer, Quote

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'name', 
            'tckn', 
            'phone', 
            'email',
            'address_street',
            'address_city',
            'address_state',
            'address_zipcode',
            # YENİ ALAN: Doğum Tarihi'ni buraya ekleyin
            'date_of_birth', 
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ad Soyad'}),
            'tckn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'TC Kimlik Numarası (11 Hane)'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telefon Numarası'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'E-posta Adresi'}),
            
            # YENİ WIDGET: Doğum Tarihi için DateInput kullanmak önemlidir.
            # Tarayıcıda takvim seçici açmasını sağlar.
            'date_of_birth': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d' # <-- KRİTİK EKLEME: Tarih formatını standartlaştırıyoruz
            ),
            
            'address_street': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sokak/Cadde'}),
            'address_city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'İl'}),
            'address_state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'İlçe'}),
            'address_zipcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Posta Kodu'}),
        }
        
        labels = {
            'name': 'Ad Soyad',
            'tckn': 'TCKN',
            # YENİ LABEL
            'date_of_birth': 'Doğum Tarihi',
            'phone': 'Telefon',
            'email': 'E-posta',
            'address_street': 'Adres',
            'address_city': 'İl',
            'address_state': 'İlçe',
            'address_zipcode': 'Posta Kodu',
        }

class PolicyForm(forms.ModelForm):
    class Meta:
        model = Policy
        fields = [
            'customer', 
            'policy_number', 
            'policy_type', 
            'start_date', 
            'end_date', 
            'premium_amount', 
            # 'status', # <-- BU SATIRI ŞİMDİLİK YORUM SATIRI YAPIN VEYA SİLİN
            'document'
        ]
        
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }



class QuoteRequestForm(forms.Form):
    """API'lerden fiyat almak için kullanılan basit form."""
    
    # 🚨 KRİTİK DÜZELTME: Form alanları init metodundan ÖNCE gelmelidir. 🚨
    
    # 1. Müşteri Seçimi Alanı
    customer = forms.ModelChoiceField(
        # Başlangıçta boş queryset tanımla, init'te acenteye göre doldurulacak
        queryset=Customer.objects.none(), 
        label="Müşteri Seçin",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # 2. Sigorta Tipi Alanı
    policy_type = forms.ChoiceField(
        choices=Quote.QUOTE_TYPES,
        label="Sigorta Tipi",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # __init__ metodu artık alanlardan sonra geliyor
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 🚨 KRİTİK KONTROL: user nesnesinin kullanılması 🚨
        if user and user.is_authenticated:
            # Yalnızca bu acenteye ait müşterileri göster
            self.fields['customer'].queryset = Customer.objects.filter(agent=user)
        else:
            self.fields['customer'].queryset = Customer.objects.none()