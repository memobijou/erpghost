from django.conf.urls import url

from stock.minus_stock import MinusStockListView
from stock.rebook import RefillOverview, RebookOnPositionOverview, BookStockOnPosition
from stock.rebook_order import AssignRebookOrderView, RebookOrderListView, RebookOrderView, \
    RebookOrderRebookOnPositionOverview, RebookOrderBookStockOnPosition
from stock.rebook_order_administration import RebookOrderAdminOverview, RebookOrderAdminUpdateView
from stock.single_stock import SingleStockListView, SingleStockDeleteView, SingleBookProductToPositionView, \
    SinglePositionListView, SingleGeneratePositionsView, SinglePositionDeleteView, SingleStockUpdateView, \
    SingleStockDeleteQuerySetView
from .views import StockListView, StockDocumentDetailView, StockUpdateView, StockDetailView, \
    StockImportView, PositionListView, BookProductToPositionView, StockDeleteView, GeneratePositionsView, \
    PositionDeleteView, PositionListAPIView, StockCorrectView, StockDeleteQuerySetView, RedirectStocksActionView

urlpatterns = [
    url(r'^$', StockListView.as_view(), name="list"),
    url(r'^single/$', SingleStockListView.as_view(), name="single_list"),
    url(r'^delete/(?P<pk>\d+)/$', StockDeleteView.as_view(), name="delete"),
    url(r'^single_delete/(?P<pk>\d+)/$', SingleStockDeleteView.as_view(), name="single_delete"),
    url(r'^delete_items/$', StockDeleteQuerySetView.as_view(), name="delete_items"),
    url(r'^delete_items/single/$', SingleStockDeleteQuerySetView.as_view(), name="single_delete_items"),
    url(r'^document/(?P<pk>\d+)/$', StockDocumentDetailView.as_view(), name="documentdetail"),
    url(r'^(?P<pk>\d+)/edit/$', StockUpdateView.as_view(), name="edit"),
    url(r'^(?P<pk>\d+)/edit/single/$', SingleStockUpdateView.as_view(), name="single_edit"),
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
    url(r'^rebook/$', RefillOverview.as_view(), name="rebook_overview"),
    url(r'^rebook_on_position/(?P<stock_pk>\d+)/$', RebookOnPositionOverview.as_view(), name="rebook_on_position"),
    url(r'^book_on_position/(?P<stock_pk>\d+)/$', BookStockOnPosition.as_view(),
        name="book_stock_on_position"),
    url(r"^redirect_stock_action/$", RedirectStocksActionView.as_view(), name="redirect_to_action"),
    url(r"^assign_rebook_order/$", AssignRebookOrderView.as_view(), name="rebook_order"),
    url(r"^rebook_order/$", RebookOrderListView.as_view(), name="rebook_order_list"),
    url(r"^rebook_order/(?P<pk>\d+)/$", RebookOrderView.as_view(), name="rebook_order"),
    url(r'^rebook_order/(?P<pk>\d+)/rebook_on_position/(?P<item_pk>\d+)/$',
        RebookOrderRebookOnPositionOverview.as_view(), name="rebook_order_rebook_on_position"),
    url(r'^rebook_order/(?P<pk>\d+)/book_on_position/(?P<item_pk>\d+)/$', RebookOrderBookStockOnPosition.as_view(),
        name="rebook_order_book_stock_on_position"),
    url(r"^rebook_order/administration/$", RebookOrderAdminOverview.as_view(), name="admin_rebook_order_list"),
    url(r"^rebook_order/administration/(?P<pk>\d+)/edit/$", RebookOrderAdminUpdateView.as_view(),
        name="admin_rebook_order_edit"),
]


