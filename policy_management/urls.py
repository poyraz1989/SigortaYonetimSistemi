# policy_management/urls.py (Temizlenmiş ve Doğru Yapı)

from django.urls import path
from . import views

urlpatterns = [
    # GİRİŞ
    path('login/', views.CustomLoginView.as_view(), name='login'), 

    # TEMEL EKRANLAR
    path('agent/', views.AgentDashboardView.as_view(), name='agent_dashboard'),
    path('agent/customers/', views.AgentCustomerListView.as_view(), name='agent_customer_list'),
    path('agent/policies/', views.AgentPolicyListView.as_view(), name='agent_policy_list'),
    
    # MÜŞTERİ YÖNETİMİ (Burada CBV'ler durabilir, çünkü onları FBV'ye çevirmedik)
    path('agent/customer/add/', views.CustomerCreateView.as_view(), name='agent_customer_add'),
    #path('agent/customer/edit/<int:pk>/', views.CustomerUpdateView.as_view(), name='agent_customer_edit'), # Eksik olan düzenleme URL'si
    
    # POLİÇE YÖNETİMİ (FBV ile Dosya Yükleme Sorunu Giderildi)
    path('agent/policy/create/', views.agent_policy_create, name='agent_policy_add'),
    path('agent/policy/edit/<int:pk>/', views.agent_policy_edit, name='agent_policy_edit'),

    # EK İŞLEVLER
    path('agent/export/customers/csv/', views.export_customer_data, name='agent_export_customers'),
    path('agent/export/policies/csv/', views.export_policy_data, name='agent_export_policies'),
    path('agent/policy/document/delete/<int:pk>/', views.agent_policy_document_delete, name='agent_policy_document_delete'),
    #path('agent/pricing/', views.agent_pricing_view, name='agent_pricing_engine'),

    # FİYAT KARŞILAŞTIRMA MODÜLÜ
    path('agent/quotes/', views.QuoteListView.as_view(), name='agent_quote_list'), # Teklif listesi ve Fiyat alma formu

    # MÜŞTERİ YÖNETİMİ YOLLARI:
    path('customers/', views.AgentCustomerListView.as_view(), name='agent_customer_list'),
    path('customers/add/', views.CustomerCreateView.as_view(), name='agent_customer_add'),

    # YENİ YOLLAR: MÜŞTERİ DÜZENLEME
    # <int:pk> kısmı, hangi müşterinin düzenleneceğini URL'den yakalar.
    path('customers/edit/<int:pk>/', views.CustomerUpdateView.as_view(), name='edit_customer'),
 
    
    # ... (Teklif Yönetimi Yolları) ...
    path('quotes/', views.QuoteListView.as_view(), name='agent_quote_list'),
    
    # 🚨 YENİ EKLEME: Teklif Detay Sayfası
    # Teklifin ID'si (pk) ile sayfaya erişilecek
    path('quotes/<int:pk>/', views.QuoteDetailView.as_view(), name='agent_quote_detail'),
    
    # 🚨 YENİ POLİÇE YÖNETİM YOLLARI:
    path('policies/', views.AgentPolicyListView.as_view(), name='agent_policy_list'),
    
    # Poliçe Oluşturma (Formu açan view)
    path('policy/create/', views.agent_policy_create, name='agent_policy_create'),
    
    # Poliçe Düzenleme (PDF analizini kullanacak)
    path('policy/edit/<int:pk>/', views.agent_policy_edit, name='agent_policy_edit'),
    
    # Poliçe Dökümanı Silme
    path('policy/delete-document/<int:pk>/', views.agent_policy_document_delete, name='agent_policy_document_delete'),

]