# policy_management/views.py

from django.views.generic import ListView, TemplateView, DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django import forms # forms modülünü import ediyoruz

# Eş zamanlı API çağrıları için
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta 

# Yerel Modeller
from .models import Customer, Policy, Quote

# Yerel Kaynaklar (Export)
from .resources import CustomerResource, PolicyResource

# Yerel API Bağlayıcıları (Simülasyonlar)
from .api_connectors import allianz, doga, turkiye

from .utils import extract_policy_data_mock

# -----------------------------------------------------
# FORMLAR (forms.py içeriğini buraya taşıdık)
# -----------------------------------------------------

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'tckn', 'phone', 'email', 'address_street', 'address_city', 
                  'address_state', 'address_zipcode', 'date_of_birth']
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ad Soyad'}),
            'tckn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'TC Kimlik Numarası (11 Hane)'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telefon Numarası'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'E-posta Adresi'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'address_street': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sokak/Cadde'}),
            'address_city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'İl'}),
            'address_state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'İlçe'}),
            'address_zipcode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Posta Kodu'}),
        }
        
        labels = {
            'name': 'Ad Soyad', 'tckn': 'TCKN', 'date_of_birth': 'Doğum Tarihi', 'phone': 'Telefon',
            'email': 'E-posta', 'address_street': 'Adres', 'address_city': 'İl', 'address_state': 'İlçe',
            'address_zipcode': 'Posta Kodu',
        }

class PolicyForm(forms.ModelForm):
    class Meta:
        model = Policy
        fields = ['customer', 'policy_number', 'policy_type', 'start_date', 'end_date', 'premium_amount', 'document']
        
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


# Fiyat Teklifi Formu (500 hatasının ana kaynağıydı)
class QuoteRequestForm(forms.Form):
    """API'lerden fiyat almak için kullanılan basit form."""
    
    # 1. Müşteri Seçimi Alanı
    customer = forms.ModelChoiceField(
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
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            self.fields['customer'].queryset = Customer.objects.filter(agent=user)
        else:
            self.fields['customer'].queryset = Customer.objects.none()


# -----------------------------------------------------
# API Bağlantıları ve Mixinler
# -----------------------------------------------------
API_CONNECTORS = {
    'allianz': allianz.get_quote,
    'doga': doga.get_quote,
    'turkiye': turkiye.get_quote,
}


class AgentAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.role == 'agent'

    def get_login_url(self):
        return '/admin/login/?next=' + self.request.path


# -----------------------------------------------------
# Acente Dashboard (Özet Sayfa)
# -----------------------------------------------------
class AgentDashboardView(AgentAccessMixin, TemplateView):
    template_name = 'agent/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context['customer_count'] = Customer.objects.filter(agent=user).count()
        context['policy_count'] = Policy.objects.filter(issued_by_agent=user).count()
        
        seven_days_later = date.today() + timedelta(days=7)

        context['expiring_policies'] = Policy.objects.filter(
            issued_by_agent=user,
            end_date__lte=seven_days_later,
            end_date__gt=date.today(),
            status='active'
        ).order_by('end_date')[:5]
        
        return context

# -----------------------------------------------------
# Acenteye Ait Müşteri Listesi & Düzenleme
# -----------------------------------------------------
class AgentCustomerListView(AgentAccessMixin, ListView):
    model = Customer
    template_name = 'agent/customer_list.html'
    context_object_name = 'customers'
    
    def get_queryset(self):
        return Customer.objects.filter(agent=self.request.user).order_by('-customer_id')

class CustomerCreateView(AgentAccessMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'agent/customer_form.html'
    success_url = reverse_lazy('agent_customer_list') 
    
    def form_valid(self, form):
        form.instance.agent = self.request.user
        return super().form_valid(form)

class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'agent/customer_form.html'
    
    def get_queryset(self):
        return self.model.objects.filter(agent=self.request.user)

    def get_success_url(self):
        messages.success(self.request, "Müşteri bilgileri başarıyla güncellendi.")
        return reverse_lazy('agent_customer_list')


# -----------------------------------------------------
# Acenteye Ait Poliçe Listesi
# -----------------------------------------------------
class AgentPolicyListView(AgentAccessMixin, ListView):
    model = Policy
    template_name = 'agent/policy_list.html'
    context_object_name = 'policies'
    
    def get_queryset(self):
        return Policy.objects.filter(issued_by_agent=self.request.user).order_by('-policy_id')
        
# -----------------------------------------------------
# Poliçe Oluşturma ve Düzenleme (Fonksiyon Tabanlı)
# -----------------------------------------------------

@login_required
def agent_policy_create(request):
    # ... (Mevcut agent_policy_create fonksiyonu buraya gelecek) ...
    extracted_data = {}
    if request.method == 'POST':
        is_analysis_request = 'analyze_document' in request.POST
        if request.FILES and 'document' in request.FILES:
            try:
                uploaded_file = request.FILES['document']
                extracted_data = extract_policy_data_mock(uploaded_file)
            except Exception as e:
                messages.error(request, f"Döküman analizi sırasında hata oluştu: {e}")
        
        if not is_analysis_request: 
            form = PolicyForm(request.POST, request.FILES)
            if form.is_valid():
                policy = form.save(commit=False)
                policy.issued_by_agent = request.user
                policy.save() 
                messages.success(request, "Yeni poliçe başarıyla oluşturuldu!")
                return redirect('agent_policy_list')
        
        initial_data = request.POST.copy()
        initial_data.update(extracted_data) 
        form = PolicyForm(initial_data, request.FILES)

    else:
        form = PolicyForm()

    context = {'form': form, 'page_title': 'Yeni Poliçe Ekle'}
    return render(request, 'agent/policy_form.html', context)


@login_required
def agent_policy_edit(request, pk):
    # ... (Mevcut agent_policy_edit fonksiyonu buraya gelecek) ...
    policy = get_object_or_404(Policy.objects.filter(issued_by_agent=request.user), pk=pk)
    if request.method == 'POST':
        form = PolicyForm(request.POST, request.FILES, instance=policy)
        if form.is_valid():
            form.save()
            messages.success(request, f"{policy.policy_number} numaralı poliçe başarıyla güncellendi.")
            return redirect('agent_policy_list')
    else:
        form = PolicyForm(instance=policy)

    context = {'form': form, 'page_title': 'Poliçe Düzenle'}
    return render(request, 'agent/policy_form.html', context)


@login_required
def agent_policy_document_delete(request, pk):
    # ... (Mevcut agent_policy_document_delete fonksiyonu buraya gelecek) ...
    if request.method == 'POST':
        policy = get_object_or_404(Policy.objects.filter(issued_by_agent=request.user), pk=pk)
        if policy.document:
            policy.document.delete(save=False)
            policy.document = None
            policy.save()
            messages.success(request, f"{policy.policy_number} numaralı poliçenin dökümanı başarıyla silindi.")
        else:
            messages.warning(request, "Poliçede zaten yüklü bir döküman bulunmamaktadır.")
    return redirect('agent_policy_list')
    

# -----------------------------------------------------
# Sahte Teklif Motoru Fonksiyonları
# -----------------------------------------------------

def get_mock_offers(customer_name, policy_type):
    # ... (Mevcut get_mock_offers fonksiyonu buraya gelecek) ...
    base_price = 1000 
    if 'TRAFIK' in policy_type.upper():
        base_price = 1200
        
    offers = [
        {'company': 'Ankara Sigorta', 'price': base_price, 'is_best': False, 'status': 'success', 'message': None},
        {'company': 'Türkiye Sigorta', 'price': base_price * 1.5, 'is_best': False, 'status': 'success', 'message': None},
        {'company': 'Allianz Sigorta', 'price': base_price * 2.5, 'is_best': False, 'status': 'success', 'message': None},
        {'company': 'Doğa Sigorta', 'price': base_price * 3.2, 'is_best': False, 'status': 'success', 'message': None},
        {'company': 'ABC Sigorta', 'price': None, 'is_best': False, 'status': 'error', 'message': 'TCKN/Plaka eşleşmedi'},
    ]
    
    successful_offers = [o for o in offers if o['status'] == 'success']
    if successful_offers:
        successful_offers.sort(key=lambda x: x['price'])
        for offer in offers:
            if offer.get('price') == successful_offers[0]['price']:
                offer['is_best'] = True
                break
        
    return offers
    
# ----------------------------------------------------------------------
# FİYAT TEKLİFİ LİSTELEME ve YENİ TEKLİF ALMA
# ----------------------------------------------------------------------

class QuoteListView(LoginRequiredMixin, ListView):
    model = Quote
    template_name = 'agent/quote_list.html'
    context_object_name = 'quotes'
    
    def get_queryset(self):
        filter_customer_id = self.request.GET.get('customer', None)
        filter_policy_type = self.request.GET.get('policy_type', None)

        queryset = Quote.objects.filter(issued_by_agent=self.request.user)
        
        if filter_customer_id:
            try:
                queryset = queryset.filter(customer=int(filter_customer_id))
            except (TypeError, ValueError):
                pass
            
        if filter_policy_type:
            queryset = queryset.filter(policy_type=filter_policy_type)
        
        if filter_customer_id or filter_policy_type:
            queryset = queryset.order_by('premium_amount', '-created_at')
        else:
            queryset = queryset.order_by('-created_at', 'premium_amount')
            
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if 'form' not in context:
            context['form'] = QuoteRequestForm(user=self.request.user) 
            
        return context

    def post(self, request, *args, **kwargs):
        form = QuoteRequestForm(request.POST, user=request.user)
        
        if form.is_valid():
            customer = form.cleaned_data['customer']
            policy_type = form.cleaned_data['policy_type']
            
            offers_data = get_mock_offers(customer.name, policy_type)
            
            with transaction.atomic():
                for result in offers_data:
                    
                    quote = Quote(
                        company_name=result['company'],
                        policy_type=policy_type,
                        issued_by_agent=request.user,
                        customer=customer
                    )
                    
                    if result['status'] == 'success' and result.get('price') is not None:
                        quote.premium_amount = result['price']
                        messages.success(request, f"{result['company']} teklifi başarıyla alındı: {result['price']} TL")
                    else:
                        quote.premium_amount = 0 
                        quote.error_message = result.get('message', 'Bilinmeyen API hatası')
                        messages.warning(request, f"{result['company']} teklif vermedi: {result.get('message', 'Bilinmeyen Hata')}")
                    
                    quote.save()

            return redirect(reverse_lazy('agent_quote_list'))

        return self.get(request, form=form)
        
        
# ----------------------------------------------------------------------
# TEKLİF DETAY SAYFASI
# ----------------------------------------------------------------------
class QuoteDetailView(LoginRequiredMixin, DetailView):
    model = Quote
    template_name = 'agent/quote_detail.html'
    context_object_name = 'quote'
    
    def get_queryset(self):
        return Quote.objects.filter(issued_by_agent=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['policy_details'] = self.get_mock_details(self.object) 
        return context
    
    # Simüle edilmiş detay verisi döndüren metot (Sözdizimi hatası çözüldü)
    def get_mock_details(self, quote):
        policy_type = quote.policy_type 

        if 'Kasko' in policy_type:
            return [
                {'kapsam': 'Genişletilmiş Kasko', 'limit': 'Tavan', 'muafiyet': 'Yok'},
                {'kapsam': 'Ek Kloz: Deprem', 'limit': '50.000 TL', 'muafiyet': 'Var (10%)'},
                {'kapsam': 'Yurt Dışı Teminatı', 'limit': '20.000 TL', 'muafiyet': 'Yok'},
            ]
        elif 'Trafik' in policy_type:
            return [
                {'kapsam': 'Maddi Hasar', 'limit': '200.000 TL', 'muafiyet': 'Yok'},
                {'kapsam': 'Can Kaybı/Yaralanma', 'limit': '1.000.000 TL', 'muafiyet': 'Yok'},
            ]
        else:
             return [
                {'kapsam': 'Detaylar Bulunamadı', 'limit': '-', 'muafiyet': '-'},
             ]


# -----------------------------------------------------
# Veri Dışa Aktarma Görünümleri (Export Views)
# -----------------------------------------------------

def export_customer_data(request):
    if not request.user.is_authenticated:
        return HttpResponse('Yetkisiz Erişim', status=403)
        
    queryset = Customer.objects.filter(agent=request.user)
    dataset = CustomerResource().export(queryset)
    
    response = HttpResponse(dataset.csv, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="musteri_listesi.csv"'
    return response

def export_policy_data(request):
    if not request.user.is_authenticated:
        return HttpResponse('Yetkisiz Erişim', status=403)
        
    queryset = Policy.objects.filter(issued_by_agent=request.user)
    dataset = PolicyResource().export(queryset)
    
    response = HttpResponse(dataset.csv, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="police_listesi.csv"'
    return response

# -----------------------------------------------------
# Özel Giriş Sayfası (Login View)
# -----------------------------------------------------
class CustomLoginView(SuccessMessageMixin, LoginView):
    template_name = 'auth/login.html' 
    redirect_authenticated_user = True 
    success_message = "Başarıyla giriş yaptınız!"