from django.db import transaction, models
from django.db.models import Sum
from .models import Merchant, Payout, LedgerEntry, IdempotencyKey
from django.utils import timezone
from rest_framework.response import Response
import uuid

class PayoutService:
    @staticmethod
    def get_merchant_balance(merchant):
        """
        Calculate balance derived from ledger entries.
        Sum of credits minus absolute sum of debits.
        """
        result = LedgerEntry.objects.filter(merchant=merchant).aggregate(
            balance=models.Sum('amount')
        )
        return result['balance'] or 0

    @staticmethod
    def create_payout(merchant, amount_paise, bank_account_id, idempotency_key_uuid=None):
        """
        Create a payout atomically with a balance check and row lock.
        """
        if amount_paise <= 0:
            raise ValueError("Amount must be positive")

        with transaction.atomic():
            # Lock the merchant row to prevent concurrent payout requests for the same merchant
            merchant_locked = Merchant.objects.select_for_update().get(id=merchant.id)
            
            # Re-calculate balance inside the locked transaction
            current_balance = PayoutService.get_merchant_balance(merchant_locked)
            
            if current_balance < amount_paise:
                raise ValueError("Insufficient balance")

            # Create Payout record
            payout = Payout.objects.create(
                merchant=merchant_locked,
                amount_paise=amount_paise,
                bank_account_id=bank_account_id,
                idempotency_key=idempotency_key_uuid,
                status='PENDING'
            )

            # Create Ledger Entry (Debit)
            LedgerEntry.objects.create(
                merchant=merchant_locked,
                amount=-amount_paise,
                entry_type='DEBIT',
                payout=payout,
                description=f"Payout request: {payout.id}"
            )

            return payout

def handle_idempotency(merchant, key_uuid, action_func):
    """
    Generic idempotency handler.
    """
    if not key_uuid:
        return action_func()

    # Try to get or create the key
    key_obj, created = IdempotencyKey.objects.get_or_create(
        key=key_uuid,
        merchant=merchant
    )

    if not created:
        # Check if it's expired
        if key_obj.is_expired:
            key_obj.delete()
            key_obj, created = IdempotencyKey.objects.get_or_create(
                key=key_uuid,
                merchant=merchant
            )
        else:
            # If it's not created, it already exists. 
            # If response exists, return it.
            if key_obj.response_body is not None:
                return Response(key_obj.response_body, status=key_obj.response_code)
            
            # If response is None, it might be in-flight.
            # We can check locked_at.
            if key_obj.locked_at and timezone.now() - key_obj.locked_at < timezone.timedelta(minutes=5):
                return Response({"error": "Request in flight"}, status=409)

    # Mark as locked
    key_obj.locked_at = timezone.now()
    key_obj.save()

    try:
        response = action_func()
        
        # Save response for next time
        key_obj.response_code = response.status_code
        key_obj.response_body = response.data
        key_obj.locked_at = None
        key_obj.save()
        
        return response
    except Exception as e:
        # Clear lock on failure so it can be retried
        key_obj.locked_at = None
        key_obj.save()
        raise e
