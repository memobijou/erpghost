from django.conf.urls import url

from stock.minus_stock import MinusStockListView
from .views import StockListView, StockDocumentDetailView, StockUpdateView, StockDetailView, \
    StockImportView, StockCopyView, PositionListView, BookProductToPositionView, StockDeleteView, GeneratePositionsView, \
    PositionDeleteView, PositionListAPIView, StockCorrectView

urlpatterns = [
    url(r'^$', StockListView.as_view(), name="list"),
    url(r'^delete/(?P<pk>\d+)/$', StockDeleteView.as_view(), name="delete"),
    url(r'^document/(?P<pk>\d+)/$', StockDocumentDetailView.as_view(), name="documentdetail"),
    url(r'^(?P<pk>\d+)/edit/$', StockUpdateView.as_view(), name="edit"),
    url(r'^(?P<pk>\d+)/correct/$', StockCorrectView.as_view(), name="correct"),
    url(r'^(?P<pk>\d+)/$', StockDetailView.as_view(), name="detail"),
    url(r'^(?P<pk>\d+)/copy/$', StockCopyView.as_view(), name="copy"),
    url(r'^import/$', StockImportView.as_view(), name="import"),
    url(r'^position/$', PositionListView.as_view(), name="position_list"),
    url(r'^position/(?P<pk>\d+)/book/$', BookProductToPositionView.as_view(), name="position_book"),
    url(r'^position/generate_positions/$', GeneratePositionsView.as_view(), name="generate_positions"),
    url(r'^delete/$', PositionDeleteView.as_view(), name="position_delete"),
    url(r'^position/api/$', PositionListAPIView.as_view(), name="position_api"),
    url(r'^minus_stock/$', MinusStockListView.as_view(), name="minus_list"),

]
