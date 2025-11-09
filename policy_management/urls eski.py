# policy_management/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # YENİ GİRİŞ URL'si
    path('login/', views.CustomLoginView.as_view(), name='login'), # Bu URL'yi kullanacağız

    # Acente Paneli Giriş Sayfası (Kendi Özetini Görecek)
    path('agent/', views.AgentDashboardView.as_view(), name='agent_dashboard'),
    
    # Acenteye ait Müşteri Listesi
    path('agent/customers/', views.AgentCustomerListView.as_view(), name='agent_customer_list'),
    
    # Acenteye ait Poliçe Listesi
    path('agent/policies/', views.AgentPolicyListView.as_view(), name='agent_policy_list'),
    
    # Yeni Müşteri Ekleme (İleride ekleriz)
    # path('agent/customer/add/', views.CustomerCreateView.as_view(), name='agent_customer_add'),
    
    
    # Yeni Ekleme URL'leri
    path('agent/customer/add/', views.CustomerCreateView.as_view(), name='agent_customer_add'),
    path('agent/policy/add/', views.PolicyCreateView.as_view(), name='agent_policy_add'),
    
    # Yeni Dışa Aktarma URL'leri
    path('agent/export/customers/csv/', views.export_customer_data, name='agent_export_customers'),
    path('agent/export/policies/csv/', views.export_policy_data, name='agent_export_policies'),

    # Poliçe Oluşturma URL'si (Güncellendi: .as_view() kalktı)
    path('agent/policy/create/', views.agent_policy_create, name='agent_policy_create'),
    
    # Poliçe Düzenleme URL'si (Güncellendi: .as_view() kalktı)
    path('agent/policy/edit/<int:pk>/', views.agent_policy_edit, name='agent_policy_edit'),

    # Poliçe Dökümanı Silme URL'si
    path('agent/policy/document/delete/<int:pk>/', views.agent_policy_document_delete, name='agent_policy_document_delete'),

    # Teklif Motoru URL'si
    path('agent/pricing/', views.agent_pricing_view, name='agent_pricing_engine'),

]