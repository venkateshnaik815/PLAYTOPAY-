from django.test import TransactionTestCase
from rest_framework.test import APIClient
from payouts.models import Merchant, Payout, LedgerEntry, IdempotencyKey
from payouts.serializers import PayoutSerializer
from payouts.services import PayoutService
import threading
import uuid
import time
from django.db import connection

class PayoutConcurrencyTest(TransactionTestCase):
    def setUp(self):
        self.merchant = Merchant.objects.create(name="Test Merchant")
        LedgerEntry.objects.create(
            merchant=self.merchant,
            amount=10000, # 100 INR
            entry_type='CREDIT'
        )
        self.client = APIClient()

    def test_concurrent_payouts(self):
        """
        Test that two simultaneous 60 INR payout requests for a 100 INR balance
        results in exactly one success and one failure.
        """
        results = []
        
        def make_request():
            # We use a new connection for each thread because Django connections aren't thread-safe
            from django.db import connections
            connections.close_all()
            
            client = APIClient()
            response = client.post(
                '/api/v1/payouts',
                {'amount_paise': 6000, 'bank_account_id': 'BANK123'},
                HTTP_X_MERCHANT_ID=str(self.merchant.id),
                HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()) # Unique key for each
            )
            results.append(response)

        threads = [threading.Thread(target=make_request) for _ in range(2)]
        for t in threads: t.start()
        for t in threads: t.join()

        success_count = len([r for r in results if r.status_code == 201])
        error_count = len([r for r in results if r.status_code == 400])

        self.assertEqual(success_count, 1)
        self.assertEqual(error_count, 1)
        
        # Verify balance is correct (100 - 60 = 40)
        balance = PayoutService.get_merchant_balance(self.merchant)
        self.assertEqual(balance, 4000)

class IdempotencyTest(TransactionTestCase):
    def setUp(self):
        self.merchant = Merchant.objects.create(name="Idempotency Merchant")
        LedgerEntry.objects.create(
            merchant=self.merchant,
            amount=10000,
            entry_type='CREDIT'
        )
        self.client = APIClient()

    def test_idempotent_requests(self):
        """
        Test that multiple requests with the same key return the same response
        and only one payout is created.
        """
        key = str(uuid.uuid4())
        payload = {'amount_paise': 1000, 'bank_account_id': 'BANK123'}
        headers = {
            'HTTP_X_MERCHANT_ID': str(self.merchant.id),
            'HTTP_IDEMPOTENCY_KEY': key
        }

        # First request
        response1 = self.client.post('/api/v1/payouts', payload, **headers)
        self.assertEqual(response1.status_code, 201)
        payout_id = response1.data['id']

        # Second request with same key
        response2 = self.client.post('/api/v1/payouts', payload, **headers)
        self.assertEqual(response2.status_code, 201)
        self.assertEqual(response2.data['id'], payout_id)

        # Verify only one payout and one ledger debit exists
        self.assertEqual(Payout.objects.filter(merchant=self.merchant).count(), 1)
        self.assertEqual(LedgerEntry.objects.filter(merchant=self.merchant, entry_type='DEBIT').count(), 1)
