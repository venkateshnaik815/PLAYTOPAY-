from django.db import models
import csv
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Merchant, Payout, LedgerEntry
from .serializers import PayoutSerializer, LedgerEntrySerializer, MerchantSerializer
from .services import PayoutService, handle_idempotency
import uuid

class PayoutCreateView(APIView):
    def post(self, request):
        # In a real system, merchant would be identified by auth.
        # For this demo, we'll use a header or default to first merchant.
        merchant_id = request.headers.get('X-Merchant-Id')
        if not merchant_id:
            merchant = Merchant.objects.first()
        else:
            merchant = Merchant.objects.get(id=merchant_id)

        idempotency_key = request.headers.get('Idempotency-Key')
        
        def action():
            amount_paise = request.data.get('amount_paise')
            bank_account_id = request.data.get('bank_account_id')
            
            if not amount_paise or not bank_account_id:
                return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                payout = PayoutService.create_payout(
                    merchant=merchant,
                    amount_paise=int(amount_paise),
                    bank_account_id=bank_account_id,
                    idempotency_key_uuid=uuid.UUID(idempotency_key) if idempotency_key else None
                )
                
                # Trigger background task
                from .tasks import process_payout
                process_payout(payout.id)

                return Response(PayoutSerializer(payout).data, status=status.HTTP_201_CREATED)
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return handle_idempotency(merchant, idempotency_key, action)

class DashboardDataView(APIView):
    def get(self, request):
        merchant_id = request.query_params.get('merchant_id')
        if not merchant_id:
            merchant = Merchant.objects.first()
        else:
            merchant = Merchant.objects.get(id=merchant_id)

        if not merchant:
            return Response({"error": "Merchant not found"}, status=404)

        balance = PayoutService.get_merchant_balance(merchant)
        
        # Held balance is the sum of PENDING and PROCESSING payouts
        held_balance_data = Payout.objects.filter(
            merchant=merchant, 
            status__in=['PENDING', 'PROCESSING']
        ).aggregate(sum=models.Sum('amount_paise'))
        held_balance = held_balance_data['sum'] or 0

        payouts = Payout.objects.filter(merchant=merchant)[:20]
        ledger_entries = LedgerEntry.objects.filter(merchant=merchant)[:20]

        return Response({
            "merchant": MerchantSerializer(merchant).data,
            "balance_paise": balance,
            "held_balance_paise": held_balance,
            "recent_payouts": PayoutSerializer(payouts, many=True).data,
            "recent_ledger": LedgerEntrySerializer(ledger_entries, many=True).data
        })

class MerchantListView(APIView):
    def get(self, request):
        merchants = Merchant.objects.all()
        return Response(MerchantSerializer(merchants, many=True).data)

from openpyxl import Workbook
from openpyxl.styles import Font

class PayoutExportView(APIView):
    def get(self, request):
        merchant_id = request.query_params.get('merchant_id')
        if not merchant_id:
            merchant = Merchant.objects.first()
        else:
            merchant = Merchant.objects.get(id=merchant_id)

        if not merchant:
            return Response({"error": "Merchant not found"}, status=404)

        payouts = Payout.objects.filter(merchant=merchant).order_by('-created_at')

        # Create workbook
        wb = Workbook()
        
        # Payouts Sheet
        ws1 = wb.active
        ws1.title = "Payout History"
        ws1.append(['ID', 'Amount (Paise)', 'Amount (INR)', 'Status', 'Bank Account ID', 'Created At', 'Updated At'])
        for cell in ws1[1]:
            cell.font = Font(bold=True)
        
        for p in payouts:
            ws1.append([
                p.id,
                p.amount_paise,
                p.amount_paise / 100,
                p.status,
                p.bank_account_id,
                p.created_at.replace(tzinfo=None),
                p.updated_at.replace(tzinfo=None),
            ])

        # Ledger Sheet
        ws2 = wb.create_sheet(title="Audit Ledger")
        ledger_entries = LedgerEntry.objects.filter(merchant=merchant).order_by('-created_at')
        ws2.append(['ID', 'Type', 'Amount', 'Description', 'Payout ID', 'Timestamp'])
        for cell in ws2[1]:
            cell.font = Font(bold=True)
            
        for l in ledger_entries:
            ws2.append([
                l.id,
                l.entry_type,
                l.amount,
                l.description,
                l.payout.id if l.payout else "N/A",
                l.created_at.replace(tzinfo=None),
            ])

        # Prepare response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="payout_ledger_{merchant.name.lower().replace(" ", "_")}.xlsx"'
        
        wb.save(response)
        return response
