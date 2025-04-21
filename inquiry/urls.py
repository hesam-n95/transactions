from django.urls import path
from .views import TransactionInquiryView, CachedTransactionInquiryView

urlpatterns = [
    path('api/transaction/v1/report', TransactionInquiryView.as_view(), name='transaction-inquiry'),
    path('api/transaction/v1/cached/report', CachedTransactionInquiryView.as_view(), name='transaction-cached'),
]
