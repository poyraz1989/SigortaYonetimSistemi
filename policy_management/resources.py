# policy_management/resources.py

from import_export import resources
from .models import Customer, Policy

class CustomerResource(resources.ModelResource):
    class Meta:
        model = Customer
        # Dışa aktarılacak alanlar. agent, ForeignKey olduğu için ID'si dışa aktarılır.
        fields = ('name', 'tckn_vkn', 'customer_type', 'phone', 'email', 'address', 'agent') 
        export_order = ('name', 'tckn_vkn', 'customer_type', 'email') # Sıralama

class PolicyResource(resources.ModelResource):
    class Meta:
        model = Policy
        fields = ('policy_number', 'policy_type', 'customer', 'start_date', 'end_date', 'premium_amount', 'status', 'issued_by_agent')
        # Bu durumda 'customer' ve 'issued_by_agent' ID'leri dışa aktarılacaktır.