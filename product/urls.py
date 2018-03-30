from django.conf.urls import url
from product.views import ProductListView, ProductListAPIView, IncomeListView, ProductImportView, ProductUpdateView, \
    ProductDetailView

urlpatterns = [
    url(r'^$', ProductListView.as_view(), name="list"),
    url(r'^api/$', ProductListAPIView.as_view(), name="apilist"),
    url(r'^api/income/$', IncomeListView.as_view(), name="income"),
    url(r'^import/$', ProductImportView.as_view(), name="import"),
    url(r'^(?P<pk>\d+)/edit/$', ProductUpdateView.as_view(), name="edit"),
    url(r'^(?P<pk>\d+)/$', ProductDetailView.as_view(), name="detail"),
]
