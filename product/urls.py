from django.conf.urls import url
from product.views import ProductListView, ProductListAPIView, IncomeListView, ProductImportView

urlpatterns = [
    url(r'^$', ProductListView.as_view(), name="list"),
    url(r'^api/$', ProductListAPIView.as_view(), name="apilist"),
    url(r'^api/income/$', IncomeListView.as_view(), name="income"),
    url(r'^import/$', ProductImportView.as_view(), name="import"),
]
