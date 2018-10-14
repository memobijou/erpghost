from django.conf.urls import url

from product.single_product import SingleProductListView, SingleProductCreateView
from product.views import ProductListView, ProductListAPIView, IncomeListView, ProductImportView, ProductUpdateView, \
    ProductDetailView, ProductImageImportView, ProductUpdateIcecatView, ProductCreateView, ProductDeleteView, \
    ProductSingleUpdateView

urlpatterns = [
    url(r'^$', ProductListView.as_view(), name="list"),
    url(r'^single/$', SingleProductListView.as_view(), name="single_list"),
    url(r'^api/$', ProductListAPIView.as_view(), name="apilist"),
    url(r'^api/income/$', IncomeListView.as_view(), name="income"),
    url(r'^import/$', ProductImportView.as_view(), name="import"),
    url(r'^import_images/$', ProductImageImportView.as_view(), name="import_images"),
    url(r'^create/$', ProductCreateView.as_view(), name="create"),
    url(r'^create/single/$', SingleProductCreateView.as_view(), name="create_single"),
    url(r'^(?P<pk>\d+)/edit/$', ProductUpdateView.as_view(), name="edit"),
    url(r'^(?P<pk>\d+)/single/edit/$', ProductSingleUpdateView.as_view(), name="edit_single"),
    url(r'^(?P<pk>\d+)/edit/icecat/$', ProductUpdateIcecatView.as_view(), name="edit_icecat"),
    url(r'^(?P<pk>\d+)/$', ProductDetailView.as_view(), name="detail"),
    url(r'^delete/$', ProductDeleteView.as_view(), name="delete"),
]
