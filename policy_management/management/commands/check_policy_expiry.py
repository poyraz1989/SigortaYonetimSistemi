# policy_management/management/commands/check_policy_expiry.py

import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from policy_management.models import Policy
# (Gerçek projede: E-posta gönderme fonksiyonunu buraya dahil edecektik)

class Command(BaseCommand):
    help = 'Poliçe bitiş tarihine 7 gün kalanları kontrol eder ve bildirim gönderir.'

    def handle(self, *args, **options):
        # Bugünün tarihini ve 7 gün sonrası tarihi hesaplayalım
        today = timezone.localdate()
        seven_days_later = today + datetime.timedelta(days=7)

        self.stdout.write(f"Bugün: {today}. 7 gün sonrası: {seven_days_later}")

        # Veritabanını sorgulama: Bitiş tarihi tam 7 gün sonrası olan aktif poliçeleri bul.
        # Neden sadece 7 gün sonrası? Çünkü daha önce uyarmışsak tekrar uyarmayalım.
        # Bu komut her gün çalıştığı için, sadece o gün 7 güne girenleri kontrol eder.
        expiring_policies = Policy.objects.filter(
            end_date=seven_days_later,
            status='active'
        )
        
        count = expiring_policies.count()
        self.stdout.write(self.style.WARNING(f"Toplam {count} adet poliçe 7 gün içinde bitiyor."))

        if count == 0:
            self.stdout.write(self.style.SUCCESS('Uyarı gerektiren poliçe bulunamadı.'))
            return

        for policy in expiring_policies:
            
            # --- Gerçek Bildirim İşlemi ---
            # Burada E-posta/SMS gönderme veya site içi bildirim kaydetme fonksiyonları çağrılmalı.
            
            customer_email = policy.customer.email
            agent_email = policy.issued_by_agent.email if policy.issued_by_agent else "Acente Yok"
            
            log_message = (
                f"Uyarılıyor: Poliçe No: {policy.policy_number}, "
                f"Müşteri: {policy.customer.name}, Bitiş: {policy.end_date}, "
                f"Müşteri E-posta: {customer_email}, Acente E-posta: {agent_email}"
            )
            self.stdout.write(log_message)
            
            # Örnek: E-posta Gönderme Fonksiyonu (Simülasyon)
            # send_notification_email(policy, customer_email, 'customer')
            # send_notification_email(policy, agent_email, 'agent')
            
            # Poliçenin durumu değiştirilmez, sadece uyarı gönderilir.
            
        self.stdout.write(self.style.SUCCESS('Poliçe bitiş kontrolü tamamlandı.'))