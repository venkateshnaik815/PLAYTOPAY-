from django.urls import path
from .views import PayoutCreateView, DashboardDataView, MerchantListView, PayoutExportView

urlpatterns = [
    path('payouts', PayoutCreateView.as_view(), name='payout-create'),
    path('dashboard', DashboardDataView.as_view(), name='dashboard-data'),
    path('merchants', MerchantListView.as_view(), name='merchant-list'),
    path('export', PayoutExportView.as_view(), name='payout-export'),
]
