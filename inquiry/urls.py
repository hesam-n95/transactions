from django.urls import path
from .views import TransactionInquiryView, CachedTransactionInquiryView

urlpatterns = [
    path('api/transaction/v1', TransactionInquiryView.as_view(), name='transaction-inquiry'),
    path('api/transaction/v1/cached', CachedTransactionInquiryView.as_view(), name='transaction-cached'),
]
