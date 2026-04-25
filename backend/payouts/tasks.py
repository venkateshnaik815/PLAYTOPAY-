from huey.contrib.djhuey import db_task, db_periodic_task
from huey import crontab
from django.db import transaction
from .models import Payout, LedgerEntry
import random
import time

@db_task()
def process_payout(payout_id):
    try:
        with transaction.atomic():
            # Use select_for_update to lock the payout record
            payout = Payout.objects.select_for_update().get(id=payout_id)
            
            # State machine check
            if payout.status not in ['PENDING', 'PROCESSING']:
                return f"Payout {payout_id} in invalid state: {payout.status}"

            payout.status = 'PROCESSING'
            payout.save()

        # Simulate bank settlement delay
        time.sleep(3) 
        
        # Simulation probabilities: 70% success, 20% fail, 10% hang
        roll = random.random()
        
        with transaction.atomic():
            payout = Payout.objects.select_for_update().get(id=payout_id)
            
            if roll < 0.70:
                payout.status = 'COMPLETED'
                payout.save()
                return f"Payout {payout_id} succeeded"
            
            elif roll < 0.90:
                payout.status = 'FAILED'
                payout.save()
                
                # Refund logic: must be atomic with state change
                LedgerEntry.objects.create(
                    merchant=payout.merchant,
                    amount=payout.amount_paise,
                    entry_type='CREDIT',
                    payout=payout,
                    description=f"Refund for failed payout: {payout.id}"
                )
                return f"Payout {payout_id} failed and refunded"
            
            else:
                # Hang simulation - leave in PROCESSING
                return f"Payout {payout_id} processing (simulated hang)"

    except Exception as e:
        # Payout stays in PROCESSING/PENDING and will be retried by periodic task
        return f"Error processing payout {payout_id}: {str(e)}"

@db_periodic_task(crontab(minute='*/1'))
def retry_stuck_payouts():
    """
    Find payouts stuck in PROCESSING for more than 30s and retry them.
    """
    from django.utils import timezone
    from datetime import timedelta
    
    stuck_time = timezone.now() - timedelta(seconds=30)
    stuck_payouts = Payout.objects.filter(
        status='PROCESSING',
        updated_at__lt=stuck_time,
        retry_count__lt=3
    )
    
    for payout in stuck_payouts:
        payout.retry_count += 1
        payout.save()
        process_payout(payout.id)
