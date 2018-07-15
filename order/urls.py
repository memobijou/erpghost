from django.conf.urls import url

from order.pdfs import OrderPdfView
from .views import OrderListView, OrderListAPIView, OrderDetailView, OrderCreateView, OrderUpdateView, \
    ScanOrderUpdateView, search_positions, PositionProductOrderListAPIView, search_after_product_on_we,\
    OrderDeleteView, GoodsReceiptListView

urlpatterns = [
    url(r'^$', OrderListView.as_view(), name="list"),
    url(r'^goods_receipt/$', GoodsReceiptListView.as_view(), name="goods_receipt_list"),

    url(r'^api/$', OrderListAPIView.as_view(), name="apilist"),
    url(r'^(?P<pk>\d+)/$', OrderDetailView.as_view(), name="detail"),
    url(r'^create/$', OrderCreateView.as_view(), name="create"),
    url(r'^(?P<pk>\d+)/edit/$', OrderUpdateView.as_view(), name="update"),
    url(r'^(?P<pk>\d+)/scan/$', ScanOrderUpdateView.as_view(), name="scan"),
    url(r'^(?P<ordernummer>\d+)/suche/$', search_positions, name="suche"),
    url(r'^wareneingangSuche/$', search_after_product_on_we, name="suchewe"),
    url(r'^(?P<pk>\d+)/api/productorderposition/$', PositionProductOrderListAPIView.as_view(),
        name="apilistforProduct"),
    url(r'^delete/$', OrderDeleteView.as_view(), name="delete"),
    url(r'^order_pdf/(?P<pk>\d+)/$', OrderPdfView.as_view(), name="order_pdf"),
]
