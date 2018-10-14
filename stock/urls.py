from django.conf.urls import url

from stock.minus_stock import MinusStockListView
from stock.single_stock import SingleStockListView, SingleStockDeleteView, SingleBookProductToPositionView, \
    SinglePositionListView, SingleGeneratePositionsView, SinglePositionDeleteView
from .views import StockListView, StockDocumentDetailView, StockUpdateView, StockDetailView, \
    StockImportView, PositionListView, BookProductToPositionView, StockDeleteView, GeneratePositionsView, \
    PositionDeleteView, PositionListAPIView, StockCorrectView

urlpatterns = [
    url(r'^$', StockListView.as_view(), name="list"),
    url(r'^single/$', SingleStockListView.as_view(), name="single_list"),
    url(r'^delete/(?P<pk>\d+)/$', StockDeleteView.as_view(), name="delete"),
    url(r'^single_delete/(?P<pk>\d+)/$', SingleStockDeleteView.as_view(), name="single_delete"),
    url(r'^document/(?P<pk>\d+)/$', StockDocumentDetailView.as_view(), name="documentdetail"),
    url(r'^(?P<pk>\d+)/edit/$', StockUpdateView.as_view(), name="edit"),
    url(r'^(?P<pk>\d+)/correct/$', StockCorrectView.as_view(), name="correct"),
    url(r'^(?P<pk>\d+)/$', StockDetailView.as_view(), name="detail"),
    url(r'^import/$', StockImportView.as_view(), name="import"),
    url(r'^position/$', PositionListView.as_view(), name="position_list"),
    url(r'^single_position/$', SinglePositionListView.as_view(), name="single_position_list"),
    url(r'^position/(?P<pk>\d+)/book/$', BookProductToPositionView.as_view(), name="position_book"),
    url(r'^position/(?P<pk>\d+)/book/single/$', SingleBookProductToPositionView.as_view(),
        name="single_position_book"),
    url(r'^position/generate_positions/$', GeneratePositionsView.as_view(), name="generate_positions"),
    url(r'^position/generate_positions/single/$', SingleGeneratePositionsView.as_view(),
        name="single_generate_positions"),
    url(r'^delete/$', PositionDeleteView.as_view(), name="position_delete"),
    url(r'^single_delete/$', SinglePositionDeleteView.as_view(), name="single_position_delete"),
    url(r'^position/api/$', PositionListAPIView.as_view(), name="position_api"),
    url(r'^minus_stock/$', MinusStockListView.as_view(), name="minus_list"),
]
