# policy_management/views.py

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

# Eş zamanlı API çağrıları için
from concurrent.futures import ThreadPoolExecutor

# Yerel Modeller
from .models import Customer, Policy, Quote

# Yerel Formlar
from .forms import CustomerForm, PolicyForm, QuoteRequestForm

# Yerel Kaynaklar (Export)
from .resources import CustomerResource, PolicyResource

# Yerel API Bağlayıcıları
from .api_connectors import allianz, doga, turkiye

from .utils import extract_policy_data_mock


# Hangi bağlayıcıların kullanılacağını tanımlayan bir sözlük (Dictionary) oluşturalım
# Bu, sistemi çok esnek yapar. Yeni şirket eklemek için sadece burayı güncellemeniz yeterli.
API_CONNECTORS = {
    'allianz': allianz.get_quote,
    'doga': doga.get_quote,
    'turkiye': turkiye.get_quote,
}


# Acentenin giriş yapmasını zorunlu kılan mixin'i oluşturalım:
class AgentAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    # Kullanıcının "is_superuser" olmaması durumunda veya 
    # özel bir 'role' kontrolü yaparak acente olduğunu teyit edebiliriz.
    # Şimdilik LoginRequiredMixin yeterli, Yönetici zaten admin paneli kullanacak.

    def test_func(self):
        user = self.request.user
        # Kullanıcı süper kullanıcı değilse VE rolü 'agent' ise erişime izin ver.
        # Superuser'lar tüm panellere erişebilmelidir.
        return user.is_superuser or user.role == 'agent'

    def get_login_url(self):
        # Giriş yapılmamışsa kullanıcıyı admin paneline yönlendir
        return '/admin/login/?next=' + self.request.path


# -----------------------------------------------------
# Acente Dashboard (Özet Sayfa)
# -----------------------------------------------------
class AgentDashboardView(AgentAccessMixin, TemplateView):
    template_name = 'agent/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Sadece bu acenteye ait müşterileri ve poliçeleri say
        context['customer_count'] = Customer.objects.filter(agent=user).count()
        context['policy_count'] = Policy.objects.filter(issued_by_agent=user).count()
        
        # 7 gün içinde bitecek kendi poliçeleri (Basit versiyon)
        from datetime import date, timedelta
        seven_days_later = date.today() + timedelta(days=7)

        context['expiring_policies'] = Policy.objects.filter(
            issued_by_agent=user,
            end_date__lte=seven_days_later,
            end_date__gt=date.today(), # Bugünden sonra bitenler
            status='active'
        ).order_by('end_date')[:5] # En yakın 5 poliçeyi göster
        
        return context

# -----------------------------------------------------
# Acenteye Ait Müşteri Listesi
# -----------------------------------------------------
class AgentCustomerListView(AgentAccessMixin, ListView):
    model = Customer
    template_name = 'agent/customer_list.html'
    context_object_name = 'customers'
    
    def get_queryset(self):
        # KRİTİK FİLTRELEME: Yalnızca kullanıcının (acentenin) sorumlu olduğu müşterileri getir
        return Customer.objects.filter(agent=self.request.user).order_by('-customer_id')

# -----------------------------------------------------
# Acenteye Ait Poliçe Listesi
# -----------------------------------------------------
class AgentPolicyListView(AgentAccessMixin, ListView):
    model = Policy
    template_name = 'agent/policy_list.html'
    context_object_name = 'policies'
    
    def get_queryset(self):
        # KRİTİK FİLTRELEME: Yalnızca kullanıcının (acentenin) düzenlediği poliçeleri getir
        return Policy.objects.filter(issued_by_agent=self.request.user).order_by('-policy_id')
        
        
       

# -----------------------------------------------------
# Müşteri Oluşturma ve Düzenleme
# -----------------------------------------------------
class CustomerCreateView(AgentAccessMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'agent/customer_form.html'
    success_url = reverse_lazy('agent_customer_list') # Başarılı kayıttan sonra listeye dön
    
    # Form kaydedilmeden önce, sorumlu acenteyi otomatik olarak oturum açmış kullanıcı yap
    def form_valid(self, form):
        form.instance.agent = self.request.user
        return super().form_valid(form)
   
        
# -----------------------------------------------------
# Veri Dışa Aktarma Görünümleri (Export Views)
# -----------------------------------------------------

def export_customer_data(request):
    if not request.user.is_authenticated:
        return HttpResponse('Yetkisiz Erişim', status=403)
        
    # Yalnızca giriş yapmış acentenin müşterilerini al
    queryset = Customer.objects.filter(agent=request.user)
    
    dataset = CustomerResource().export(queryset)
    
    response = HttpResponse(dataset.csv, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="musteri_listesi.csv"'
    return response

def export_policy_data(request):
    if not request.user.is_authenticated:
        return HttpResponse('Yetkisiz Erişim', status=403)
        
    # Yalnızca giriş yapmış acentenin poliçelerini al
    queryset = Policy.objects.filter(issued_by_agent=request.user)
    
    dataset = PolicyResource().export(queryset)
    
    response = HttpResponse(dataset.csv, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="police_listesi.csv"'
    return response
    

# -----------------------------------------------------
# Özel Giriş Sayfası (Login View)
# -----------------------------------------------------
class CustomLoginView(SuccessMessageMixin, LoginView):
    template_name = 'auth/login.html' # Kendi şablonumuzu işaret ediyoruz
    redirect_authenticated_user = True # Giriş yapmış kullanıcıyı tekrar login sayfasına gönderme
    # LOGIN_REDIRECT_URL ayarını kullanacak
    success_message = "Başarıyla giriş yaptınız!"


# -----------------------------------------------------
# Poliçe Oluşturma (Fonksiyon Tabanlı)
# -----------------------------------------------------

@login_required
def agent_policy_create(request):
    extracted_data = {}
    
    if request.method == 'POST':
        # 1. ANALİZ BUTONU KONTROLÜ
        is_analysis_request = 'analyze_document' in request.POST
        
        # 2. Dosya yüklenmişse veriyi çek
        if request.FILES and 'document' in request.FILES:
            try:
                uploaded_file = request.FILES['document']
                extracted_data = extract_policy_data_mock(uploaded_file)
            except Exception as e:
                messages.error(request, f"Döküman analizi sırasında hata oluştu: {e}")
        
        # 3. KAYDETME İŞLEMİ (Kaydet butonuna basıldıysa VE dosya yüklüyse)
        if not is_analysis_request: # Kaydet butonuna basıldıysa (Analyze değilse)
            form = PolicyForm(request.POST, request.FILES)
            
            if form.is_valid():
                # Normal kaydetme mantığı
                policy = form.save(commit=False)
                policy.issued_by_agent = request.user
                policy.save() 
                messages.success(request, "Yeni poliçe başarıyla oluşturuldu!")
                return redirect('agent_policy_list')
        
        # 4. ANALİZ VEYA KAYIT HATASI İÇİN FORMU OLUŞTURMA
        
        # POST verisini (veya analiz verisini) initial değer olarak kullan
        initial_data = request.POST.copy()
        initial_data.update(extracted_data) # Analizden gelen veriler, POST verilerinin üzerine yazılır.
        
        # Formu, gönderilen (ve analiz edilen) verilerle yeniden başlat
        form = PolicyForm(initial_data, request.FILES)

    else:
        # GET isteği
        form = PolicyForm()

    context = {'form': form, 'page_title': 'Yeni Poliçe Ekle'}
    return render(request, 'agent/policy_form.html', context)


# -----------------------------------------------------
# Poliçe Düzenleme (Fonksiyon Tabanlı)
# -----------------------------------------------------
@login_required
def agent_policy_edit(request, pk):
    policy = get_object_or_404(Policy.objects.filter(issued_by_agent=request.user), pk=pk)
    
    if request.method == 'POST':
        form = PolicyForm(request.POST, request.FILES, instance=policy) # KRİTİK: request.FILES ve instance eklenmeli
        if form.is_valid():
            form.save()
            messages.success(request, f"{policy.policy_number} numaralı poliçe başarıyla güncellendi.")
            return redirect('agent_policy_list')
    else:
        form = PolicyForm(instance=policy)

    context = {'form': form, 'page_title': 'Poliçe Düzenle'}
    return render(request, 'agent/policy_form.html', context)



# -----------------------------------------------------
# Poliçe Dökümanı Silme Fonksiyonu
# -----------------------------------------------------
@login_required
def agent_policy_document_delete(request, pk):
    # Sadece POST isteği kabul et
    if request.method == 'POST':
        # Poliçeyi bul ve acentenin poliçesi olduğundan emin ol
        policy = get_object_or_404(Policy.objects.filter(issued_by_agent=request.user), pk=pk)
        
        # Döküman alanı boş değilse işlemi yap
        if policy.document:
            # Dosyayı sunucudan sil (opsiyonel ama önerilir)
            policy.document.delete(save=False)
            
            # Veritabanındaki alanı boşalt
            policy.document = None
            policy.save()
            
            messages.success(request, f"{policy.policy_number} numaralı poliçenin dökümanı başarıyla silindi.")
        else:
            messages.warning(request, "Poliçede zaten yüklü bir döküman bulunmamaktadır.")
    
    # Poliçe listesine geri yönlendir
    return redirect('agent_policy_list')
    
    
    # -----------------------------------------------------
# Sahte Teklif Motoru Fonksiyonları
# -----------------------------------------------------

# Bu, her sigorta şirketinin teklifini simüle eden bir fonksiyon olsun
def get_mock_offers(customer_name, policy_type):
    # Gerçek uygulamada: Burada her şirket için API çağrısı yapılır.
    
    # Biz burada sahte veriler döndürüyoruz
    base_price = 1000 # Başlangıç fiyatı
    if 'TRAFIK' in policy_type.upper():
        base_price = 1200
        
    offers = [
        {'company': 'Ankara Sigorta', 'price': base_price, 'is_best': False},
        {'company': 'Türkiye Sigorta', 'price': base_price * 1.5, 'is_best': False},
        {'company': 'Allianz Sigorta', 'price': base_price * 2.5, 'is_best': False},
        {'company': 'Doğa Sigorta', 'price': base_price * 3.2, 'is_best': False},
    ]
    
    # Fiyatlara göre sırala ve en iyiyi işaretle
    offers.sort(key=lambda x: x['price'])
    if offers:
        offers[0]['is_best'] = True
        
    return offers


@login_required
def agent_pricing_view(request): # <-- ARANAN FONKSİYON BURADA
    # Bu projede sadece müşterileri çekebiliyoruz, müşteri seçimi yapılabilir
    customer_list = Customer.objects.filter(agent=request.user)
    
    offers = []
    
    # Varsayılan değerler
    selected_customer = None
    selected_policy_type = "Trafik Sigortası"
    
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        policy_type = request.POST.get('policy_type')
        
        # Müşteri ve poliçe tipine göre teklifleri çek (sahte)
        if customer_id and policy_type:
            selected_customer = get_object_or_404(customer_list, pk=customer_id)
            selected_policy_type = policy_type
            offers = get_mock_offers(selected_customer.name, policy_type)

    context = {
        'customers': customer_list,
        'offers': offers,
        'selected_customer': selected_customer,
        'selected_policy_type': selected_policy_type,
        'policy_types': ['Trafik Sigortası', 'Kasko Sigortası', 'DASK', 'Konut Sigortası'],
        'page_title': 'Sigorta Teklif Motoru',
    }
    return render(request, 'agent/pricing_engine.html', context)
    
    
    # ----------------------------------------------------------------------
# FİYAT TEKLİFİ LİSTELEME ve YENİ TEKLİF ALMA
# ----------------------------------------------------------------------

class QuoteListView(LoginRequiredMixin, ListView):
    model = Quote
    template_name = 'agent/quote_list.html'
    context_object_name = 'quotes'
    
    # Sadece kendi tekliflerini listelesin
    def get_queryset(self):
        # Filtreleme parametrelerini al
        filter_customer_id = self.request.GET.get('customer', None)
        filter_policy_type = self.request.GET.get('policy_type', None)

        # Temel sorgu: Acenteye ait teklifler
        queryset = Quote.objects.filter(issued_by_agent=self.request.user)
        
        # 1. Filtreleri uygula
        if filter_customer_id:
            queryset = queryset.filter(customer=filter_customer_id)
            
        if filter_policy_type:
            queryset = queryset.filter(policy_type=filter_policy_type)
        
        # 2. SIRALAMA MANTIĞI
        # Eğer bir filtreleme yapılmışsa (yani kullanıcı bir karşılaştırma yapmak istiyorsa), fiyata göre sırala.
        if filter_customer_id or filter_policy_type:
            # Filtre varsa: En ucuz teklifi en üste getir.
            queryset = queryset.order_by('premium_amount', '-created_at')
        else:
            # Filtre yoksa (Varsayılan): En yeni teklifi en üste getir.
            queryset = queryset.order_by('-created_at', 'premium_amount')
            
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Formu konteks içine ekle
        if 'form' not in context:
            context['form'] = QuoteRequestForm(user=self.request.user) # Eğer user bazlı seçimleriniz varsa
            
        return context

    def post(self, request, *args, **kwargs):
        form = QuoteRequestForm(request.POST, user=request.user) # user'ı POST'a da ekleyin
        
        if form.is_valid():
            customer = form.cleaned_data['customer']
            policy_type = form.cleaned_data['policy_type']
            
            # Müşteri verilerini API'lerin anlayacağı formata (dict) dönüştürelim
            customer_api_data = {
                'tckn': customer.tckn_vkn,
                'name': customer.name,
                'email': customer.email,
                # Not: Gerçek API'ler araç plakası, model yılı vb. isteyecektir.
                # Şimdilik simülasyon için bu yeterli.
            }

            # API çağrılarını eş zamanlı yapalım (Hız için)
            with ThreadPoolExecutor(max_workers=len(API_CONNECTORS)) as executor:
                futures = []
                
                # YENİ DÖNGÜ:
                for connector_func in API_CONNECTORS.values():
                    futures.append(
                        executor.submit(
                            connector_func, # Her şirketin kendi fonksiyonunu çağır
                            customer_api_data, 
                            policy_type
                        )
                    )
                
                new_quotes = []
                
                # Sonuçları topla ve kaydet
                with transaction.atomic():
                    for future in futures:
                        result = future.result()
                        
                        quote = Quote(
                            company_name=result['company'],
                            policy_type=policy_type,
                            issued_by_agent=request.user,
                            customer=customer # <-- KRİTİK EKLEME: Müşteriyi buraya kaydedin
                        )
                        
                        if result['status'] == 'success':
                            quote.premium_amount = result['price']
                            messages.success(request, f"{result['company']} teklifi başarıyla alındı: {result['price']} TL")
                        else:
                            quote.error_message = result.get('message', 'Bilinmeyen API hatası')
                            messages.warning(request, f"{result['company']} teklif vermedi: {result.get('message')}")
                        
                        quote.save()
                        new_quotes.append(quote)

            return redirect(reverse_lazy('agent_quote_list'))

        # Form geçerli değilse
        return self.get(request, form=form)
        
        
        
# MÜŞTERİ DÜZENLEME (UpdateView)
class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'agent/customer_form.html'
    
    def get_queryset(self):
        # Yalnızca acentenin kendi müşterisini düzenleyebilmesini sağla
        
        # ESKİ HATALI KOD:
        # return self.model.objects.filter(issued_by_agent=self.request.user)
        
        # YENİ DOĞRU KOD:
        return self.model.objects.filter(agent=self.request.user)

    def get_success_url(self):
        # Başarılı düzenlemeden sonra müşteri listesine dön
        messages.success(self.request, "Müşteri bilgileri başarıyla güncellendi.")
        return reverse_lazy('agent_customer_list')
        
    