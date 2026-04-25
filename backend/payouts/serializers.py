from rest_framework import serializers
from .models import Merchant, Payout, LedgerEntry

class MerchantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Merchant
        fields = ['id', 'name', 'external_id', 'created_at']

class PayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        fields = ['id', 'amount_paise', 'status', 'bank_account_id', 'created_at', 'updated_at']

class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = ['id', 'amount', 'entry_type', 'description', 'created_at']
