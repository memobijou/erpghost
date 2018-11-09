from django.conf.urls import url

from online.billing import OnlineBillingView
from online.delivery_note import OnlineDeliveryNoteView
from online.ebay import EbayView
from online.pick import AcceptOnlinePickList, PickOrderView, PickerView, GoFromStationToPackingView, PackingView, \
    ProvidePackingView, LoginToStationView, LogoutFromStationView, PackingPickOrderOverview, ConfirmManualView, \
    FinishPackingView
from online.refill import AcceptRefillStockView, BookOutForOnlinePositions, RefillStockView, \
    BookInOnlineWarehouseList, ProductsForBookInView, BookProductInPosition, FinishRefillOrderView, OnlineRedirectView
from .views import OnlineListView, OnlineDetailView, ImportMissionView
from .dpd import DPDCreatePDFView, DPDGetLabelView
from .dhl import DHLCreatePdfView, DhlGetLabelView, DhlDeleteLabelView
from online.import_offers import ImportOffersView


urlpatterns = [
    url(r'^$', OnlineListView.as_view(), name="list"),
    url(r'^(?P<pk>\d+)/$', OnlineDetailView.as_view(), name="detail"),
    url(r'^(?P<pk>\d+)/dpd_label/(?P<business_account_pk>\d+)/$', DPDCreatePDFView.as_view(), name="dpd_pdf"),
    url(r'^(?P<pk>\d+)/dhl_label/(?P<business_account_pk>\d+)/$', DHLCreatePdfView.as_view(), name="dhl_pdf"),
    url(r'^(?P<pk>\d+)/dhl/get_label/(?P<shipment_number>\d+)/$', DhlGetLabelView.as_view(), name="dhl_get_label"),
    url(r'^(?P<pk>\d+)/dhl/delete_label/(?P<shipment_number>\d+)/$', DhlDeleteLabelView.as_view(),
        name="dhl_delete_label"),
    url(r'^(?P<pk>\d+)/dpd/get_label/$', DPDGetLabelView.as_view(), name="dpd_get_label"),
    url(r'^accept_picklist/$', AcceptOnlinePickList.as_view(), name="accept_picklist"),
    url(r'^picking/$', PickOrderView.as_view(), name="picking"),
    url(r'^pickorder/$', PickerView.as_view(), name="pickorder"),
    url(r'^packing_overview/$', PackingPickOrderOverview.as_view(), name="packing_overview"),
    url(r'^station/(?P<pk>\d+)/$', GoFromStationToPackingView.as_view(), name="from_station_to_packing"),
    url(r'^packing/(?P<pk>\d+)/$', PackingView.as_view(), name="packing"),
    url(r'^provide_packing/(?P<pk>\d+)/$', ProvidePackingView.as_view(), name="provide_packing"),
    url(r'^finish_packing/(?P<pk>\d+)/$', FinishPackingView.as_view(), name="finish_packing"),
    url(r'^(?P<pk>\d+)/delivery_note/(?P<delivery_note_pk>\d+)/$', OnlineDeliveryNoteView.as_view(),
        name="delivery_note"),
    url(r'^(?P<pk>\d+)/billing/(?P<billing_pk>\d+)/$', OnlineBillingView.as_view(),
        name="billing"),
    url(r'^login_station/$', LoginToStationView.as_view(), name="login_station"),
    url(r'^logout_from_station/(?P<pk>\d+)/$', LogoutFromStationView.as_view(), name="logout_from_station"),
    url(r'^ebay_test/$', EbayView.as_view(), name="ebay_test"),
    url(r'^accept_refill_order/$', AcceptRefillStockView.as_view(), name="accept_refill"),
    url(r'^refill_order/$', RefillStockView.as_view(), name="refill"),
    url(r'^stock/(?P<pk>\d+)/bookout/$', BookOutForOnlinePositions.as_view(), name="book_out"),
    url(r'^warehouse/product/(?P<pk>\d+)/state/(?P<state>[\w\-]+)/$', BookInOnlineWarehouseList.as_view(),
        name="warehouse"),
    url(r'^products_for_bookin/$', ProductsForBookInView.as_view(), name="products_for_bookin"),
    url(r'^book_product/(?P<product_pk>\d+)/state/(?P<state>[\w\-]+)/position/(?P<position_pk>\d+)/$',
        BookProductInPosition.as_view(), name="book_product_in_position"),
    url(r'^finish_refill_order/$', FinishRefillOrderView.as_view(), name="finish_refill_order"),
    url(r'^online_redirect/$', OnlineRedirectView.as_view(), name="online_redirect"),
    url(r'^import_mission/$', ImportMissionView.as_view(), name="import_mission"),
    url(r'^import_offers/$', ImportOffersView.as_view(), name="import_offers"),
    url(r'^confirm_manual/(?P<pk>\d+)/$', ConfirmManualView.as_view(), name="confirm_manual"),

]

