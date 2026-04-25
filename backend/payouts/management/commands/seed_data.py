from django.core.management.base import BaseCommand
from payouts.models import Merchant, LedgerEntry
from django.utils import timezone

class Command(BaseCommand):
    help = 'Seed merchants and initial credit history'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding data...")
        
        # Clear existing data (optional, but good for repeatable seeds)
        # Merchant.objects.all().delete()

        merchants = [
            {"name": "Venkatesh Agencies", "credits": [1000000, 500000]}, # 15,000 INR
            {"name": "TechFlow Solutions", "credits": [2500000, 750000]}, # 32,500 INR
            {"name": "Creative Studio", "credits": [500000, 200000, 300000]}, # 10,000 INR
        ]

        for m_data in merchants:
            merchant, created = Merchant.objects.get_or_create(name=m_data["name"])
            if created:
                self.stdout.write(f"Created merchant: {merchant.name}")
            
            for amount in m_data["credits"]:
                # Check if we already seeded this (simple check for demo)
                if not LedgerEntry.objects.filter(merchant=merchant, amount=amount, entry_type='CREDIT').exists():
                    LedgerEntry.objects.create(
                        merchant=merchant,
                        amount=amount,
                        entry_type='CREDIT',
                        description="Customer Payment (Simulated)"
                    )
                    self.stdout.write(f"  Added credit of {amount} paise to {merchant.name}")

        self.stdout.write(self.style.SUCCESS("Successfully seeded data"))
