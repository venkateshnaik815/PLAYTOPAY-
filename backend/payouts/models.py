from django.db import models
from django.utils import timezone
import uuid

class Merchant(models.Model):
    name = models.CharField(max_length=255)
    external_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Payout(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name='payouts')
    amount_paise = models.BigIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    bank_account_id = models.CharField(max_length=100)
    idempotency_key = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    retry_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

class LedgerEntry(models.Model):
    TYPE_CHOICES = [
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
    ]

    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name='ledger_entries')
    amount = models.BigIntegerField()  # Positive for credit, negative for debit
    entry_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    payout = models.ForeignKey(Payout, on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_entries')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class IdempotencyKey(models.Model):
    key = models.UUIDField()
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    response_code = models.IntegerField(null=True)
    response_body = models.JSONField(null=True)
    locked_at = models.DateTimeField(null=True, blank=True) # To handle in-flight
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('key', 'merchant')
        indexes = [
            models.Index(fields=['key', 'merchant']),
        ]

    @property
    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(hours=24)
